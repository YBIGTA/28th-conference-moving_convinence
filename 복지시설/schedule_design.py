# -*- coding: utf-8 -*-
# 고립지수 × 생활인구 곱셈 모형 → 주간 방문 스케줄 설계

import pandas as pd
import glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.gridspec import GridSpec
from pathlib import Path
from pyproj import Transformer
import warnings
warnings.filterwarnings("ignore")

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

BASE = Path(r"E:\서울시 빅데이터 캠퍼스\Seoul")
all_csv = glob.glob(str(BASE / "eunpyeong" / "data" / "**" / "*.csv"), recursive=True)

def find_csv(unit, keyword, metric):
    for f in all_csv:
        if unit in f and keyword in f and metric in f:
            return f

COMPLEX_RISK = ["응암3동","불광2동","역촌동","갈현1동","갈현2동","구산동"]

# ── 오전/저녁 피크 (이전 분석 결과) ─────────────────────────────────────────
PEAK = {
    "불광2동": "오전",
    "갈현1동": "저녁", "갈현2동": "저녁", "구산동": "저녁",
    "역촌동":  "저녁", "응암3동": "저녁",
}

# ── 거점 좌표 ─────────────────────────────────────────────────────────────────
SPOTS = {
    "녹번종합사회복지관":     (37.602715, 126.931803),
    "신사종합사회복지관":     (37.598056, 126.912212),
    "은평종합사회복지관":     (37.586025, 126.888843),
    "시립은평노인종합복지관": (37.632018, 126.930342),
    "불광2동 주민센터":       (37.626383, 126.927266),
    "갈현1동 주민센터":       (37.623700, 126.916695),
    "갈현2동 주민센터":       (37.618586, 126.915839),
    "서울청년센터 은평":      (37.610719, 126.928472),
    "구산동도서관마을":       (37.609518, 126.913097),
    "역촌동 주민센터":        (37.604429, 126.915108),
    "신사종합사회복지관":     (37.598056, 126.912212),
    "응암3동 주민센터":       (37.592246, 126.915734),
    "신사2동 주민센터":       (37.590280, 126.908419),
    "대조동 주민센터":        (37.614189, 126.920825),
}

# 복합취약형 동별 대표 거점
DONG_SPOT = {
    "불광2동": ("불광2동 주민센터",   37.626383, 126.927266),
    "갈현1동": ("갈현1동 주민센터",   37.623700, 126.916695),
    "갈현2동": ("갈현2동 주민센터",   37.618586, 126.915839),
    "구산동":  ("구산동도서관마을",   37.609518, 126.913097),
    "역촌동":  ("역촌동 주민센터",    37.604429, 126.915108),
    "응암3동": ("응암3동 주민센터",   37.592246, 126.915734),
}

HUBS = {
    "녹번종합사회복지관":     (37.602715, 126.931803),
    "은평종합사회복지관":     (37.586025, 126.888843),
    "신사종합사회복지관":     (37.598056, 126.912212),
    "시립은평노인종합복지관": (37.632018, 126.930342),
}

tf = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
def dist_km(lat1, lon1, lat2, lon2):
    x1, y1 = tf.transform(lon1, lat1)
    x2, y2 = tf.transform(lon2, lat2)
    return ((x1-x2)**2 + (y1-y2)**2)**0.5 / 1000

# ── 최적 허브 선정 (6개 동 거점까지 평균 거리 최소) ─────────────────────────
hub_scores = {}
for hub, (hlat, hlon) in HUBS.items():
    dists = [dist_km(hlat, hlon, lat, lon) for _, lat, lon in DONG_SPOT.values()]
    hub_scores[hub] = np.mean(dists)

best_hub = min(hub_scores, key=hub_scores.get)
print("=== 허브 후보별 복합취약형 거점까지 평균 거리 ===")
for h, d in sorted(hub_scores.items(), key=lambda x: x[1]):
    marker = " ← 선정" if h == best_hub else ""
    print(f"  {h:18s}  {d:.2f} km{marker}")

# ── 고립지수 × 총생활인구 곱셈 점수 ──────────────────────────────────────────
iso_df  = pd.read_csv(str(BASE / "고립지수분석" / "data" / "중장년_고립유형_사분면.csv"))
iso_eunp = iso_df[(iso_df["자치구"]=="은평구") & (iso_df["행정동"].isin(COMPLEX_RISK))]
iso_eunp = iso_eunp.set_index("행정동")[["고립지수_종합"]]

oa_df    = pd.read_csv(find_csv("집계구", "전체", "절대인구"), dtype={"OA_CD": str})
risk_oa  = oa_df[oa_df["dong_nm"].isin(COMPLEX_RISK)]
oa_count  = risk_oa.groupby("dong_nm").size().rename("집계구수")
oa_midpop = risk_oa.groupby("dong_nm")["MID_POP"].mean().rename("MID_POP")
total_pop = (oa_midpop * oa_count).rename("총생활인구")

