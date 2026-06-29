# -*- coding: utf-8 -*-
# 주간 동선 지도 — 생활인구 choropleth + 요일별 동선 오버레이

import geopandas as gpd
import pandas as pd
import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import contextily as ctx
from pyproj import Transformer
from pathlib import Path
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

COMPLEX_RISK = {"응암3동","불광2동","역촌동","갈현1동","갈현2동","구산동"}
WEEKDAYS = ["월요일","화요일","수요일","목요일","금요일"]

# ── 경계 로드 ─────────────────────────────────────────────────────────────────
dong_shp = gpd.read_file(str(BASE / "통계지역경계(2016년+기준)" / "행정구역.shp"), encoding="cp949")
eunp = dong_shp[dong_shp["SIGUNGU_NM"] == "은평구"].copy().reset_index(drop=True)
eunp = eunp.set_crs("EPSG:5179", allow_override=True).to_crs("EPSG:3857")
eunp["is_risk"] = eunp["ADM_NM"].isin(COMPLEX_RISK)

# ── 생활인구 (평일 평균) ──────────────────────────────────────────────────────
parts = []
for d in WEEKDAYS:
    path = find_csv("행정동", d, "절대인구")
    df_d = pd.read_csv(path, dtype={"H_DNG_CD": str})
    parts.append(df_d[["dong_nm", "MID_POP"]])
pop_avg = pd.concat(parts).groupby("dong_nm")["MID_POP"].mean().reset_index()
eunp = eunp.merge(pop_avg, left_on="ADM_NM", right_on="dong_nm", how="left")

# ── 좌표 변환 ─────────────────────────────────────────────────────────────────
tf = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
def to_merc(lat, lon):
    return tf.transform(lon, lat)

x_min, y_min = to_merc(37.568, 126.876)
x_max, y_max = to_merc(37.648, 126.963)
dx = x_max - x_min
dy = y_max - y_min

# ── 스케줄 정의 ───────────────────────────────────────────────────────────────
HUB_NAME  = "신사종합사회복지관"
HUB_COORD = (37.598056, 126.912212)

DONG_SPOT = {
    "불광2동": ("불광2동 주민센터",   37.626383, 126.927266),
    "갈현1동": ("갈현1동 주민센터",   37.623700, 126.916695),
    "갈현2동": ("갈현2동 주민센터",   37.618586, 126.915839),
    "구산동":  ("구산동도서관마을",   37.609518, 126.913097),
    "역촌동":  ("역촌동 주민센터",    37.604429, 126.915108),
    "응암3동": ("응암3동 주민센터",   37.592246, 126.915734),
}

# (요일, 오전동, 시간대, 오후동, 시간대, 화살표 곡률)
SCHEDULE = [
    ("월", "불광2동", "오전(08-13시)", "갈현1동", "오후(14-18시)",  0.08),
    ("화", "역촌동",  "오전(08-13시)", "응암3동", "오후(14-18시)",  0.08),   # 1차
    ("수", "구산동",  "오전(08-13시)", "갈현2동", "오후(14-18시)",  0.0),
    ("목", "역촌동",  "오전(08-13시)", "응암3동", "오후(14-18시)", -0.08),   # 2차
]

# 소프트 파스텔 팔레트
DAY_COLORS = {
    "월": "#34D399",   # emerald-400
    "화": "#818CF8",   # indigo-400
    "수": "#FBBF24",   # amber-400
    "목": "#F87171",   # red-400 (역촌·응암3 2차)
}

# 동 → 방문 요일 색 매핑 (역촌·응암3은 화=fill, 목=edge ring)
DONG_DAY_COLOR  = {}
DONG_DAY_COLOR2 = {}
for _day, _d1, _, _d2, *__ in SCHEDULE:
    if _d1 not in DONG_DAY_COLOR:
        DONG_DAY_COLOR[_d1] = DAY_COLORS[_day]
    if _d2 not in DONG_DAY_COLOR:
        DONG_DAY_COLOR[_d2] = DAY_COLORS[_day]
    elif _d2 not in DONG_DAY_COLOR2:
        DONG_DAY_COLOR2[_d2] = DAY_COLORS[_day]

