#%% Cell 0 — Setup & 데이터 로드
# 12개월(2025-03~2026-02) analysis_local_people 파생 parquet 로드.
# 시간 필터(08~20시)가 가능한 by_time과, 요일 차원이 있는 by_dow를 분리해 준비한다.
# - by_time : (TIME × H_DNG_CD) × 12개월 → 08~19시만 남김 (08~20 = [08,20))
# - by_dow  : (DOW  × H_DNG_CD) × 12개월 → 08~22시가 이미 합산된 상태 (시간 필터 불가)
import glob
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

pd.set_option("display.max_rows", 60)
pd.set_option("display.float_format", lambda x: f"{x:,.1f}")

# macOS 한글 폰트
mpl.rcParams["font.family"] = "AppleGothic"
mpl.rcParams["axes.unicode_minus"] = False

# === 환경 설정 (팀원 공유용) =========================================
# 이 스크립트(analysis.py)가 seoul/ 폴더 안에 있다고 가정하고 자동으로 데이터 위치를 찾는다.
# 다른 위치에 두고 싶다면 아래 PROJECT_ROOT 줄만 본인 환경의 seoul 폴더 절대경로로 바꿔주면 된다.
#   예) PROJECT_ROOT = Path("/Users/이름/어딘가/seoul")
try:
    PROJECT_ROOT = Path(__file__).resolve().parent
except NameError:  # 순수 Jupyter 노트북 등 __file__ 미정의 환경
    PROJECT_ROOT = Path.cwd()
BASE = PROJECT_ROOT / "db" / "analysis_local_people"
assert BASE.exists(), (
    f"데이터 폴더를 찾을 수 없습니다: {BASE}\n"
    f"analysis.py를 seoul/ 폴더에 두거나, 위 PROJECT_ROOT를 본인의 seoul 폴더 절대경로로 직접 지정하세요."
)
# ====================================================================
M_COLS = ["M40", "M45", "M50", "M55", "M60", "M65"]
F_COLS = ["F40", "F45", "F50", "F55", "F60", "F65"]
AGE_COLS = M_COLS + F_COLS
TIMES_08_20 = [f"{h:02d}" for h in range(8, 20)]  # ['08'..'19'], 12시간

DOW_ORDER = ["월", "화", "수", "목", "금", "토", "일"]
WEEKDAY = {"월", "화", "수", "목", "금"}


def _load_all(subdir: str) -> pd.DataFrame:
    files = sorted(glob.glob(str(BASE / subdir / "*.parquet")))
    parts = []
    for f in files:
        df = pd.read_parquet(f)
        df["YM"] = Path(f).stem.split("_")[2]  # LOCAL_PEOPLE_202503_by_time → '202503'
        parts.append(df)
    return pd.concat(parts, ignore_index=True)


bt = _load_all("by_time")
bt = bt[bt["TIME"].isin(TIMES_08_20)].copy()
bt["MF_4065"] = bt[AGE_COLS].sum(axis=1)
bt["M_4065"] = bt[M_COLS].sum(axis=1)
bt["F_4065"] = bt[F_COLS].sum(axis=1)

bd = _load_all("by_dow")
bd["MF_4065"] = bd[AGE_COLS].sum(axis=1)

# 12개월 동안 각 요일이 며칠 발생했는지 카운트 (요일별/평일·주말 일평균 정규화에 필요)
months = sorted(bt["YM"].unique())
dow_counts = {d: 0 for d in DOW_ORDER}
for ym in months:
    y, m = int(ym[:4]), int(ym[4:])
    start = pd.Timestamp(year=y, month=m, day=1)
    end = start + pd.offsets.MonthEnd(0)
    for d in pd.date_range(start, end, freq="D"):
        dow_counts[DOW_ORDER[d.weekday()]] += 1

