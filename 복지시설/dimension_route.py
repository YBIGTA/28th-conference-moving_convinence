# -*- coding: utf-8 -*-
# 동선 2안 — 고립 차원 이원화
# 분류: 6개 동 내 z-score 비교 (z_사회 vs z_경제)
#   z_사회 ≥ z_경제 → 관계 회복 트랙 (사회적 연결 회복 중점)
#   z_사회 < z_경제 → 복지 연계 트랙 (경제·복지 서비스 연계 중점)

import geopandas as gpd
import pandas as pd
import numpy as np
import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from scipy.stats import zscore
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

TRACK_COLOR = {
    "관계 회복 트랙": "#6366F1",
    "복지 연계 트랙": "#F59E0B",
}

# ── 1. 이원화 분류 ────────────────────────────────────────────────────────────
df_q = pd.read_csv(str(BASE / "고립지수분석/data/중장년_고립유형_사분면.csv"),
                   encoding="utf-8")
sub = df_q[df_q["행정동"].isin(COMPLEX_RISK)].copy().reset_index(drop=True)

sub["사회적연결결핍"] = (sub["지수_사회활동"] + sub["지수_사회적_관계"]) / 2
sub["z_사회"] = zscore(sub["사회적연결결핍"])
sub["z_경제"] = zscore(sub["지수_경제적_불안정성"])
sub["z_diff"] = sub["z_사회"] - sub["z_경제"]
sub["트랙"] = sub["z_diff"].apply(
    lambda x: "관계 회복 트랙" if x >= 0 else "복지 연계 트랙")
sub = sub.sort_values("고립지수_종합", ascending=False).reset_index(drop=True)
dong_track = dict(zip(sub["행정동"], sub["트랙"]))

print("=" * 62)
print("  복합취약형 은평구 6개 동 고립 차원 이원화")
print("  기준: 6개 동 내 z-score (z_사회 vs z_경제)")
print("=" * 62)
for _, r in sub.iterrows():
    mk = "●" if r["트랙"] == "관계 회복 트랙" else "◆"
    print(f"  {mk} {r['행정동']:5s}  고립={r['고립지수_종합']:.3f}  "
          f"사회={r['사회적연결결핍']:.3f}  경제={r['지수_경제적_불안정성']:.3f}  "
          f"z_diff={r['z_diff']:+.2f}  → {r['트랙']}")
print()
for t, cnt in sub.groupby("트랙").size().items():
    print(f"  {t}: {cnt}개 동")

# ── 2. Figure 1: 산점도 + z_diff 막대차트 ────────────────────────────────────
mean_soc = sub["사회적연결결핍"].mean()
std_soc  = sub["사회적연결결핍"].std()
mean_eco = sub["지수_경제적_불안정성"].mean()
std_eco  = sub["지수_경제적_불안정성"].std()

# z=0 isoline: Y = (std_soc/std_eco)*(X - mean_eco) + mean_soc
x_pad = sub["지수_경제적_불안정성"].max() - sub["지수_경제적_불안정성"].min()
y_pad = sub["사회적연결결핍"].max() - sub["사회적연결결핍"].min()
x_iso = np.linspace(sub["지수_경제적_불안정성"].min() - x_pad * 0.3,
                    sub["지수_경제적_불안정성"].max() + x_pad * 0.3, 200)
y_iso = (std_soc / std_eco) * (x_iso - mean_eco) + mean_soc

fig1, (ax_s, ax_b) = plt.subplots(
    1, 2, figsize=(15, 7),
    gridspec_kw={"width_ratios": [1.1, 0.85]})
fig1.patch.set_facecolor("white")

# ── 왼쪽: 산점도 ──
ax_s.set_facecolor("#F8FAFC")
ax_s.grid(True, alpha=0.30, color="#CBD5E1", linewidth=0.7)

# 등선 + 영역 음영
y_top = sub["사회적연결결핍"].max() + y_pad * 0.3
y_bot = sub["사회적연결결핍"].min() - y_pad * 0.3
ax_s.fill_between(x_iso, y_iso, y_top,
                  color=TRACK_COLOR["관계 회복 트랙"], alpha=0.07)
