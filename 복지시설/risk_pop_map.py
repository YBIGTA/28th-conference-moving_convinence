# -*- coding: utf-8 -*-
# 복합취약형 × 생활인구 지도
# A안: 전체 시간대 단일 지도 + 거점 마커
# B안: 오전/점심/오후/저녁 2×2 패널

import admdongkor as adk
import pandas as pd
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
import glob
import warnings
warnings.filterwarnings("ignore")

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# ── 공통 데이터 ───────────────────────────────────────────────────────────────
latest = adk.versions()[-1]
print(f"경계 버전: {latest}")
gdf_all = adk.get(latest, "emd", crs="EPSG:3857")
eunp_base = gdf_all[gdf_all["sggnm"] == "은평구"].copy().reset_index(drop=True)

# 복합취약형 6개 동 (고립지수 × 사각지대 분석 결과)
COMPLEX_RISK = {"응암3동", "불광2동", "역촌동", "갈현1동", "갈현2동", "구산동"}

# 거점 20곳
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

MARKER_COLOR = "#F97316"
MARKER_SIZE  = 110
CMAP         = "Blues"

BASE = Path(r"E:\서울시 빅데이터 캠퍼스\Seoul")
_all_csv = glob.glob(str(BASE / "eunpyeong" / "data" / "**" / "*.csv"), recursive=True)

def load_pop(unit, band):
    path = next(f for f in _all_csv if unit in f and band in f and "절대인구" in f)
    df = pd.read_csv(path, dtype={"H_DNG_CD": str})
    return df

def merge_gdf(band):
    df = load_pop("행정동", band)
    gdf = eunp_base.merge(df[["dong_nm", "MID_POP"]], left_on="emdnm", right_on="dong_nm", how="left")
    gdf["is_risk"] = gdf["emdnm"].isin(COMPLEX_RISK)
    return gdf

def add_basemap(ax):
    try:
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.PositronNoLabels, zoom=14, alpha=0.28)
    except Exception:
        try:
            ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=14, alpha=0.22)
        except Exception:
            ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=14, alpha=0.12)

def draw_choropleth(ax, gdf, norm, cmap):
    gdf.plot(ax=ax, column="MID_POP", cmap=cmap, norm=norm,
             alpha=0.45, edgecolor="none", missing_kwds={"color": "#EEF2F7"}, zorder=2)
    gdf.plot(ax=ax, facecolor="none", edgecolor="#C4C9D4", linewidth=0.5, zorder=3)
    gdf[gdf["is_risk"]].plot(ax=ax, facecolor="none", edgecolor="#6B7280", linewidth=1.2, zorder=4)

def draw_labels(ax, gdf):
    for _, row in gdf.iterrows():
        centroid = row.geometry.centroid
        if row["is_risk"]:
            ax.text(centroid.x, centroid.y, row["emdnm"],
                    fontsize=7.5, ha="center", va="center",
                    color="#1E3A5F", fontweight="bold",
                    path_effects=[pe.withStroke(linewidth=2.0, foreground="white")],
                    zorder=5)
        else:
            ax.text(centroid.x, centroid.y, row["emdnm"],
                    fontsize=6.0, ha="center", va="center", color="#B0B8C8",
                    path_effects=[pe.withStroke(linewidth=1.5, foreground="white")],
                    zorder=5)

def draw_markers(ax):
    for name, lat, lon in candidates:
        x, y = to_merc(lat, lon)
        ax.scatter(x, y, s=MARKER_SIZE * 2.4, marker="o",
                   color=MARKER_COLOR, alpha=0.18, linewidths=0, zorder=7)
        ax.scatter(x, y, s=MARKER_SIZE, marker="o",
                   color=MARKER_COLOR, edgecolors="none", zorder=8)
        ax.text(
            x, y + (y_max - y_min) * 0.009, name,
            fontsize=6.0, ha="center", va="bottom", color="#111827", fontweight="bold",
            path_effects=[pe.withStroke(linewidth=1.8, foreground="white")],
            zorder=9,
        )


# 동별 집계구 수 (실제 추정인구 = 집계구 평균 MID_POP × 집계구 수)
def _build_cell_cnt():
    f = next(f for f in _all_csv if "집계구" in f and "오전" in f and "절대인구" in f)
    return pd.read_csv(f).groupby("dong_nm").size().reset_index(name="cell_cnt")
