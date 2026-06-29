# -*- coding: utf-8 -*-
# 집계구 단위 생활인구 × 거점 검증 지도

import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import contextily as ctx
from pyproj import Transformer
from pathlib import Path
import glob
import warnings
warnings.filterwarnings("ignore")

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

BASE = Path(r"E:\서울시 빅데이터 캠퍼스\Seoul")

# ── 경계 데이터 (통계지역경계 shp) ───────────────────────────────────────────
dong_shp = gpd.read_file(str(BASE / "통계지역경계(2016년+기준)" / "행정구역.shp"), encoding="cp949")
eunp_base = dong_shp[dong_shp["SIGUNGU_NM"] == "은평구"].copy().reset_index(drop=True)
eunp_base = eunp_base.set_crs("EPSG:5179", allow_override=True).to_crs("EPSG:3857")

COMPLEX_RISK = {"응암3동", "불광2동", "역촌동", "갈현1동", "갈현2동", "구산동"}
eunp_dongs   = set(eunp_base["ADM_NM"].tolist())

# ── 집계구 shapefile ──────────────────────────────────────────────────────────
shp = gpd.read_file(str(BASE / "통계지역경계(2016년+기준)" / "집계구.shp"), encoding="cp949")
shp = shp[shp["ADM_NM"].isin(eunp_dongs)].copy().reset_index(drop=True)
shp = shp.set_crs("EPSG:5179", allow_override=True).to_crs("EPSG:3857")

# ── 생활인구 CSV 조인 (glob으로 실제 경로 탐색) ───────────────────────────────
_all_csv = glob.glob(str(BASE / "eunpyeong" / "data" / "**" / "*.csv"), recursive=True)
_oa_path = next(f for f in _all_csv if "집계구" in f and "전체" in f and "절대인구" in f)
oa_df = pd.read_csv(_oa_path, dtype={"OA_CD": str, "H_DNG_CD": str})
shp = shp.merge(oa_df[["OA_CD", "MID_POP"]], left_on="TOT_REG_CD", right_on="OA_CD", how="left")

# ── 복합취약형 6개 동 거점 + 허브 ───────────────────────────────────────────
candidates = [
    ("불광2동 주민센터",  37.626383, 126.927266),
    ("갈현1동 주민센터",  37.623700, 126.916695),
    ("갈현2동 주민센터",  37.618586, 126.915839),
    ("구산동도서관마을",  37.609518, 126.913097),
    ("역촌동 주민센터",   37.604429, 126.915108),
    ("응암3동 주민센터",  37.592246, 126.915734),
]
HUB = ("신사종합사회복지관", 37.598056, 126.912212)

tf = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
def to_merc(lat, lon):
    return tf.transform(lon, lat)

x_min, y_min = to_merc(37.568, 126.876)
x_max, y_max = to_merc(37.648, 126.963)

# ── 컬러 설정 ─────────────────────────────────────────────────────────────────
MARKER_COLOR = "#1D4ED8"   # 파란색 (YlOrRd 대비)
MARKER_SIZE  = 110
CMAP         = "YlOrRd"

vmax = shp["MID_POP"].quantile(0.97)
norm = Normalize(vmin=0, vmax=vmax)

# ── 지도 그리기 ───────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 15))
fig.patch.set_facecolor("#FFFFFF")
ax.set_facecolor("#F8FAFC")
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)

try:
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.PositronNoLabels, zoom=14, alpha=0.28)
except Exception:
    try:
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=14, alpha=0.22)
    except Exception:
        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=14, alpha=0.12)

# 집계구 choropleth
shp.plot(ax=ax, column="MID_POP", cmap=CMAP, norm=norm,
         alpha=0.60, edgecolor="none", missing_kwds={"color": "#EEF2F7"}, zorder=2)

# 행정동 경계
eunp_base.plot(ax=ax, facecolor="none", edgecolor="#C4C9D4", linewidth=0.5, zorder=3)

# 복합취약형 강조 테두리
eunp_base[eunp_base["ADM_NM"].isin(COMPLEX_RISK)].plot(
    ax=ax, facecolor="none", edgecolor="#6B7280", linewidth=1.5, zorder=4)

# 행정동 라벨
for _, row in eunp_base.iterrows():
    c = row.geometry.centroid
    if row["ADM_NM"] in COMPLEX_RISK:
        ax.text(c.x, c.y, row["ADM_NM"], fontsize=12.0, ha="center", va="center",
                color="#1E3A5F", fontweight="bold",
                path_effects=[pe.withStroke(linewidth=2.5, foreground="white")], zorder=5)
    else:
        ax.text(c.x, c.y, row["ADM_NM"], fontsize=7.0, ha="center", va="center",
                color="#B0B8C8",
                path_effects=[pe.withStroke(linewidth=1.5, foreground="white")], zorder=5)

