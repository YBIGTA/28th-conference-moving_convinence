# -*- coding: utf-8 -*-
# 평일 vs 주말 중장년 생활인구 2패널 지도

import geopandas as gpd
import pandas as pd
import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.ticker
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

# ── glob으로 실제 경로 탐색 (Mac NFD 경로 우회) ───────────────────────────────
all_csv = glob.glob(str(BASE / "eunpyeong" / "data" / "**" / "*.csv"), recursive=True)

def find_csv(unit, keyword, metric):
    for f in all_csv:
        if unit in f and keyword in f and metric in f:
            return f
    return None

# ── 경계 데이터 ───────────────────────────────────────────────────────────────
dong_shp = gpd.read_file(str(BASE / "통계지역경계(2016년+기준)" / "행정구역.shp"), encoding="cp949")
eunp_base = dong_shp[dong_shp["SIGUNGU_NM"] == "은평구"].copy().reset_index(drop=True)
eunp_base = eunp_base.set_crs("EPSG:5179", allow_override=True).to_crs("EPSG:3857")

COMPLEX_RISK = {"응암3동","불광2동","역촌동","갈현1동","갈현2동","구산동"}

# ── 거점 20곳 ─────────────────────────────────────────────────────────────────
candidates = [
    ("녹번종합사회복지관",     37.602715, 126.931803),
    ("은평평화공원",           37.605149, 126.923042),
    ("불광근린공원",           37.619257, 126.929725),
    ("은평구립도서관",         37.619012, 126.928307),
    ("신사종합사회복지관",     37.598056, 126.912212),
    ("시립은평청소년센터",     37.594199, 126.924428),
    ("서울청년센터 은평",      37.610719, 126.928472),
    ("은평구청",               37.602784, 126.929164),
    ("구산동도서관마을",       37.609518, 126.913097),
    ("은평종합사회복지관",     37.586025, 126.888843),
    ("시립은평노인종합복지관", 37.632018, 126.930342),
    ("갈현1동 주민센터",       37.623700, 126.916695),
    ("갈현2동 주민센터",       37.618586, 126.915839),
    ("불광2동 주민센터",       37.626383, 126.927266),
    ("신사2동 주민센터",       37.590280, 126.908419),
    ("증산동 주민센터",        37.584344, 126.907051),
    ("응암1동 주민센터",       37.600700, 126.926766),
    ("응암3동 주민센터",       37.592246, 126.915734),
    ("대조동 주민센터",        37.614189, 126.920825),
    ("역촌동 주민센터",        37.604429, 126.915108),
]

tf = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
def to_merc(lat, lon):
    return tf.transform(lon, lat)

x_min, y_min = to_merc(37.568, 126.876)
x_max, y_max = to_merc(37.648, 126.963)

WEEKDAYS = ["월요일","화요일","수요일","목요일","금요일"]
WEEKENDS = ["토요일","일요일"]

# ── 평일/주말 평균 MID_POP 계산 ───────────────────────────────────────────────
def load_avg(days):
    parts = []
    for d in days:
        path = find_csv("행정동", d, "절대인구")
        df = pd.read_csv(path, dtype={"H_DNG_CD": str})
        parts.append(df[["dong_nm","MID_POP"]])
    combined = pd.concat(parts)
    return combined.groupby("dong_nm")["MID_POP"].mean().reset_index()

wd_df = load_avg(WEEKDAYS).rename(columns={"MID_POP": "MID_POP"})
we_df = load_avg(WEEKENDS).rename(columns={"MID_POP": "MID_POP"})

def merge_gdf(pop_df):
    gdf = eunp_base.merge(pop_df, left_on="ADM_NM", right_on="dong_nm", how="left")
    gdf["is_risk"] = gdf["ADM_NM"].isin(COMPLEX_RISK)
    return gdf

gdf_wd = merge_gdf(wd_df)
gdf_we = merge_gdf(we_df)

# 두 패널 공통 norm
all_vals = pd.concat([wd_df["MID_POP"], we_df["MID_POP"]]).dropna()
norm = Normalize(vmin=all_vals.min() * 0.85, vmax=all_vals.max())
CMAP = "Blues"
MARKER_COLOR = "#1D4ED8"
MARKER_SIZE  = 90