cell_cnt_df = _build_cell_cnt()

# ════════════════════════════════════════════════════════════════════════════════
# A안: 전체 시간대 단일 지도
# ════════════════════════════════════════════════════════════════════════════════
gdf_all_band = merge_gdf("전체")
vals = gdf_all_band["MID_POP"].fillna(0)
norm_a = Normalize(vmin=vals.min() * 0.85, vmax=vals.max())
cmap_obj = plt.get_cmap(CMAP)

fig, ax = plt.subplots(figsize=(13, 15))
fig.patch.set_facecolor("#FFFFFF")
ax.set_facecolor("#F8FAFC")
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)

add_basemap(ax)
draw_choropleth(ax, gdf_all_band, norm_a, CMAP)
draw_labels(ax, gdf_all_band)
draw_markers(ax)

# 컬러바
sm = ScalarMappable(cmap=cmap_obj, norm=norm_a)
sm.set_array([])
cbar_ax = fig.add_axes([0.52, 0.055, 0.38, 0.016])
cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
cbar.set_label("중장년 생활인구 (명/셀·평균)", fontsize=9.0, color="#374151", labelpad=5)
cbar.ax.xaxis.set_label_position("top")
cbar.ax.tick_params(labelsize=8.0, colors="#374151")
cbar.outline.set_edgecolor("#D1D5DB")
cbar.ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:.0f}"))

# 범례
h_marker = mpatches.Circle((0.5, 0.5), radius=0.3, facecolor=MARKER_COLOR, edgecolor="none",
                            label=f"이동형 마음편의점 후보 거점 ({len(candidates)}곳)")
h_risk   = mpatches.Patch(facecolor="none", edgecolor="#6B7280", linewidth=1.2,
                           label=f"복합취약형 행정동 ({len(COMPLEX_RISK)}개동) — 고립지수↑·사각지대")
ax.legend(handles=[h_marker, h_risk], loc="lower left", bbox_to_anchor=(0.01, 0.01),
          fontsize=9.0, frameon=True, framealpha=0.95, edgecolor="#D1D5DB", facecolor="white",
          borderpad=0.9)

date_str = f"{latest[:4]}.{latest[4:6]}.{latest[6:]}"
ax.set_title("복합취약형 × 중장년 생활인구  |  서울시 은평구",
             fontsize=16, fontweight="bold", color="#111827", pad=14, loc="left")
ax.text(0.0, 1.013,
        f"중장년(40–64세) 생활인구 기반 입지 우선순위 분석  ·  경계: {date_str}  ·  생활인구: 08–20시 평균",
        transform=ax.transAxes, fontsize=9.0, color="#6B7280")
ax.set_axis_off()

plt.tight_layout(pad=1.2)
out_a = str(BASE / "복지시설" / "복합위험_생활인구_단일.png")
plt.savefig(out_a, dpi=180, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"저장 완료: {out_a}")


# ════════════════════════════════════════════════════════════════════════════════
# B안: 오전/점심/오후/저녁 2×2 패널
# ════════════════════════════════════════════════════════════════════════════════
BANDS = [("오전", "08–11시"), ("점심", "11–14시"), ("오후", "14–17시"), ("저녁", "17–20시")]

# 4개 시간대 공통 norm (비교 가능하도록)
all_vals = pd.concat(
    [load_pop("행정동", b)["MID_POP"] for b, _ in BANDS]
).dropna()
norm_b = Normalize(vmin=all_vals.min() * 0.85, vmax=all_vals.max())

fig, axes = plt.subplots(2, 2, figsize=(22, 24))
fig.patch.set_facecolor("#FFFFFF")

for idx, (band, label) in enumerate(BANDS):
    ax = axes[idx // 2][idx % 2]
    gdf = merge_gdf(band)

    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    add_basemap(ax)
    draw_choropleth(ax, gdf, norm_b, CMAP)
    draw_labels(ax, gdf)

    ax.set_title(label, fontsize=17, fontweight="bold", color="#111827", pad=10)
    ax.set_axis_off()

# 공통 컬러바 (fig 하단 중앙)
sm_b = ScalarMappable(cmap=plt.get_cmap(CMAP), norm=norm_b)
sm_b.set_array([])
cbar_ax_b = fig.add_axes([0.25, 0.04, 0.50, 0.012])
cbar_b = fig.colorbar(sm_b, cax=cbar_ax_b, orientation="horizontal")
cbar_b.set_label("중장년 생활인구 (명/셀·평균)  —  4개 시간대 공통 스케일", fontsize=11, color="#374151", labelpad=6)
cbar_b.ax.xaxis.set_label_position("top")
cbar_b.ax.tick_params(labelsize=10, colors="#374151")
cbar_b.outline.set_edgecolor("#D1D5DB")
cbar_b.ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:.0f}"))