print(f"by_time (08~20 한정): {len(bt):,} rows / 행정동 {bt['H_DNG_CD'].nunique()}개 / 월 {len(months)}개")
print(f"by_dow (08~22 포함) : {len(bd):,} rows")
print(f"12개월 요일 발생일수: {dow_counts}")


#%% Cell 1 — [요청1] 행정동 전체 top 10 (M+F 40~65 합산, 12개월 누적, 08~20시)
# 인사이트: 12개월 통산으로 40~65세 생활인구 체류량(인-시간)이 가장 큰 행정동.
total_by_dong = (
    bt.groupby("H_DNG_CD")["MF_4065"].sum().sort_values(ascending=False)
)
print("[1] 12개월 누적 (08~20시) M+F 40~65 합산 top 10 — 단위: 인-시간")
print(total_by_dong.head(10).to_frame("MF_4065_sum"))

# 시각화: top 10 가로 막대 (상위가 위로 오도록 역순)
fig, ax = plt.subplots(figsize=(9, 5))
total_by_dong.head(10).iloc[::-1].plot.barh(ax=ax, color="steelblue")
ax.set_title("[1] 행정동 top 10 (M+F 40~65, 12개월 누적, 08~20시)")
ax.set_xlabel("인-시간 합")
ax.set_ylabel("행정동 코드")
plt.tight_layout()
plt.show()


#%% Cell 2 — [요청2] top 10 행정동 월별 추이 (시계열)
# 인사이트: 1번에서 뽑힌 top 10 행정동의 월간 변동. 계절성/이상치/추세를 본다.
top10_dongs = total_by_dong.head(10).index.tolist()
monthly = (
    bt.groupby(["YM", "H_DNG_CD"])["MF_4065"].sum().reset_index()
)
trend = (
    monthly[monthly["H_DNG_CD"].isin(top10_dongs)]
    .pivot(index="YM", columns="H_DNG_CD", values="MF_4065")
    .sort_index()
)
trend = trend[top10_dongs]  # 1위→10위 순서로 컬럼 정렬
print("[2] top 10 행정동 월별 추이 (인-시간) — 행: 월, 열: 행정동(1위→10위)")
print(trend)
print("\n[참고] 월별 변동률(전월 대비 %): 마지막 행 = 직전월 → 당월 변화")
print((trend.pct_change() * 100).round(1))