# 레이블 지시선 오프셋 (점에서 텍스트 방향)
LABEL_OFFSET = {
    "불광2동": ( dx*0.17,  dy*0.012),
    "갈현1동": (-dx*0.17,  dy*0.015),
    "갈현2동": (-dx*0.17, -dy*0.008),
    "구산동":  (-dx*0.17, -dy*0.016),
    "역촌동":  ( dx*0.17,  dy*0.008),
    "응암3동": (-dx*0.17, -dy*0.010),
}

# ── 그리기 ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 18))
fig.patch.set_facecolor("#FFFFFF")
ax.set_facecolor("#F8FAFC")
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)

# 배경 지도 (노라벨 경량 타일, 낮은 투명도)
try:
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.PositronNoLabels, zoom=14, alpha=0.28)
except Exception:
    try:
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=14, alpha=0.22)
    except Exception:
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=14, alpha=0.12)

# 생활인구 choropleth
norm = Normalize(vmin=eunp["MID_POP"].min() * 0.85, vmax=eunp["MID_POP"].max())
eunp.plot(ax=ax, column="MID_POP", cmap="Blues", norm=norm,
          alpha=0.45, edgecolor="none",
          missing_kwds={"color": "#EEF2F7"}, zorder=2)

# 전체 경계 (매우 연한)
eunp.plot(ax=ax, facecolor="none", edgecolor="#C4C9D4", linewidth=0.5, zorder=3)

# 복합취약형 6개 동 경계 (진한 회색, 얇게)
eunp[eunp["is_risk"]].plot(
    ax=ax, facecolor="none", edgecolor="#6B7280", linewidth=1.2, zorder=4)

# 동명 레이블 (비복합취약형: 작게 회색)
for _, row in eunp.iterrows():
    if row["is_risk"]:
        continue
    c = row.geometry.centroid
    ax.text(c.x, c.y, row["ADM_NM"],
            fontsize=6.0, ha="center", va="center", color="#B0B8C8",
            path_effects=[pe.withStroke(linewidth=1.5, foreground="white")], zorder=5)

# ── 동선 화살표 ───────────────────────────────────────────────────────────────
hx, hy = to_merc(*HUB_COORD)

for day, d1, t1, d2, t2, rad in SCHEDULE:
    color = DAY_COLORS[day]
    _, lat1, lon1 = DONG_SPOT[d1]
    _, lat2, lon2 = DONG_SPOT[d2]
    x1, y1 = to_merc(lat1, lon1)
    x2, y2 = to_merc(lat2, lon2)

    # 직선 구간도 약간 아크로 처리
    r = rad if rad != 0.0 else 0.08

    fwd_kw = dict(arrowstyle="-|>", mutation_scale=13, lw=2.0,
                  color=color, alpha=0.82)

    if (lat1, lon1) != HUB_COORD:
        ax.annotate("", xy=(x1, y1), xytext=(hx, hy),
                    arrowprops=dict(**fwd_kw, connectionstyle=f"arc3,rad={r}"),
                    zorder=9)

    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(**fwd_kw, connectionstyle=f"arc3,rad={r}"),
                zorder=9)

# ── 거점 마커 & 지시선 레이블 ────────────────────────────────────────────────
# 허브
ax.scatter(hx, hy, s=480, marker="*", color="#1E3A5F", edgecolors="white",
           linewidths=1.5, zorder=14)
ax.annotate(f"★ {HUB_NAME}\n(이동형 마음편의점 허브)",
            xy=(hx, hy),
            xytext=(hx + dx*0.025, hy + dy*0.022),
            fontsize=13.0, fontweight="bold", color="#1E3A5F", ha="left",
            path_effects=[pe.withStroke(linewidth=3.0, foreground="white")],
            arrowprops=dict(arrowstyle="-", color="#6B7280", lw=0.8,
                           shrinkA=0, shrinkB=7),
            zorder=15)

