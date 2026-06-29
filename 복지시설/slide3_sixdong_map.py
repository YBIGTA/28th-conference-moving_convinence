# -*- coding: utf-8 -*-
# Slide 3용: 복합취약형 6개 동 확정 — 은평구 고립지수 choropleth

import admdongkor as adk
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib.patches as mpatches
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
import contextily as ctx
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# 파스텔 웜톤 커스텀 컬러맵: 크림 → 살구 → 뮤트 코랄
PASTEL_RISK_CMAP = LinearSegmentedColormap.from_list(
    "pastel_risk", ["#FFF3E8", "#FCCB95", "#EF9264"], N=256)

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

BASE = Path(r"E:\서울시 빅데이터 캠퍼스\Seoul")

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
p = next(BASE.rglob("중장년_연간_고립지수.csv"))
df = pd.read_csv(p)

COMPLEX_RISK = {"응암3동","불광2동","역촌동","갈현1동","갈현2동","구산동"}

# 6개 동 데이터
df6 = df[df["행정동"].isin(COMPLEX_RISK)][
    ["행정동","고립지수_종합","지수_경제적_불안정성","지수_사회활동","지수_사회적_관계","지수_고립형_생활"]
].copy().reset_index(drop=True)

# ── 경계 로드 ─────────────────────────────────────────────────────────────────
latest = adk.versions()[-1]
gdf_all = adk.get(latest, "emd", crs="EPSG:3857")
eunp = gdf_all[gdf_all["sggnm"] == "은평구"].copy().reset_index(drop=True)
eunp = eunp.merge(df[["행정동","고립지수_종합"]], left_on="emdnm", right_on="행정동", how="left")
eunp["is_risk"] = eunp["emdnm"].isin(COMPLEX_RISK)

# ── 좌표 범위 ─────────────────────────────────────────────────────────────────
from pyproj import Transformer
tf = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
def to_merc(lat, lon): return tf.transform(lon, lat)
x_min, y_min = to_merc(37.568, 126.876)
x_max, y_max = to_merc(37.648, 126.963)

# ── norm (복합취약형 6개 동 범위만 사용) ──────────────────────────────────────
norm_risk = Normalize(
    vmin=eunp.loc[eunp["is_risk"], "고립지수_종합"].min() * 0.92,
    vmax=eunp.loc[eunp["is_risk"], "고립지수_종합"].max()
)

# ── 레이블 오프셋 (동 외부로 인출) ───────────────────────────────────────────
dx = x_max - x_min
dy = y_max - y_min

LABEL_OFFSET_6 = {
    "불광2동": ( dx*0.18,  dy*0.028),
    "갈현1동": (-dx*0.17,  dy*0.020),
    "갈현2동": (-dx*0.18, -dy*0.008),
    "구산동":  (-dx*0.18, -dy*0.030),
    "역촌동":  ( dx*0.16,  dy*0.005),
    "응암3동": ( dx*0.16, -dy*0.048),
}

# ── 그리기 ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 13))
fig.patch.set_facecolor("#FFFFFF")
ax.set_facecolor("#F8FAFC")
ax.set_xlim(x_min, x_max)
ax.set_ylim(y_min, y_max)

# 배경 타일
try:
    ctx.add_basemap(ax, source=ctx.providers.CartoDB.PositronNoLabels, zoom=14, alpha=0.22)
except Exception:
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=14, alpha=0.10)

# 비복합취약형 동: 연한 청회색
eunp[~eunp["is_risk"]].plot(ax=ax, facecolor="#E8EDF2", edgecolor="#C8CDD6",
                             linewidth=0.5, zorder=2)

# 복합취약형 6개 동: 파스텔 choropleth
eunp[eunp["is_risk"]].plot(ax=ax, column="고립지수_종합", cmap=PASTEL_RISK_CMAP,
                            norm=norm_risk, alpha=0.92,
                            edgecolor="#C8956A", linewidth=1.4, zorder=3)

# 비복합취약형 동 이름 (작게, 연하게)
for _, row in eunp[~eunp["is_risk"]].iterrows():
    c = row.geometry.centroid
    ax.text(c.x, c.y, row["emdnm"],
            fontsize=6.0, ha="center", va="center", color="#B5BEC8",
            path_effects=[pe.withStroke(linewidth=1.0, foreground="white")], zorder=5)

# 복합취약형 6개 동: 외부 인출 레이블
for _, row in eunp[eunp["is_risk"]].iterrows():
    c = row.geometry.centroid
    dong = row["emdnm"]
    score = row["고립지수_종합"]
    ox, oy = LABEL_OFFSET_6.get(dong, (dx*0.15, dy*0.015))
    ha = "left" if ox > 0 else "right"
    ax.annotate(f"{dong}\n{score:.3f}",
                xy=(c.x, c.y), xytext=(c.x + ox, c.y + oy),
                ha=ha, va="center",
                fontsize=12.5, fontweight="bold", color="#3D1C0A",
                path_effects=[pe.withStroke(linewidth=2.8, foreground="white")],
                arrowprops=dict(arrowstyle="-", color="#C8956A", lw=0.9,
                               shrinkA=5, shrinkB=0),
                zorder=8)

# ── 컬러바 ────────────────────────────────────────────────────────────────────
sm = ScalarMappable(cmap=PASTEL_RISK_CMAP, norm=norm_risk)
sm.set_array([])
cbar_ax = fig.add_axes([0.58, 0.065, 0.30, 0.014])
cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
cbar.set_label("종합 고립지수", fontsize=8.5, color="#374151", labelpad=4)
cbar.ax.xaxis.set_label_position("top")
cbar.ax.tick_params(labelsize=8, colors="#374151")
cbar.outline.set_edgecolor("#D1D5DB")

# ── 범례 ──────────────────────────────────────────────────────────────────────
h_risk  = mpatches.Patch(facecolor="#EF9264", edgecolor="#C8956A", linewidth=1.2,
                          label=f"복합취약형 6개 동 (경제↑ + 사회단절↑)")
h_other = mpatches.Patch(facecolor="#E8EDF2", edgecolor="#C8CDD6",
                          label="기타 행정동")
ax.legend(handles=[h_risk, h_other], loc="lower left", bbox_to_anchor=(0.01, 0.01),
          fontsize=9.0, frameon=True, framealpha=0.96,
          edgecolor="#D1D5DB", facecolor="white", borderpad=0.9)

# ── 제목 ──────────────────────────────────────────────────────────────────────
ax.set_title("복합취약형 6개 동 확정  |  서울시 은평구",
             fontsize=15, fontweight="bold", color="#111827", pad=12, loc="left")
ax.text(0.0, 1.011,
        "Jenks 경제축 임계값(≈0.41) 적용  ·  대조동·신사1동·신사2동 경제축 미달 제외  ·  경계: admdongkor",
        transform=ax.transAxes, fontsize=8.0, color="#6B7280")
ax.set_axis_off()

plt.tight_layout(pad=1.0)
out = str(BASE / "복지시설" / "slide3_복합취약6동_고립지수.png")
plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"저장 완료: {out}")