df = iso_eunp.join(total_pop).join(oa_count)
df["곱셈점수"] = df["고립지수_종합"] * df["총생활인구"]
df["순위"]     = df["곱셈점수"].rank(ascending=False, method="min").astype(int)
df["피크"]     = df.index.map(PEAK)

# 주 2회: 1위 동
df["주_방문"] = df["순위"].apply(lambda r: "주 2회" if r == 1 else "주 1회")

print()
print("=== 곱셈 점수 순위 (고립지수 × 총생활인구) ===")
print(f"  {'동명':8s}  {'고립지수':>8s}  {'총생활인구':>10s}  {'곱셈점수':>10s}  {'순위':>4s}  {'피크':>4s}  {'방문빈도'}")
print("  " + "-" * 65)
for dong in df.sort_values("순위").index:
    r = df.loc[dong]
    print(f"  {dong:8s}  {r['고립지수_종합']:>8.3f}  {r['총생활인구']:>10,.0f}"
          f"  {r['곱셈점수']:>10,.0f}  {r['순위']:>4d}위  {r['피크']:>4s}  {r['주_방문']}")

# ── 주간 스케줄 설계 ──────────────────────────────────────────────────────────
# 지리적 인접 쌍으로 묶기 (북쪽/북서/남쪽)
# 역촌동(1위) + 응암3동(고립지수 최고)은 목요일 2차 방문
SCHEDULE = [
    ("월", "불광2동", "오전(08-13시)", "갈현1동", "오후(14-18시)"),
    ("화", "역촌동",  "오전(08-13시)", "응암3동", "오후(14-18시)"),  # 역촌 1차
    ("수", "구산동",  "오전(08-13시)", "갈현2동", "오후(14-18시)"),
    ("목", "역촌동",  "오전(08-13시)", "응암3동", "오후(14-18시)"),  # 역촌+응암3 2차
]

hlat, hlon = HUBS[best_hub]
print()
print(f"=== 주간 운영 스케줄  |  허브: {best_hub} ===")
print(f"  {'요일':3s}  {'방문1(동)':8s}  {'시간대':12s}  {'방문2(동)':8s}  {'시간대':12s}  {'동선 거리'}")
print("  " + "-" * 72)
total_dist = 0
for day, d1, t1, d2, t2 in SCHEDULE:
    _, lat1, lon1 = DONG_SPOT[d1]
    _, lat2, lon2 = DONG_SPOT[d2]
    route = (dist_km(hlat, hlon, lat1, lon1)
           + dist_km(lat1, lon1, lat2, lon2)
           + dist_km(lat2, lon2, hlat, hlon))
    total_dist += route
    freq2 = " ★2차" if day == "목" else ""
    print(f"  {day}   {d1:8s}  {t1:12s}  {d2:8s}  {t2:12s}  {route:.1f} km{freq2}")
print(f"  {'':3s}  {'주간 총 이동거리':30s}  {total_dist:.1f} km")

# ════════════════════════════════════════════════════════════════════════════════
# 그래프
# ════════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(20, 12))
gs  = GridSpec(2, 2, figure=fig, hspace=0.38, wspace=0.32,
               left=0.06, right=0.97, top=0.92, bottom=0.07)
fig.patch.set_facecolor("#FFFFFF")

COLOR_AM = "#0EA5E9"   # 오전 피크
COLOR_PM = "#F97316"   # 저녁 피크
COLOR_2X = "#DC2626"   # 주 2회

# ── 패널 1: 곱셈점수 가로 막대 ───────────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor("#F9FAFB")

sorted_df = df.sort_values("곱셈점수", ascending=True)
bar_colors = []
for dong in sorted_df.index:
    if sorted_df.loc[dong, "주_방문"] == "주 2회":
        bar_colors.append(COLOR_2X)
    elif sorted_df.loc[dong, "피크"] == "오전":
        bar_colors.append(COLOR_AM)
    else:
        bar_colors.append(COLOR_PM)

bars = ax1.barh(sorted_df.index, sorted_df["곱셈점수"],
                color=bar_colors, edgecolor="white", linewidth=0.8,
                height=0.6, zorder=2)

for bar, (dong, row) in zip(bars, sorted_df.iterrows()):
    freq = "★주 2회" if row["주_방문"] == "주 2회" else "주 1회"
    ax1.text(row["곱셈점수"] + 120, bar.get_y() + bar.get_height()/2,
             f"{row['곱셈점수']:,.0f}  {freq}",
             va="center", fontsize=9, color="#111827",
             fontweight="bold" if row["주_방문"] == "주 2회" else "normal")

ax1.set_xlabel("고립지수 × 총생활인구", fontsize=10, color="#374151")
ax1.set_xlim(0, sorted_df["곱셈점수"].max() * 1.35)
ax1.set_title("방문 우선순위 점수", fontsize=12, fontweight="bold", color="#111827", pad=10)
ax1.grid(axis="x", color="#E5E7EB", linewidth=0.7, zorder=1)
ax1.spines[["top","right"]].set_visible(False)