# ── 공통 드로잉 함수 ─────────────────────────────────────────────────────────
def draw_panel(ax, gdf, title):
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

    gdf.plot(ax=ax, column="MID_POP", cmap=CMAP, norm=norm,
             alpha=0.45, edgecolor="none", missing_kwds={"color": "#EEF2F7"}, zorder=2)
    gdf.plot(ax=ax, facecolor="none", edgecolor="#C4C9D4", linewidth=0.5, zorder=3)
    gdf[gdf["is_risk"]].plot(
        ax=ax, facecolor="none", edgecolor="#6B7280",
        linewidth=1.2, zorder=4)

    for _, row in gdf.iterrows():
        c = row.geometry.centroid
        if row["is_risk"]:
            ax.text(c.x, c.y, row["ADM_NM"], fontsize=7.5, ha="center", va="center",
                    color="#1E3A5F", fontweight="bold",
                    path_effects=[pe.withStroke(linewidth=2.0, foreground="white")],
                    zorder=5)
        else:
            ax.text(c.x, c.y, row["ADM_NM"], fontsize=6.0, ha="center", va="center",
                    color="#B0B8C8",
                    path_effects=[pe.withStroke(linewidth=1.5, foreground="white")],
                    zorder=5)

    for name, lat, lon in candidates:
        x, y = to_merc(lat, lon)
        ax.scatter(x, y, s=MARKER_SIZE * 2.4, color=MARKER_COLOR, alpha=0.18,
                   linewidths=0, zorder=7)
        ax.scatter(x, y, s=MARKER_SIZE, color=MARKER_COLOR, edgecolors="white",
                   linewidths=0.8, zorder=8)
        ax.text(x, y + (y_max - y_min) * 0.009, name,
                fontsize=5.2, ha="center", va="bottom", color="#1E3A5F", fontweight="bold",
                path_effects=[pe.withStroke(linewidth=1.5, foreground="white")], zorder=9)

    ax.set_title(title, fontsize=18, fontweight="bold", color="#111827", pad=12)
    ax.set_axis_off()

# ── 그리기 ────────────────────────────────────────────────────────────────────
fig, (ax_wd, ax_we) = plt.subplots(1, 2, figsize=(24, 15))
fig.patch.set_facecolor("#FFFFFF")

draw_panel(ax_wd, gdf_wd, "평일 (월~금) 평균")
draw_panel(ax_we, gdf_we, "주말 (토~일) 평균")

# 공통 컬러바
sm = ScalarMappable(cmap=plt.get_cmap(CMAP), norm=norm)
sm.set_array([])
cbar_ax = fig.add_axes([0.25, 0.045, 0.50, 0.014])
cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
cbar.set_label("중장년 생활인구 (명/행정동·평균, 08–20시)", fontsize=11, color="#374151", labelpad=5)
cbar.ax.xaxis.set_label_position("top")
cbar.ax.tick_params(labelsize=10, colors="#374151")
cbar.outline.set_edgecolor("#D1D5DB")
cbar.ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:.0f}"))

# 범례
h_marker = mpatches.Circle((0.5, 0.5), radius=0.3, facecolor=MARKER_COLOR, edgecolor="white",
                            label=f"이동형 마음편의점 후보 거점 ({len(candidates)}곳)")
h_risk   = mpatches.Patch(facecolor="none", edgecolor="#6B7280", linewidth=1.2,
                           label=f"복합취약형 행정동 ({len(COMPLEX_RISK)}개동)")
fig.legend(handles=[h_marker, h_risk], loc="lower left", bbox_to_anchor=(0.02, 0.08),
           fontsize=11, frameon=True, framealpha=0.95, edgecolor="#D1D5DB", facecolor="white")

fig.suptitle(
    "평일 vs 주말 중장년 생활인구  |  서울시 은평구",
    fontsize=22, fontweight="bold", color="#111827", y=0.97,
)
fig.text(0.5, 0.955,
         "중장년(40–64세) · 08–20시 · 양쪽 공통 컬러 스케일  |  회색 실선 = 복합취약형 행정동",
         ha="center", fontsize=11, color="#6B7280")

plt.subplots_adjust(left=0.01, right=0.99, top=0.94, bottom=0.09, wspace=0.04)
out = str(BASE / "복지시설" / "평일_주말_생활인구.png")
plt.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"저장 완료: {out}")