# 거점 마커 & 외부 인출 레이블
dx = x_max - x_min
dy = y_max - y_min
SPOT_OFFSET = {
    "불광2동 주민센터": ( dx*0.17,  dy*0.014),
    "갈현1동 주민센터": (-dx*0.16,  dy*0.016),
    "갈현2동 주민센터": (-dx*0.17, -dy*0.008),
    "구산동도서관마을": (-dx*0.17, -dy*0.020),
    "역촌동 주민센터":  ( dx*0.16,  dy*0.006),
    "응암3동 주민센터": ( dx*0.16, -dy*0.040),
}
for name, lat, lon in candidates:
    x, y = to_merc(lat, lon)
    ax.scatter(x, y, s=MARKER_SIZE * 2.4, marker="o",
               color=MARKER_COLOR, alpha=0.18, linewidths=0, zorder=7)
    ax.scatter(x, y, s=MARKER_SIZE, marker="o",
               color=MARKER_COLOR, edgecolors="white", linewidths=0.8, zorder=8)
    ox, oy = SPOT_OFFSET.get(name, (dx*0.14, dy*0.012))
    ha = "left" if ox > 0 else "right"
    ax.annotate(name,
                xy=(x, y), xytext=(x + ox, y + oy),
                ha=ha, va="center",
                fontsize=12.0, fontweight="bold", color="#1E3A5F",
                path_effects=[pe.withStroke(linewidth=2.8, foreground="white")],
                arrowprops=dict(arrowstyle="-", color="#9CA3AF", lw=0.8,
                               shrinkA=5, shrinkB=0),
                zorder=9)

# ── 컬러바 ────────────────────────────────────────────────────────────────────
sm = ScalarMappable(cmap=plt.get_cmap(CMAP), norm=norm)
sm.set_array([])
cbar_ax = fig.add_axes([0.52, 0.055, 0.38, 0.016])
cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
cbar.set_label("중장년 생활인구 (명/집계구·평균, 08–20시)", fontsize=9.0, color="#374151", labelpad=5)
cbar.ax.xaxis.set_label_position("top")
cbar.ax.tick_params(labelsize=8.0, colors="#374151")
cbar.outline.set_edgecolor("#D1D5DB")
ax.text(0.52, 0.042, f"※ 상위 3% 클리핑 (최대 {vmax:.0f}명 기준)",
        transform=ax.transAxes, fontsize=7.5, color="#9CA3AF")

# ── 범례 ─────────────────────────────────────────────────────────────────────
# 허브 마커 (별)
hx, hy = to_merc(HUB[1], HUB[2])
ax.scatter(hx, hy, s=520, marker="*", color="#1E3A5F", edgecolors="white",
           linewidths=1.5, zorder=12)
ax.annotate(f"★ {HUB[0]}\n(이동형 마음편의점 허브)",
            xy=(hx, hy), xytext=(hx + dx*0.14, hy + dy*0.022),
            ha="left", va="center",
            fontsize=11.0, fontweight="bold", color="#1E3A5F",
            path_effects=[pe.withStroke(linewidth=2.8, foreground="white")],
            arrowprops=dict(arrowstyle="-", color="#6B7280", lw=0.8,
                           shrinkA=6, shrinkB=0),
            zorder=13)

h_marker = mpatches.Circle((0.5, 0.5), radius=0.3, facecolor=MARKER_COLOR, edgecolor="white",
                            label=f"복합취약형 동 거점 ({len(candidates)}곳)")
h_hub    = mpatches.RegularPolygon((0.5, 0.5), numVertices=5, radius=0.4,
                                   facecolor="#1E3A5F", edgecolor="white",
                                   label="이동형 마음편의점 허브 (신사종합사회복지관)")
h_risk   = mpatches.Patch(facecolor="none", edgecolor="#6B7280", linewidth=1.5,
                           label=f"복합취약형 행정동 ({len(COMPLEX_RISK)}개동)")
ax.legend(handles=[h_marker, h_hub, h_risk], loc="lower left", bbox_to_anchor=(0.01, 0.01),
          fontsize=9.0, frameon=True, framealpha=0.95, edgecolor="#D1D5DB", facecolor="white",
          borderpad=0.9)

ax.set_title("집계구 단위 중장년 생활인구 × 거점 위치 검증  |  서울시 은평구",
             fontsize=15, fontweight="bold", color="#111827", pad=14, loc="left")
ax.text(0.0, 1.013,
        "중장년(40–64세) 08–20시 평균 · 집계구 946개 · 경계: 통계청 행정구역(2016+)  |  회색 실선 = 복합취약형 행정동",
        transform=ax.transAxes, fontsize=9.0, color="#6B7280")
ax.set_axis_off()

plt.tight_layout(pad=1.2)
out = str(BASE / "복지시설" / "집계구_생활인구_거점검증.png")
plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"저장 완료: {out}")