ax_s.fill_between(x_iso, y_bot, y_iso,
                  color=TRACK_COLOR["복지 연계 트랙"], alpha=0.07)
ax_s.plot(x_iso, y_iso, color="#94A3B8", lw=1.5, ls="--", zorder=3)

# 트랙 레이블 (데이터 상하단 기준으로 상대 위치)
ax_s.text(x_iso[20], y_top - y_pad * 0.08, "관계 회복 트랙\n(z_사회 > z_경제)",
          fontsize=9.5, color=TRACK_COLOR["관계 회복 트랙"], ha="left",
          path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])
ax_s.text(x_iso[160], y_bot + y_pad * 0.08, "복지 연계 트랙\n(z_경제 ≥ z_사회)",
          fontsize=9.5, color=TRACK_COLOR["복지 연계 트랙"], ha="right",
          path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])

# 라벨 오프셋 (포인트 단위)
SCAT_OFF = {
    "응암3동": ( 0, 12), "불광2동": ( 10,  0),
    "역촌동":  (10,  0), "갈현2동": (  0,-12),
    "갈현1동": (10,  0), "구산동":  ( 10,-10),
}

for _, row in sub.iterrows():
    tc = TRACK_COLOR[row["트랙"]]
    x, y = row["지수_경제적_불안정성"], row["사회적연결결핍"]
    ax_s.scatter(x, y, s=540, color=tc, alpha=0.13, linewidths=0, zorder=4)
    ax_s.scatter(x, y, s=270, color=tc, edgecolors="white", linewidths=1.5,
                 zorder=5, alpha=0.92)
    ox, oy = SCAT_OFF.get(row["행정동"], (0, 12))
    ha = "left" if ox > 2 else ("right" if ox < -2 else "center")
    ax_s.annotate(row["행정동"], xy=(x, y),
                  xytext=(ox, oy), textcoords="offset points",
                  ha=ha, fontsize=9.5, fontweight="bold", color=tc,
                  path_effects=[pe.withStroke(linewidth=2.0, foreground="white")],
                  zorder=6)

ax_s.set_xlabel("지수_경제적_불안정성", fontsize=11, color="#374151", labelpad=8)
ax_s.set_ylabel(
    "사회적연결결핍\n[(지수_사회활동 + 지수_사회적_관계) / 2]",
    fontsize=11, color="#374151", labelpad=8)
ax_s.set_title("고립 차원 이원화\n6개 동 내 z-score 비교",
               fontsize=12, fontweight="bold", color="#1F2937", pad=10)

handles_s = [
    mpatches.Patch(facecolor=TRACK_COLOR["관계 회복 트랙"], alpha=0.85,
                   label="관계 회복 트랙 — z_사회 ≥ z_경제 (2개 동)"),
    mpatches.Patch(facecolor=TRACK_COLOR["복지 연계 트랙"], alpha=0.85,
                   label="복지 연계 트랙 — z_경제 > z_사회 (4개 동)"),
    Line2D([0],[0], color="#94A3B8", lw=1.5, ls="--",
           label="z_사회 = z_경제 경계선"),
]
ax_s.legend(handles=handles_s, loc="lower right", fontsize=9,
            frameon=True, framealpha=0.95, edgecolor="#D1D5DB")
for sp in ax_s.spines.values():
    sp.set_edgecolor("#E5E7EB")

# ── 오른쪽: z_diff 수평 막대 ──
sub_bar = sub.sort_values("z_diff")
dongs   = sub_bar["행정동"].tolist()
z_vals  = sub_bar["z_diff"].tolist()
colors  = [TRACK_COLOR[dong_track[d]] for d in dongs]

ax_b.set_facecolor("#F8FAFC")
bars = ax_b.barh(dongs, z_vals, color=colors, alpha=0.82, height=0.62, zorder=3)
ax_b.axvline(0, color="#374151", lw=1.2, zorder=4)
ax_b.axvspan(0, max(z_vals) + 0.25,
             color=TRACK_COLOR["관계 회복 트랙"], alpha=0.05, zorder=1)