# 시각화: top 10 행정동 12개월 시계열
fig, ax = plt.subplots(figsize=(11, 6))
trend.plot(ax=ax, marker="o")
ax.set_title("[2] top 10 행정동 월별 추이 (08~20시 합)")
ax.set_xlabel("YM")
ax.set_ylabel("인-시간")
ax.legend(title="H_DNG_CD", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


#%% Cell 3 — [요청3] 요일별 top 10 (일평균 정규화)
# 인사이트: 요일마다 어떤 동에 40~65세가 가장 몰리나. 누적합 그대로 비교하면
# 12개월 안에서 요일 발생 횟수(52~53회 vs 다른 요일)가 달라 왜곡되므로
# "해당 요일 발생일수"로 나눠 일평균(인-시간/일)으로 정규화한다.
# 주의: by_dow는 08~22시가 모두 합산된 값(시간 필터 불가) — 21·22시 ~13% 노이즈 포함.
dow_dong = (
    bd.groupby(["DOW", "H_DNG_CD"])["MF_4065"].sum().reset_index()
)
dow_dong["MF_per_day"] = dow_dong.apply(
    lambda r: r["MF_4065"] / dow_counts[r["DOW"]], axis=1
)

print("[3] 요일별 top 10 (일평균 인-시간) — by_dow 기준 (08~22시 포함)")
for dow in DOW_ORDER:
    sub = (
        dow_dong[dow_dong["DOW"] == dow]
        .sort_values("MF_per_day", ascending=False)
        .head(10)
    )
    print(f"\n=== {dow}요일 (12개월 중 {dow_counts[dow]}일) ===")
    print(sub[["H_DNG_CD", "MF_per_day"]].to_string(index=False))

# 시각화: 전체 top 5 행정동의 요일별 일평균 패턴 (주말 dip 보기 용이)
top5 = total_by_dong.head(5).index.tolist()
viz3 = (
    dow_dong[dow_dong["H_DNG_CD"].isin(top5)]
    .pivot(index="DOW", columns="H_DNG_CD", values="MF_per_day")
    .reindex(DOW_ORDER)[top5]
)
fig, ax = plt.subplots(figsize=(10, 5))
viz3.plot(ax=ax, marker="o")
ax.set_title("[3] top 5 행정동의 요일별 일평균 (인-시간/일)")
ax.set_xlabel("요일")
ax.set_ylabel("일평균 인-시간")
ax.legend(title="H_DNG_CD")
plt.tight_layout()
plt.show()


#%% Cell 4 — [요청4] 시간대(오전/점심/오후/저녁)별 top 10
# 인사이트: 시간대마다 40~65세가 어디에 집중되는지. 직장·점심상권·퇴근 동선이 드러난다.
# 시간대 정의(좌측포함, 우측미포함): 오전 [08,11), 점심 [11,14), 오후 [14,17), 저녁 [17,20)
def time_band(t: str) -> str:
    h = int(t)
    if 8 <= h < 11:
        return "오전(08-11)"
    if 11 <= h < 14:
        return "점심(11-14)"
    if 14 <= h < 17:
        return "오후(14-17)"
    if 17 <= h < 20:
        return "저녁(17-20)"
    return "기타"


bt["TIME_BAND"] = bt["TIME"].map(time_band)
band_dong = (
    bt.groupby(["TIME_BAND", "H_DNG_CD"])["MF_4065"].sum().reset_index()
)
BAND_ORDER = ["오전(08-11)", "점심(11-14)", "오후(14-17)", "저녁(17-20)"]

print("[4] 시간대(3시간)별 top 10 (12개월 누적, 인-시간)")
for band in BAND_ORDER:
    sub = (
        band_dong[band_dong["TIME_BAND"] == band]
        .sort_values("MF_4065", ascending=False)
        .head(10)
    )
    print(f"\n=== {band} ===")
    print(sub[["H_DNG_CD", "MF_4065"]].to_string(index=False))

# 시각화: 전체 top 5 행정동의 시간대 패턴 (점심 피크/저녁 dip 등)
viz4 = (
    band_dong[band_dong["H_DNG_CD"].isin(top5)]
    .pivot(index="TIME_BAND", columns="H_DNG_CD", values="MF_4065")
    .reindex(BAND_ORDER)[top5]
)
fig, ax = plt.subplots(figsize=(10, 5))
viz4.plot(ax=ax, marker="o")
ax.set_title("[4] top 5 행정동의 시간대별 인-시간 합")
ax.set_xlabel("시간대")
ax.set_ylabel("인-시간")
ax.legend(title="H_DNG_CD")
plt.tight_layout()
plt.show()


#%% Cell 5 — [요청5] 평일 vs 주말 top 10 (일평균 정규화)
# 인사이트: 평일에만 강한 동(직장/업무 상권) vs 주말에만 강한 동(여가·관광·주거) 구분.
# 평일/주말 각각 12개월 누적 일수로 나눠 일평균으로 비교한다. (by_dow 기준, 08~22시 포함)
bd["DAY_TYPE"] = bd["DOW"].map(lambda d: "평일" if d in WEEKDAY else "주말")
weekday_days = sum(v for d, v in dow_counts.items() if d in WEEKDAY)
weekend_days = sum(v for d, v in dow_counts.items() if d not in WEEKDAY)
day_count_map = {"평일": weekday_days, "주말": weekend_days}
print(f"[참고] 12개월: 평일 {weekday_days}일 / 주말 {weekend_days}일")

dt_dong = (
    bd.groupby(["DAY_TYPE", "H_DNG_CD"])["MF_4065"].sum().reset_index()
)
dt_dong["MF_per_day"] = dt_dong.apply(
    lambda r: r["MF_4065"] / day_count_map[r["DAY_TYPE"]], axis=1
)

print("\n[5] 평일/주말 top 10 (일평균 인-시간)")
for dt in ["평일", "주말"]:
    sub = (
        dt_dong[dt_dong["DAY_TYPE"] == dt]
        .sort_values("MF_per_day", ascending=False)
        .head(10)
    )
    print(f"\n=== {dt} ===")
    print(sub[["H_DNG_CD", "MF_per_day"]].to_string(index=False))

# 평일·주말 top 10 비교
wd_top = set(dt_dong[dt_dong["DAY_TYPE"] == "평일"].nlargest(10, "MF_per_day")["H_DNG_CD"])
we_top = set(dt_dong[dt_dong["DAY_TYPE"] == "주말"].nlargest(10, "MF_per_day")["H_DNG_CD"])
print(f"\n공통 top 10  : {sorted(wd_top & we_top)}")
print(f"평일 only    : {sorted(wd_top - we_top)}")
print(f"주말 only    : {sorted(we_top - wd_top)}")

# 시각화: 평일 top 5 ∪ 주말 top 5 (대개 7~10개)에 대해 평일/주말 일평균 막대 비교
union5 = list(
    set(dt_dong[dt_dong["DAY_TYPE"] == "평일"].nlargest(5, "MF_per_day")["H_DNG_CD"])
    | set(dt_dong[dt_dong["DAY_TYPE"] == "주말"].nlargest(5, "MF_per_day")["H_DNG_CD"])
)
viz5 = (
    dt_dong[dt_dong["H_DNG_CD"].isin(union5)]
    .pivot(index="H_DNG_CD", columns="DAY_TYPE", values="MF_per_day")
    .sort_values("평일", ascending=False)
)
fig, ax = plt.subplots(figsize=(11, 5))
viz5[["평일", "주말"]].plot.bar(ax=ax, color=["#3b7ddd", "#dd9b3b"])
ax.set_title("[5] 평일 vs 주말 일평균 비교 (평일·주말 top 5 union)")
ax.set_xlabel("행정동 코드")
ax.set_ylabel("일평균 인-시간")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


#%% Cell 6 — [요청6] 성별 분리 top 10 (12개월 전체 합산, 08~20시)
# 인사이트: 40~65세 남성/여성이 각각 어디에 몰리는지. 직장 밀집(남↑) vs 생활/여가 밀집(여↑) 단서.
m_dong = bt.groupby("H_DNG_CD")["M_4065"].sum().sort_values(ascending=False)
f_dong = bt.groupby("H_DNG_CD")["F_4065"].sum().sort_values(ascending=False)

print("[6] 성별 top 10 (12개월 누적, 인-시간)")
print("\n=== 남성 40~65 top 10 ===")
print(m_dong.head(10).to_frame("M_4065_sum"))
print("\n=== 여성 40~65 top 10 ===")
print(f_dong.head(10).to_frame("F_4065_sum"))

# 성별 비교 + 성비(M/F) 가장 치우친 동
m_top10 = set(m_dong.head(10).index)
f_top10 = set(f_dong.head(10).index)
print(f"\n남녀 공통 top 10: {sorted(m_top10 & f_top10)}")
print(f"남성에만 top 10 : {sorted(m_top10 - f_top10)}")
print(f"여성에만 top 10 : {sorted(f_top10 - m_top10)}")

mf_ratio = (m_dong / f_dong).rename("M/F_ratio").to_frame()
mf_ratio = mf_ratio.join(m_dong.rename("M")).join(f_dong.rename("F"))
print("\n[참고] 남성 편향 top 10 (M/F 비율 큰 동)")
print(mf_ratio.sort_values("M/F_ratio", ascending=False).head(10))
print("\n[참고] 여성 편향 top 10 (M/F 비율 작은 동)")
print(mf_ratio.sort_values("M/F_ratio", ascending=True).head(10))

# 시각화: 남성 top 10 ∪ 여성 top 10 행정동에 대해 M/F 막대 비교
union6 = list(set(m_dong.head(10).index) | set(f_dong.head(10).index))
viz6 = pd.DataFrame({"M": m_dong.reindex(union6), "F": f_dong.reindex(union6)})
viz6 = viz6.sort_values("M", ascending=False)
fig, ax = plt.subplots(figsize=(11, 5))
viz6[["M", "F"]].plot.bar(ax=ax, color=["#3b7ddd", "#dd5b7d"])
ax.set_title("[6] 성별 top 10 비교 (M·F top 10 union, 12개월 누적)")
ax.set_xlabel("행정동 코드")
ax.set_ylabel("인-시간 합")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


#%% Cell 7 — [요청7] 시간대별 순위 변동 — 어떤 동이 시간대에 따라 순위가 크게 바뀌나
# 인사이트: 항상 top인 거대 동(예: 강남)은 변동이 작다. 반면 특정 시간대만 튀는 동
# (예: 점심 상권만 강한 동, 저녁 거주지로만 회귀하는 동)은 순위 폭이 크다.
# 4개 시간대 각각의 행정동 순위를 만들어 max-min 변동폭을 본다.
rank_pivot = (
    band_dong.pivot(index="H_DNG_CD", columns="TIME_BAND", values="MF_4065")
    .fillna(0)
)
rank_pivot = rank_pivot[BAND_ORDER]
ranks = rank_pivot.rank(ascending=False, method="min").astype(int)
ranks["RANK_RANGE"] = ranks[BAND_ORDER].max(axis=1) - ranks[BAND_ORDER].min(axis=1)
ranks["RANK_BEST"] = ranks[BAND_ORDER].min(axis=1)
ranks["RANK_WORST"] = ranks[BAND_ORDER].max(axis=1)

# "한 번이라도 top 10에 든 적 있는 동"으로 한정해 의미있는 변동만 추림
ever_top10 = ranks[(ranks[BAND_ORDER] <= 10).any(axis=1)].copy()
ever_top10 = ever_top10.sort_values("RANK_RANGE", ascending=False)

print("[7-a] 시간대별 순위 변동이 큰 행정동 (한번이라도 top 10 진입, 변동폭 큰 순) — top 15")
print(ever_top10[BAND_ORDER + ["RANK_BEST", "RANK_WORST", "RANK_RANGE"]].head(15))

print("\n[7-b] 항상 top 10에 머무는 '안정적 거대 동' (4개 시간대 모두 top 10)")
always_top10 = ranks[(ranks[BAND_ORDER] <= 10).all(axis=1)]
print(always_top10[BAND_ORDER + ["RANK_RANGE"]])

print("\n[7-c] 시간대별 top 10 명단 (코드)")
for band in BAND_ORDER:
    top = (
        rank_pivot[band].sort_values(ascending=False).head(10).index.tolist()
    )
    print(f"  {band}: {top}")

# 시각화: 변동폭 큰 top 10 행정동의 4개 시간대 순위 추적 (y축 뒤집어 1위가 위)
viz7 = ever_top10.head(10)[BAND_ORDER]
fig, ax = plt.subplots(figsize=(11, 6))
for dong in viz7.index:
    ax.plot(BAND_ORDER, viz7.loc[dong].values, marker="o", label=dong)
ax.invert_yaxis()
ax.axhline(y=10, color="gray", linestyle="--", alpha=0.5)
ax.text(0, 10.5, "top 10 경계", color="gray", fontsize=8)
ax.set_title("[7] 시간대별 순위 변동 — 변동폭 큰 top 10 행정동")
ax.set_xlabel("시간대")
ax.set_ylabel("순위 (낮을수록 상위)")
ax.legend(title="H_DNG_CD", bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
plt.tight_layout()
plt.show()

# %%