# 공통 범례 (fig 하단 왼쪽)
h_risk_b = mpatches.Patch(facecolor="none", edgecolor="#6B7280", linewidth=1.2,
                           label=f"복합취약형 행정동 ({len(COMPLEX_RISK)}개동)")
fig.legend(handles=[h_risk_b], loc="lower left", bbox_to_anchor=(0.02, 0.055),
           fontsize=11, frameon=True, framealpha=0.95, edgecolor="#D1D5DB", facecolor="white")

fig.suptitle(
    "시간대별 중장년 생활인구  ×  복합취약형 행정동  |  서울시 은평구",
    fontsize=20, fontweight="bold", color="#111827", y=0.98,
)
fig.text(0.5, 0.965,
         f"중장년(40–64세) · 08–20시 · 경계: {date_str}  |  회색 실선 = 복합취약형 행정동",
         ha="center", fontsize=11, color="#6B7280")

plt.subplots_adjust(left=0.02, right=0.98, top=0.955, bottom=0.07, hspace=0.04, wspace=0.03)
out_b = str(BASE / "복지시설" / "복합위험_생활인구_시간대.png")
plt.savefig(out_b, dpi=160, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"저장 완료: {out_b}")


# ════════════════════════════════════════════════════════════════════════════════
# C안: 저녁–오전 실제 추정인구 차이 (집계구 평균 × 집계구 수)
# ════════════════════════════════════════════════════════════════════════════════
def _est_pop(band, col_out):
    return (load_pop("행정동", band)[["dong_nm", "MID_POP"]]
            .merge(cell_cnt_df, on="dong_nm", how="left")
            .assign(**{col_out: lambda d: d["MID_POP"] * d["cell_cnt"]})
            [["dong_nm", col_out]])

df_am = _est_pop("오전", "pop_am")
df_ev = _est_pop("저녁", "pop_ev")
df_diff_abs = df_am.merge(df_ev, on="dong_nm", how="outer")
df_diff_abs["pop_diff"] = df_diff_abs["pop_ev"] - df_diff_abs["pop_am"]

gdf_c = eunp_base.merge(df_diff_abs, left_on="emdnm", right_on="dong_nm", how="left")
gdf_c["is_risk"] = gdf_c["emdnm"].isin(COMPLEX_RISK)

vmax_c = gdf_c.loc[gdf_c["is_risk"], "pop_diff"].abs().max()
norm_c = Normalize(vmin=-vmax_c, vmax=vmax_c)

fig, ax = plt.subplots(figsize=(13, 15))
fig.patch.set_facecolor("#FFFFFF")
ax.set_facecolor("#F8FAFC")
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)
add_basemap(ax)

# 비복합취약형: 단색, 경계없음
gdf_c[~gdf_c["is_risk"]].plot(ax=ax, facecolor="#E8EDF2", edgecolor="none", zorder=2)

# 복합취약형 6개 동: diverging choropleth
gdf_c[gdf_c["is_risk"]].plot(ax=ax, column="pop_diff", cmap="RdBu_r", norm=norm_c,
                              alpha=0.55, edgecolor="#6B7280", linewidth=1.0, zorder=3)

# 은평구 전체 윤곽만 얇게
eunp_base.dissolve().plot(ax=ax, facecolor="none", edgecolor="#BCC5CE", linewidth=0.7, zorder=4)