ax_b.axvspan(min(z_vals) - 0.25, 0,
             color=TRACK_COLOR["복지 연계 트랙"], alpha=0.05, zorder=1)

for bar, val in zip(bars, z_vals):
    ha = "left" if val >= 0 else "right"
    offset = 0.04 if val >= 0 else -0.04
    ax_b.text(val + offset, bar.get_y() + bar.get_height() / 2,
              f"{val:+.2f}", ha=ha, va="center",
              fontsize=9, color="#374151", fontweight="bold")

ax_b.set_xlabel("z_사회 − z_경제  (양수 = 사회 우세, 음수 = 경제 우세)",
                fontsize=10, color="#374151", labelpad=8)
ax_b.set_title("차원 우세 지표\n(z_사회 − z_경제)",
               fontsize=12, fontweight="bold", color="#1F2937", pad=10)
ax_b.grid(True, axis="x", alpha=0.35, color="#CBD5E1", linewidth=0.7)
for sp in ax_b.spines.values():
    sp.set_edgecolor("#E5E7EB")

fig1.suptitle(
    "이동형 마음편의점 동선 2안  |  복합취약형 은평구 6개 동 고립 차원 이원화\n"
    "관계 회복 트랙 vs 복지 연계 트랙 분류 (방법론: 사분면 X·Y축 기반 z-score)",
    fontsize=13, fontweight="bold", color="#1F2937", y=1.02)
plt.tight_layout(pad=1.5)

out1 = str(BASE / "복지시설" / "dimension_scatter.png")
plt.savefig(out1, dpi=160, bbox_inches="tight", facecolor="white")
plt.close(fig1)
print(f"\n저장 완료: {out1}")

# ── 3. Figure 2: 동선 지도 (트랙 색상) ───────────────────────────────────────
dong_shp = gpd.read_file(
    str(BASE / "통계지역경계(2016년+기준)" / "행정구역.shp"), encoding="cp949")
eunp = dong_shp[dong_shp["SIGUNGU_NM"] == "은평구"].copy().reset_index(drop=True)
eunp = eunp.set_crs("EPSG:5179", allow_override=True).to_crs("EPSG:3857")
eunp["is_risk"] = eunp["ADM_NM"].isin(COMPLEX_RISK)

parts = []
for d in WEEKDAYS:
    path = find_csv("행정동", d, "절대인구")
    df_d = pd.read_csv(path, dtype={"H_DNG_CD": str})
    parts.append(df_d[["dong_nm", "MID_POP"]])
pop_avg = pd.concat(parts).groupby("dong_nm")["MID_POP"].mean().reset_index()
eunp = eunp.merge(pop_avg, left_on="ADM_NM", right_on="dong_nm", how="left")

tf = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
def to_merc(lat, lon):
    return tf.transform(lon, lat)

x_min, y_min = to_merc(37.568, 126.876)
x_max, y_max = to_merc(37.648, 126.963)
dx = x_max - x_min
dy = y_max - y_min

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

# 동선2 — 트랙 기반 묶음 방문
# (트랙, 요일, 오전 동, 오후 동: None=전일 집중, 곡률)
# 관계 회복: 같은 트랙 두 동을 하루에 묶어 반나절씩 방문
# 복지 연계: 인접 동 두 쌍으로 방문
# 역촌동(1위): 목요일 전일 집중 → 주 2회
SCHEDULE2 = [
    ("관계 회복 트랙", "월", "불광2동", "역촌동",  0.08),   # 관계회복 페어
    ("복지 연계 트랙", "화", "갈현1동", "응암3동", 0.0),    # 복지연계 1
    ("복지 연계 트랙", "수", "갈현2동", "구산동",  0.08),   # 복지연계 2
    ("관계 회복 트랙", "목", "역촌동",   None,     0.0),    # 역촌동 전일 집중 (주 2회)
]

# 동별 방문 정보 (트랙, 요일, 시간대)
DONG_VISIT = {}
for _trk, _day, _d1, _d2, _ in SCHEDULE2:
    DONG_VISIT[_d1] = (_trk, _day, "오전(08-13시)" if _d2 else "전일(08-18시)")
    if _d2:
        DONG_VISIT[_d2] = (_trk, _day, "오후(14-18시)")

