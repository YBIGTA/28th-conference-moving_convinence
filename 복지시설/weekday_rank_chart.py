# -*- coding: utf-8 -*-
# 평일 요일별 행정동 생활인구 순위 — 히트맵 + 순위표

import pandas as pd
import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
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

WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일"]
COMPLEX_RISK = ["응암3동","불광2동","역촌동","갈현1동","갈현2동","구산동"]

# ── 데이터 로드 ───────────────────────────────────────────────────────────────
parts = []
for d in WEEKDAYS:
    df = pd.read_csv(find_csv("행정동", d, "절대인구"), dtype={"H_DNG_CD": str})
    df["요일"] = d
    parts.append(df)

wide = pd.concat(parts).pivot(index="dong_nm", columns="요일", values="MID_POP")[WEEKDAYS]
wide["평균"] = wide[WEEKDAYS].mean(axis=1)

# 복합취약형 + 전체 두 버전
risk_wide  = wide[wide.index.isin(COMPLEX_RISK)].sort_values("평균", ascending=False)
total_wide = wide.sort_values("평균", ascending=False)

# 요일별 순위 (전체 16동 기준)
rank_wide = total_wide[WEEKDAYS].rank(ascending=False, method="min").astype(int)

print("=== 평일 요일별 MID_POP 및 순위 (복합취약형 6개 동, 16동 내 순위) ===")
for dong in risk_wide.index:
    row = risk_wide.loc[dong]
    ranks = rank_wide.loc[dong]
    vals  = "  |  ".join([f"{d[:1]}: {row[d]:.0f}({ranks[d]}위)" for d in WEEKDAYS])
    print(f"  {dong:8s}  {vals}")

print()
print("=== 요일별 생활인구 1위 동 (전체 16동) ===")
for d in WEEKDAYS:
    top = total_wide[d].idxmax()
    print(f"  {d}: {top}  ({total_wide.loc[top, d]:.0f}명)")

print()
print("=== 요일별 생활인구 1위 동 (복합취약형 6개 동 내) ===")
for d in WEEKDAYS:
    top = risk_wide[d].idxmax()
    print(f"  {d}: {top}  ({risk_wide.loc[top, d]:.0f}명)")

# ════════════════════════════════════════════════════════════════════════════════
# 그래프 1: 히트맵 (복합취약형 6개 동 × 5요일, MID_POP)
# ════════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 2, figsize=(20, 6),
                         gridspec_kw={"width_ratios": [1.1, 1]})
fig.patch.set_facecolor("#FFFFFF")

# --- 히트맵 ---
ax = axes[0]
mat = risk_wide[WEEKDAYS].values
day_labels = ["월", "화", "수", "목", "금"]
dong_labels = list(risk_wide.index)

im = ax.imshow(mat, cmap="Blues", aspect="auto",
               vmin=mat.min() * 0.92, vmax=mat.max())

ax.set_xticks(range(len(WEEKDAYS)))
ax.set_xticklabels(day_labels, fontsize=13, fontweight="bold")
ax.set_yticks(range(len(dong_labels)))
ax.set_yticklabels(dong_labels, fontsize=12)
ax.tick_params(left=False, bottom=False)

# 셀 값 표시
for i, dong in enumerate(dong_labels):
    for j, d in enumerate(WEEKDAYS):
        val = risk_wide.loc[dong, d]
        is_peak = val == risk_wide.loc[dong, WEEKDAYS].max()
        color = "white" if val > mat.mean() else "#1E3A5F"
        txt = ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                      fontsize=10.5, color=color, fontweight="bold" if is_peak else "normal")
        if is_peak:
            txt.set_path_effects([pe.withStroke(linewidth=1.5, foreground="white"
                                                if color == "#1E3A5F" else "#1D4ED8")])

# 컬러바
cbar = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
cbar.set_label("MID_POP (명/행정동 평균)", fontsize=9, color="#374151")
cbar.ax.tick_params(labelsize=8, colors="#374151")

ax.set_title("복합취약형 동 × 평일 요일별 생활인구", fontsize=14,
             fontweight="bold", color="#111827", pad=12)
ax.text(0.5, -0.06, "굵은 숫자 = 해당 동의 주중 피크 요일",
        transform=ax.transAxes, ha="center", fontsize=9, color="#6B7280")

# --- 요일별 순위 막대 (복합취약형 내 순위) ---
ax2 = axes[1]
colors_map = {
    "월요일": "#3B82F6", "화요일": "#60A5FA",
    "수요일": "#93C5FD", "목요일": "#60A5FA", "금요일": "#3B82F6"
}

# 복합취약형 6개 동 내 요일별 순위
risk_rank = risk_wide[WEEKDAYS].rank(ascending=False, method="min").astype(int)

x = np.arange(len(WEEKDAYS))
width = 0.08
for i, dong in enumerate(dong_labels):
    offsets = np.linspace(-(len(dong_labels)-1)/2 * width,
                           (len(dong_labels)-1)/2 * width,
                           len(dong_labels))
    vals = [risk_wide.loc[dong, d] for d in WEEKDAYS]
    bars = ax2.bar(x + offsets[i], vals, width,
                   label=dong, alpha=0.85, zorder=2)

ax2.set_xticks(x)
ax2.set_xticklabels(["월", "화", "수", "목", "금"], fontsize=13, fontweight="bold")
ax2.set_ylabel("MID_POP (명)", fontsize=10, color="#374151")
ax2.yaxis.set_tick_params(labelsize=9)
ax2.set_ylim(risk_wide[WEEKDAYS].min().min() * 0.85,
             risk_wide[WEEKDAYS].max().max() * 1.08)
ax2.legend(fontsize=8.5, ncol=3, loc="upper right",
           framealpha=0.9, edgecolor="#D1D5DB")
ax2.set_facecolor("#FAFAFA")
ax2.grid(axis="y", color="#E5E7EB", linewidth=0.7, zorder=1)
ax2.spines[["top","right"]].set_visible(False)
ax2.set_title("복합취약형 동별 평일 생활인구 비교", fontsize=14,
              fontweight="bold", color="#111827", pad=12)
ax2.text(0.5, -0.06, "y축 하단 절사 — 동 간 상대 차이 강조",
         transform=ax2.transAxes, ha="center", fontsize=9, color="#6B7280")

fig.suptitle("평일 요일별 중장년 생활인구  |  복합취약형 6개 동  |  서울시 은평구",
             fontsize=16, fontweight="bold", color="#111827", y=1.02)

plt.tight_layout()
out = str(BASE / "복지시설" / "평일_요일별_순위.png")
plt.savefig(out, dpi=160, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"\n저장 완료: {out}")