# 복합취약형 6개 동: 외부 인출 레이블
_dx_c = x_max - x_min
_dy_c = y_max - y_min
_OFFSET_C = {
    "불광2동": ( _dx_c*0.18,  _dy_c*0.028),
    "갈현1동": (-_dx_c*0.17,  _dy_c*0.020),
    "갈현2동": (-_dx_c*0.18, -_dy_c*0.008),
    "구산동":  (-_dx_c*0.18, -_dy_c*0.030),
    "역촌동":  ( _dx_c*0.16,  _dy_c*0.005),
    "응암3동": ( _dx_c*0.16, -_dy_c*0.048),
}
for _, row in gdf_c[gdf_c["is_risk"]].iterrows():
    c = row.geometry.centroid
    dong = row["emdnm"]
    diff_val = row["pop_diff"]
    if pd.isna(diff_val):
        continue
    ox, oy = _OFFSET_C.get(dong, (_dx_c*0.15, _dy_c*0.015))
    ha = "left" if ox > 0 else "right"
    ax.annotate(f"{dong}\n{diff_val:+,.0f}명",
                xy=(c.x, c.y), xytext=(c.x + ox, c.y + oy),
                ha=ha, va="center",
                fontsize=15.5, fontweight="bold", color="#111827",
                path_effects=[pe.withStroke(linewidth=3.2, foreground="white")],
                arrowprops=dict(arrowstyle="-", color="#6B7280", lw=0.9,
                               shrinkA=5, shrinkB=0),
                zorder=8)

sm_c = ScalarMappable(cmap=plt.get_cmap("RdBu_r"), norm=norm_c)
sm_c.set_array([])
cbar_ax_c = fig.add_axes([0.52, 0.055, 0.38, 0.016])
cbar_c = fig.colorbar(sm_c, cax=cbar_ax_c, orientation="horizontal")
cbar_c.set_label("중장년 생활인구 저녁–오전 차이 (명 추정)", fontsize=9.0, color="#374151", labelpad=5)
cbar_c.ax.xaxis.set_label_position("top")
cbar_c.ax.tick_params(labelsize=8.0, colors="#374151")
cbar_c.outline.set_edgecolor("#D1D5DB")
cbar_c.ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:+,.0f}"))

h_blue = mpatches.Patch(facecolor="#4393C3", label="저녁 인구 > 오전 (외부 유입)")
h_red  = mpatches.Patch(facecolor="#D6604D", label="오전 인구 > 저녁 (이른 활동)")
h_risk_c = mpatches.Patch(facecolor="none", edgecolor="#6B7280", linewidth=1.0,
                           label=f"복합취약형 행정동 ({len(COMPLEX_RISK)}개동)")
ax.legend(handles=[h_blue, h_red, h_risk_c], loc="lower left", bbox_to_anchor=(0.01, 0.01),
          fontsize=9.0, frameon=True, framealpha=0.95, edgecolor="#D1D5DB", facecolor="white",
          borderpad=0.9)
ax.set_title("중장년 생활인구 저녁–오전 차이  |  서울시 은평구",
             fontsize=16, fontweight="bold", color="#111827", pad=14, loc="left")
ax.text(0.0, 1.013,
        "추정인구 = 집계구 평균 × 집계구 수  |  파란색: 저녁 > 오전  /  빨간색: 오전 > 저녁",
        transform=ax.transAxes, fontsize=9.0, color="#6B7280")
ax.set_axis_off()
plt.tight_layout(pad=1.2)
out_c = str(BASE / "복지시설" / "복합위험_생활인구_저녁오전차이.png")
plt.savefig(out_c, dpi=180, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"저장 완료: {out_c}")


# ════════════════════════════════════════════════════════════════════════════════
# D안: 중장년 비율(%p) 저녁–오전 차이
# ════════════════════════════════════════════════════════════════════════════════
df_am_full = load_pop("행정동", "오전")
df_ev_full = load_pop("행정동", "저녁")

if "TOT_POP" in df_am_full.columns:
    df_am_full["mid_rate"] = df_am_full["MID_POP"] / df_am_full["TOT_POP"].replace(0, float("nan")) * 100
    df_ev_full["mid_rate"] = df_ev_full["MID_POP"] / df_ev_full["TOT_POP"].replace(0, float("nan")) * 100
    rate_label = "중장년 비율(%p) 저녁–오전 차이"
    rate_fmt = lambda x, _: f"{x:+.2f}"
else:
    am_sum = df_am_full["MID_POP"].sum()
    ev_sum = df_ev_full["MID_POP"].sum()
    df_am_full["mid_rate"] = df_am_full["MID_POP"] / am_sum * 100
    df_ev_full["mid_rate"] = df_ev_full["MID_POP"] / ev_sum * 100
    rate_label = "동별 생활인구 비중(%p) 저녁–오전 차이"
    rate_fmt = lambda x, _: f"{x:+.3f}"