LABEL_OFFSET = {
    "불광2동": ( dx*0.17,  dy*0.012),
    "갈현1동": (-dx*0.17,  dy*0.015),
    "갈현2동": (-dx*0.17, -dy*0.008),
    "구산동":  (-dx*0.17, -dy*0.016),
    "역촌동":  ( dx*0.17,  dy*0.008),
    "응암3동": (-dx*0.17, -dy*0.010),
}

fig2, ax = plt.subplots(figsize=(14, 18))
fig2.patch.set_facecolor("#FFFFFF")
ax.set_facecolor("#F8FAFC")
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)

try:
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.PositronNoLabels,
                    zoom=14, alpha=0.28)
except Exception:
    try:
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron,
                        zoom=14, alpha=0.22)
    except Exception:
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik,
                        zoom=14, alpha=0.12)

norm = Normalize(vmin=eunp["MID_POP"].min() * 0.85, vmax=eunp["MID_POP"].max())
eunp.plot(ax=ax, column="MID_POP", cmap="Blues", norm=norm,
          alpha=0.42, edgecolor="none",
          missing_kwds={"color": "#EEF2F7"}, zorder=2)
eunp.plot(ax=ax, facecolor="none", edgecolor="#C4C9D4", linewidth=0.5, zorder=3)
eunp[eunp["is_risk"]].plot(
    ax=ax, facecolor="none", edgecolor="#6B7280", linewidth=1.2, zorder=4)

for _, row in eunp.iterrows():
    if row["is_risk"]:
        continue
    c = row.geometry.centroid
    ax.text(c.x, c.y, row["ADM_NM"],
            fontsize=6.0, ha="center", va="center", color="#B0B8C8",
            path_effects=[pe.withStroke(linewidth=1.5, foreground="white")],
            zorder=5)

# 동선 화살표 (트랙 색 — SCHEDULE2 기반)
hx, hy = to_merc(*HUB_COORD)
for track, day, d1, d2, rad in SCHEDULE2:
    color = TRACK_COLOR[track]
    _, lat1, lon1 = DONG_SPOT[d1]
    x1, y1 = to_merc(lat1, lon1)
    r = rad if rad != 0.0 else 0.08
    fwd_kw = dict(arrowstyle="-|>", mutation_scale=12, lw=1.8,
                  color=color, alpha=0.70)
    if (lat1, lon1) != HUB_COORD:
        ax.annotate("", xy=(x1, y1), xytext=(hx, hy),
                    arrowprops=dict(**fwd_kw, connectionstyle=f"arc3,rad={r}"),
                    zorder=9)
    if d2 is not None:
        _, lat2, lon2 = DONG_SPOT[d2]
        x2, y2 = to_merc(lat2, lon2)
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(**fwd_kw, connectionstyle=f"arc3,rad={r}"),
                    zorder=9)

# 허브 마커
ax.scatter(hx, hy, s=480, marker="*", color="#1E3A5F",
           edgecolors="white", linewidths=1.5, zorder=14)
ax.annotate(f"★ {HUB_NAME}\n(이동형 마음편의점 허브)",
            xy=(hx, hy),
            xytext=(hx + dx*0.025, hy + dy*0.022),
            fontsize=13.0, fontweight="bold", color="#1E3A5F", ha="left",
            path_effects=[pe.withStroke(linewidth=3.0, foreground="white")],
            arrowprops=dict(arrowstyle="-", color="#6B7280", lw=0.8,
                           shrinkA=0, shrinkB=7),
            zorder=15)