leg = [mpatches.Patch(color=COLOR_2X, label="주 2회 (1위 역촌동·응암3동)"),
       mpatches.Patch(color=COLOR_PM, label="저녁 피크 동 (주 1회)"),
       mpatches.Patch(color=COLOR_AM, label="오전 피크 동 (주 1회)")]
ax1.legend(handles=leg, fontsize=8, loc="lower right",
           framealpha=0.9, edgecolor="#D1D5DB")

# ── 패널 2: 고립지수 vs 생활인구 산점도 ──────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor("#F9FAFB")

for dong in df.index:
    r = df.loc[dong]
    color = COLOR_2X if r["주_방문"] == "주 2회" else (COLOR_AM if r["피크"] == "오전" else COLOR_PM)
    size  = r["곱셈점수"] / df["곱셈점수"].max() * 500 + 80
    ax2.scatter(r["총생활인구"], r["고립지수_종합"],
                s=size, color=color, edgecolors="white", linewidths=1.2,
                zorder=3, alpha=0.88)
    ax2.annotate(dong, xy=(r["총생활인구"], r["고립지수_종합"]),
                 xytext=(0, 11), textcoords="offset points",
                 ha="center", fontsize=9.5, fontweight="bold",
                 color="#111827" if r["주_방문"] != "주 2회" else COLOR_2X,
                 path_effects=[pe.withStroke(linewidth=2, foreground="white")],
                 zorder=4)

ax2.axvline(df["총생활인구"].median(), color="#CBD5E1", linewidth=1.1, linestyle="--")
ax2.axhline(df["고립지수_종합"].median(), color="#CBD5E1", linewidth=1.1, linestyle="--")
ax2.set_xlabel("총 중장년 생활인구 (명)", fontsize=10, color="#374151")
ax2.set_ylabel("고립지수_종합", fontsize=10, color="#374151")
ax2.set_title("고립지수 × 생활인구 분포\n(마커 크기 = 곱셈점수)", fontsize=12,
              fontweight="bold", color="#111827", pad=10)
ax2.grid(True, color="#E5E7EB", linewidth=0.7, zorder=0)
ax2.spines[["top","right"]].set_visible(False)

# ── 패널 3: 주간 스케줄 표 ───────────────────────────────────────────────────
ax3 = fig.add_subplot(gs[1, :])
ax3.set_facecolor("#FFFFFF")
ax3.axis("off")

# 스케줄 표 데이터
col_labels = ["요일", "오전 방문", "시간대", "오후 방문", "시간대", "동선 거리", "누적 커버 동수"]
table_data = []
covered = set()
for day, d1, t1, d2, t2 in SCHEDULE:
    _, lat1, lon1 = DONG_SPOT[d1]
    _, lat2, lon2 = DONG_SPOT[d2]
    route = (dist_km(hlat, hlon, lat1, lon1)
           + dist_km(lat1, lon1, lat2, lon2)
           + dist_km(lat2, lon2, hlat, hlon))
    covered.update([d1, d2])
    spot1 = DONG_SPOT[d1][0]
    spot2 = DONG_SPOT[d2][0]
    freq2 = " ★2차" if day == "목" else ""
    table_data.append([day,
                        f"{d1}\n({spot1})", t1,
                        f"{d2}{freq2}\n({spot2})", t2,
                        f"{route:.1f} km",
                        f"{len(covered)}개 동"])

table = ax3.table(
    cellText=table_data,
    colLabels=col_labels,
    cellLoc="center",
    loc="center",
    bbox=[0, 0, 1, 1]
)
table.auto_set_font_size(False)
table.set_fontsize(9.5)

# 헤더 스타일
for j in range(len(col_labels)):
    table[(0, j)].set_facecolor("#1E3A5F")
    table[(0, j)].set_text_props(color="white", fontweight="bold")

# 행별 스타일
row_colors = ["#EFF6FF", "#FFF7ED", "#EFF6FF", "#FFF1F2"]
peak_cols  = [COLOR_AM, COLOR_PM, COLOR_PM, COLOR_PM]
for i, (rcolor, pcolor) in enumerate(zip(row_colors, peak_cols)):
    for j in range(len(col_labels)):
        cell = table[(i+1, j)]
        cell.set_facecolor(rcolor)
        if j in (1,):   # 오전 방문 열
            cell.set_facecolor("#E0F2FE")
        if j in (3,) and i == 3:   # 목 오후열 (응암3동 2차)
            cell.set_facecolor("#FEE2E2")

for (r, c), cell in table.get_celld().items():
    cell.set_edgecolor("#D1D5DB")

ax3.set_title(
    f"주간 운영 계획  |  허브: {best_hub}  |  복합취약형 6개 동 전수 커버",
    fontsize=12, fontweight="bold", color="#111827", pad=14, loc="left"
)

fig.suptitle(
    "이동형 마음편의점 주간 운영 스케줄  —  고립지수 × 생활인구 곱셈 모형 기반",
    fontsize=16, fontweight="bold", color="#111827", y=0.97
)

out = str(BASE / "복지시설" / "주간_운영스케줄.png")
plt.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"\n저장 완료: {out}")