# 각 동 거점
for dong, (spot, lat, lon) in DONG_SPOT.items():
    if (lat, lon) == HUB_COORD:
        continue

    x, y = to_merc(lat, lon)
    mc = DONG_DAY_COLOR[dong]
    ec = DONG_DAY_COLOR2.get(dong, "white")
    ew = 2.5 if dong in DONG_DAY_COLOR2 else 1.2

    # 글로우 + 마커
    ax.scatter(x, y, s=280, color=mc, alpha=0.18, linewidths=0, zorder=12)
    ax.scatter(x, y, s=175, color=mc, edgecolors=ec, linewidths=ew, zorder=13)

    # 방문 정보 텍스트
    visit_info = []
    for s_day, s_d1, s_t1, s_d2, s_t2, *_ in SCHEDULE:
        if s_d1 == dong:
            visit_info.append(f"{s_day}  {s_t1}")
        elif s_d2 == dong:
            visit_info.append(f"{s_day}  {s_t2}")
    time_str = "\n".join(visit_info)

    spot_short = (spot.replace(" 주민센터", "센터")
                      .replace("도서관마을", "도서관")
                      .replace("서울청년센터 은평", "청년센터"))
    label = f"{dong}  {spot_short}\n{time_str}"

    ox, oy = LABEL_OFFSET.get(dong, (0, dy * 0.010))
    ha = "left" if ox > 0 else ("right" if ox < 0 else "center")

    ax.annotate(label,
                xy=(x, y), xytext=(x + ox, y + oy),
                ha=ha, va="center",
                fontsize=13.0, fontweight="bold", color="#1F2937",
                path_effects=[pe.withStroke(linewidth=3.0, foreground="white")],
                arrowprops=dict(arrowstyle="-", color="#9CA3AF", lw=0.8,
                               shrinkA=0, shrinkB=6),
                zorder=14)

# ── 컬러바 (우측 상단, 세로형) ───────────────────────────────────────────────
sm = ScalarMappable(cmap=plt.get_cmap("Blues"), norm=norm)
sm.set_array([])
cbar_ax = fig.add_axes([0.88, 0.62, 0.020, 0.18])
cbar = fig.colorbar(sm, cax=cbar_ax, orientation="vertical")
cbar.set_label("중장년\n생활인구\n(명/동)", fontsize=7.5, color="#6B7280", labelpad=4)
cbar.ax.yaxis.set_label_position("left")
cbar.ax.tick_params(labelsize=7, colors="#6B7280")
cbar.outline.set_edgecolor("#D1D5DB")

# ── 범례 ──────────────────────────────────────────────────────────────────────
SCHEDULE_LABEL = {
    "월": "월  불광2동(오전) → 갈현1동(오후)",
    "화": "화  역촌동(오전) → 응암3동(오후)  [1차]",
    "수": "수  구산동(오전) → 갈현2동(오후)",
    "목": "목  역촌동(오전) → 응암3동(오후)  [2차]",
}
day_handles = [
    Line2D([0],[0], color=v, linewidth=2.5,
           marker="o", markersize=8,
           markerfacecolor=v, markeredgecolor="white", markeredgewidth=1.0,
           label=SCHEDULE_LABEL[k])
    for k, v in DAY_COLORS.items()
]
extra_handles = [
    Line2D([0],[0], marker="o", color="w",
           markerfacecolor=DAY_COLORS["화"],
           markeredgecolor=DAY_COLORS["목"], markeredgewidth=2.5,
           markersize=10, label="역촌동·응암3동  화·목 각 1회 (테두리=목)"),
    Line2D([0],[0], marker="*", color="w", markerfacecolor="#1E3A5F",
           markersize=15, label=f"허브  ({HUB_NAME})"),
    mpatches.Patch(facecolor="none", edgecolor="#6B7280", linewidth=1.2,
                   label="복합취약형 6개 동 경계"),
]

ax.legend(handles=day_handles + extra_handles,
          loc="lower right", bbox_to_anchor=(0.86, 0.04),
          fontsize=8.0, frameon=True, framealpha=0.96,
          edgecolor="#D1D5DB", facecolor="white",
          title="요일별 동선", title_fontsize=9.0)

ax.set_title(
    "이동형 마음편의점 주간 동선  |  은평구 복합취약형 6개 동  |  총 22.2 km/주",
    fontsize=13, fontweight="bold", color="#1F2937", pad=14)
ax.set_axis_off()

out = str(BASE / "복지시설" / "주간_동선_지도.png")
plt.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"저장 완료: {out}")