# 거점 마커 — 트랙 색 + 요일·시간대 표시
for dong, (spot, lat, lon) in DONG_SPOT.items():
    if (lat, lon) == HUB_COORD:
        continue
    x, y = to_merc(lat, lon)
    track = dong_track.get(dong, "관계 회복 트랙")
    mc = TRACK_COLOR[track]
    trk_v, day_v, band_v = DONG_VISIT.get(dong, (track, "", ""))
    is_all_day = band_v == "전일(08-18시)"

    s_outer = 420 if is_all_day else 340
    s_inner = 260 if is_all_day else 200
    ew = 2.5 if is_all_day else 1.5
    ax.scatter(x, y, s=s_outer, color=mc, alpha=0.18, linewidths=0, zorder=12)
    ax.scatter(x, y, s=s_inner, color=mc, edgecolors="white", linewidths=ew,
               zorder=13)

    spot_short = (spot.replace(" 주민센터", "센터")
                      .replace("도서관마을", "도서관")
                      .replace("서울청년센터 은평", "청년센터"))
    band_short = (band_v.replace("오전(08-13시)", "오전")
                        .replace("오후(14-18시)", "오후")
                        .replace("전일(08-18시)", "전일★"))
    label = f"{dong}  {day_v} {band_short}\n{spot_short}"

    ox, oy = LABEL_OFFSET.get(dong, (0, dy * 0.010))
    ha = "left" if ox > 0 else ("right" if ox < 0 else "center")
    ax.annotate(label,
                xy=(x, y), xytext=(x + ox, y + oy),
                ha=ha, va="center",
                fontsize=13.0, fontweight="bold", color=mc,
                path_effects=[pe.withStroke(linewidth=3.0, foreground="white")],
                arrowprops=dict(arrowstyle="-", color="#9CA3AF", lw=0.7,
                               shrinkA=0, shrinkB=6),
                zorder=14)

# 컬러바
sm = ScalarMappable(cmap=plt.get_cmap("Blues"), norm=norm)
sm.set_array([])
cbar_ax = fig2.add_axes([0.88, 0.62, 0.020, 0.18])
cbar = fig2.colorbar(sm, cax=cbar_ax, orientation="vertical")
cbar.set_label("중장년\n생활인구\n(명/동)", fontsize=7.5, color="#6B7280", labelpad=4)
cbar.ax.yaxis.set_label_position("left")
cbar.ax.tick_params(labelsize=7, colors="#6B7280")
cbar.outline.set_edgecolor("#D1D5DB")

# 범례
handles_m = [
    mpatches.Patch(facecolor=TRACK_COLOR["관계 회복 트랙"],
                   label="관계 회복 트랙 (2개 동)  역촌(주 2회) + 불광2"),
    mpatches.Patch(facecolor=TRACK_COLOR["복지 연계 트랙"],
                   label="복지 연계 트랙 (4개 동)  갈현1·갈현2·구산·응암3"),
    *[Line2D([0],[0], color=TRACK_COLOR[trk], linewidth=2.0,
              marker="o", markersize=7,
              markerfacecolor=TRACK_COLOR[trk], markeredgecolor="white",
              label=f"{day}  {d1}" + (f" → {d2}" if d2 else "  [전일 집중]"))
      for trk, day, d1, d2, _ in SCHEDULE2],
    Line2D([0],[0], marker="*", color="w", markerfacecolor="#1E3A5F",
           markersize=14, label=f"허브  ({HUB_NAME})"),
    mpatches.Patch(facecolor="none", edgecolor="#6B7280", linewidth=1.2,
                   label="복합취약형 6개 동 경계"),
]
ax.legend(handles=handles_m,
          loc="lower right", bbox_to_anchor=(0.86, 0.04),
          fontsize=7.8, frameon=True, framealpha=0.96,
          edgecolor="#D1D5DB", facecolor="white",
          title="트랙 분류 · 요일별 동선", title_fontsize=9.0)

ax.set_title(
    "이동형 마음편의점 동선 2안  |  고립 차원 이원화\n"
    "관계 회복 트랙 vs 복지 연계 트랙  |  은평구 복합취약형 6개 동",
    fontsize=13, fontweight="bold", color="#1F2937", pad=14)
ax.set_axis_off()

out2 = str(BASE / "복지시설" / "dimension_route_map.png")
plt.savefig(out2, dpi=160, bbox_inches="tight", facecolor="white")
plt.close(fig2)
print(f"저장 완료: {out2}")