df_rate_diff = df_am_full[["dong_nm", "mid_rate"]].rename(columns={"mid_rate": "rate_am"}).merge(
    df_ev_full[["dong_nm", "mid_rate"]].rename(columns={"mid_rate": "rate_ev"}),
    on="dong_nm", how="outer"
)
df_rate_diff["rate_diff"] = df_rate_diff["rate_ev"] - df_rate_diff["rate_am"]

gdf_d = eunp_base.merge(df_rate_diff, left_on="emdnm", right_on="dong_nm", how="left")
gdf_d["is_risk"] = gdf_d["emdnm"].isin(COMPLEX_RISK)

vmax_d = gdf_d["rate_diff"].abs().quantile(0.98)
norm_d = Normalize(vmin=-vmax_d, vmax=vmax_d)

fig, ax = plt.subplots(figsize=(13, 15))
fig.patch.set_facecolor("#FFFFFF")
ax.set_facecolor("#F8FAFC")
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)
add_basemap(ax)
gdf_d.plot(ax=ax, column="rate_diff", cmap="RdBu_r", norm=norm_d,
           alpha=0.55, edgecolor="none", missing_kwds={"color": "#EEF2F7"}, zorder=2)
gdf_d.plot(ax=ax, facecolor="none", edgecolor="#C4C9D4", linewidth=0.5, zorder=3)
gdf_d[gdf_d["is_risk"]].plot(ax=ax, facecolor="none", edgecolor="#6B7280", linewidth=1.2, zorder=4)
draw_labels(ax, gdf_d)

sm_d = ScalarMappable(cmap=plt.get_cmap("RdBu_r"), norm=norm_d)
sm_d.set_array([])
cbar_ax_d = fig.add_axes([0.52, 0.055, 0.38, 0.016])
cbar_d = fig.colorbar(sm_d, cax=cbar_ax_d, orientation="horizontal")
cbar_d.set_label(rate_label, fontsize=9.0, color="#374151", labelpad=5)
cbar_d.ax.xaxis.set_label_position("top")
cbar_d.ax.tick_params(labelsize=8.0, colors="#374151")
cbar_d.outline.set_edgecolor("#D1D5DB")
cbar_d.ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(rate_fmt))

h_blue_d = mpatches.Patch(facecolor="#4393C3", label="저녁 비율 > 오전 (파란색)")
h_red_d  = mpatches.Patch(facecolor="#D6604D", label="오전 비율 > 저녁 (빨간색)")
h_risk_d = mpatches.Patch(facecolor="none", edgecolor="#6B7280", linewidth=1.2,
                           label=f"복합취약형 행정동 ({len(COMPLEX_RISK)}개동)")
ax.legend(handles=[h_blue_d, h_red_d, h_risk_d], loc="lower left", bbox_to_anchor=(0.01, 0.01),
          fontsize=9.0, frameon=True, framealpha=0.95, edgecolor="#D1D5DB", facecolor="white",
          borderpad=0.9)
ax.set_title("중장년 비율 저녁–오전 차이  |  서울시 은평구",
             fontsize=16, fontweight="bold", color="#111827", pad=14, loc="left")
ax.text(0.0, 1.013, "파란색: 저녁 비율 높음 / 빨간색: 오전 비율 높음  |  복합취약형 동 = 회색 경계",
        transform=ax.transAxes, fontsize=9.0, color="#6B7280")
ax.set_axis_off()
plt.tight_layout(pad=1.2)
out_d = str(BASE / "복지시설" / "복합위험_비율_저녁오전차이.png")
plt.savefig(out_d, dpi=180, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"저장 완료: {out_d}")


# ════════════════════════════════════════════════════════════════════════════════
# E안: 피크 시간대 분류 지도 (스케줄 설계 근거)
# ════════════════════════════════════════════════════════════════════════════════
df_peak = df_am.merge(df_ev, on="dong_nm", how="outer")
df_peak["peak"] = df_peak.apply(
    lambda r: "오전 피크" if r["pop_am"] >= r["pop_ev"] else "저녁 피크", axis=1
)

gdf_e = eunp_base.merge(df_peak, left_on="emdnm", right_on="dong_nm", how="left")
gdf_e["is_risk"] = gdf_e["emdnm"].isin(COMPLEX_RISK)
gdf_e["peak"] = gdf_e["peak"].fillna("미분류")

COLOR_PEAK = {"오전 피크": "#FCD34D", "저녁 피크": "#60A5FA", "미분류": "#EEF2F7"}

fig, ax = plt.subplots(figsize=(13, 15))
fig.patch.set_facecolor("#FFFFFF")
ax.set_facecolor("#F8FAFC")
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)
add_basemap(ax)

for peak_val, color in COLOR_PEAK.items():
    sub = gdf_e[gdf_e["peak"] == peak_val]
    if not sub.empty:
        sub.plot(ax=ax, facecolor=color, alpha=0.55, edgecolor="none", zorder=2)

gdf_e.plot(ax=ax, facecolor="none", edgecolor="#C4C9D4", linewidth=0.5, zorder=3)
gdf_e[gdf_e["is_risk"]].plot(ax=ax, facecolor="none", edgecolor="#6B7280", linewidth=1.2, zorder=4)

# 비복합취약형 동: 소형 회색 레이블
for _, row in gdf_e[~gdf_e["is_risk"]].iterrows():
    c = row.geometry.centroid
    ax.text(c.x, c.y, row["emdnm"],
            fontsize=6.0, ha="center", va="center", color="#B5BEC8",
            path_effects=[pe.withStroke(linewidth=1.0, foreground="white")], zorder=5)

# 복합취약형 6개 동: 외부 인출 레이블
_dx_e = x_max - x_min
_dy_e = y_max - y_min
_OFFSET_E = {
    "불광2동": ( _dx_e*0.18,  _dy_e*0.028),
    "갈현1동": (-_dx_e*0.17,  _dy_e*0.020),
    "갈현2동": (-_dx_e*0.18, -_dy_e*0.008),
    "구산동":  (-_dx_e*0.18, -_dy_e*0.030),
    "역촌동":  ( _dx_e*0.16,  _dy_e*0.005),
    "응암3동": ( _dx_e*0.16, -_dy_e*0.048),
}
_PEAK_LABEL = {"오전 피크": "오전피크", "저녁 피크": "저녁피크"}
for _, row in gdf_e[gdf_e["is_risk"]].iterrows():
    c = row.geometry.centroid
    dong = row["emdnm"]
    peak_str = _PEAK_LABEL.get(row["peak"], "")
    ox, oy = _OFFSET_E.get(dong, (_dx_e*0.15, _dy_e*0.015))
    ha = "left" if ox > 0 else "right"
    ax.annotate(f"{dong}\n{peak_str}",
                xy=(c.x, c.y), xytext=(c.x + ox, c.y + oy),
                ha=ha, va="center",
                fontsize=12.5, fontweight="bold", color="#111827",
                path_effects=[pe.withStroke(linewidth=2.8, foreground="white")],
                arrowprops=dict(arrowstyle="-", color="#6B7280", lw=0.9,
                               shrinkA=5, shrinkB=0),
                zorder=8)

n_am = (df_peak["peak"] == "오전 피크").sum()
n_ev = (df_peak["peak"] == "저녁 피크").sum()
h_am_e = mpatches.Patch(facecolor="#FCD34D", alpha=0.55, label=f"오전 피크  ({n_am}개동)")
h_ev_e = mpatches.Patch(facecolor="#60A5FA", alpha=0.55, label=f"저녁 피크  ({n_ev}개동)")
h_risk_e = mpatches.Patch(facecolor="none", edgecolor="#6B7280", linewidth=1.2,
                           label=f"복합취약형 행정동 ({len(COMPLEX_RISK)}개동)")
ax.legend(handles=[h_am_e, h_ev_e, h_risk_e], loc="lower left", bbox_to_anchor=(0.01, 0.01),
          fontsize=9.0, frameon=True, framealpha=0.95, edgecolor="#D1D5DB", facecolor="white",
          borderpad=0.9)
ax.set_title("생활인구 피크 시간대 분류  |  서울시 은평구",
             fontsize=16, fontweight="bold", color="#111827", pad=14, loc="left")
ax.text(0.0, 1.013,
        "중장년(40–64세) 오전(08–11시) vs 저녁(17–20시) 생활인구 비교  ·  이동형 동선 스케줄 설계 근거",
        transform=ax.transAxes, fontsize=9.0, color="#6B7280")
ax.set_axis_off()
plt.tight_layout(pad=1.2)
out_e = str(BASE / "복지시설" / "생활인구_피크시간대.png")
plt.savefig(out_e, dpi=180, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"저장 완료: {out_e}")
