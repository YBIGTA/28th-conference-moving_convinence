"""
은평구 중장년(40~64세) 인구 순위 CSV 48개 생성 — 자체 완결 스크립트.

원본 LOCAL_PEOPLE parquet 12개월치 → 은평구 필터 → 시간 08~20 한정 →
지표(절대인구·비율) × {전체·시간대 4밴드·요일 7개} 조합으로 CSV 48개 산출.

  - 전체   : 4   = 2 단위(행정동/집계구) × 2 지표
  - 시간대 : 16  = 2 × 4 밴드(오전/점심/오후/저녁) × 2 지표
  - 요일   : 28  = 2 × 7 요일(월~일) × 2 지표

이 스크립트 한 개만 있으면 eunpyeong/data/ 폴더의 모든 CSV를 처음부터 만들 수 있다.

[폴더 구조]
  eunpyeong/
  ├── README.md
  ├── code/
  │   └── build_rankings.py    ← 이 파일
  └── data/
      ├── 행정동/
      │   ├── 시간대별/         ← 전체(2) + 4밴드(8) = 10개 CSV
      │   └── 요일별/           ← 7요일 × 2지표 = 14개 CSV
      └── 집계구/
          ├── 시간대별/         ← 전체(2) + 4밴드(8) = 10개 CSV
          └── 요일별/           ← 7요일 × 2지표 = 14개 CSV

[필요 데이터]
  LOCAL_PEOPLE_YYYYMM.parquet (12개) — 다음 위치 중 하나에 두면 자동 탐지:
    1) eunpyeong/LOCAL_PEOPLE/      (eunpyeong/ 폴더 안)
    2) seoul/db/LOCAL_PEOPLE/       (프로젝트 표준 위치)
    3) eunpyeong/../LOCAL_PEOPLE/   (eunpyeong/ 의 상위 폴더)

[필요 패키지]
  pandas, pyarrow

[실행]
  cd eunpyeong/code
  python build_rankings.py
"""
from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd

# === 경로 ==============================================================
# 이 스크립트는 eunpyeong/code/build_rankings.py 라고 가정한다.
# 출력은 한 단계 위(eunpyeong/), raw 데이터는 eunpyeong/ 또는 그 부모에서 탐색.
HERE = Path(__file__).resolve().parent          # eunpyeong/code/
EUNPYEONG = HERE.parent                          # eunpyeong/
PROJECT_ROOT = EUNPYEONG.parent                  # seoul/ 등 상위

RAW_CANDIDATES = [
    EUNPYEONG / "LOCAL_PEOPLE",
    PROJECT_ROOT / "db" / "LOCAL_PEOPLE",
    PROJECT_ROOT / "LOCAL_PEOPLE",
]
RAW_DIR = next((p for p in RAW_CANDIDATES if p.exists()), None)
if RAW_DIR is None:
    raise FileNotFoundError(
        "LOCAL_PEOPLE parquet 폴더를 찾을 수 없습니다. 다음 중 한 곳에 두세요:\n"
        + "\n".join(f"  - {p}" for p in RAW_CANDIDATES)
    )
OUT_DIR = EUNPYEONG / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)
print(f"[경로] raw  : {RAW_DIR}")
print(f"[경로] 출력 : {OUT_DIR}")


# === 상수 ==============================================================
# 은평구 8자리 KOSIS 행정동 코드 → 동명 (16개)
DONG_NAME_MAP: dict[str, str] = {
    "11380510": "녹번동", "11380520": "불광1동", "11380530": "불광2동",
    "11380551": "갈현1동", "11380552": "갈현2동", "11380560": "구산동",
    "11380570": "대조동", "11380580": "응암1동", "11380590": "응암2동",
    "11380600": "응암3동", "11380625": "역촌동", "11380631": "신사1동",
    "11380632": "신사2동", "11380640": "증산동", "11380650": "수색동",
    "11380690": "진관동",
}

MID_COLS = ["M40", "M45", "M50", "M55", "M60",
            "F40", "F45", "F50", "F55", "F60"]   # 40~64세 10개 (M65/F65 제외)
NUM_COLS = ["SPOP"] + MID_COLS
KEEP_COLS = ["YMD", "TIME", "H_DNG_CD", "OA_CD"] + NUM_COLS

TIMES_08_20 = [f"{h:02d}" for h in range(8, 20)]   # 08~19, 12시간
BAND_DEF: dict[str, set[str]] = {
    "오전": {"08", "09", "10"},
    "점심": {"11", "12", "13"},
    "오후": {"14", "15", "16"},
    "저녁": {"17", "18", "19"},
}
METRIC_LABEL = {"MID_POP": "절대인구", "MID_RATIO": "비율"}
DOW_KOR = ["월", "화", "수", "목", "금", "토", "일"]   # 0=월 ... 6=일


def time_to_band(t: str) -> str | None:
    for band, hours in BAND_DEF.items():
        if t in hours:
            return band
    return None


# === 1) raw parquet 12개월 로드 + 은평구 필터 + 수치 변환 ==============
def load_eunpyeong() -> pd.DataFrame:
    files = sorted(glob.glob(str(RAW_DIR / "LOCAL_PEOPLE_*.parquet")))
    if not files:
        raise FileNotFoundError(f"parquet 파일이 없습니다: {RAW_DIR}")
    parts = []
    for f in files:
        df = pd.read_parquet(f, columns=KEEP_COLS)
        df = df[df["H_DNG_CD"].str.startswith("1138")].copy()  # 은평구
        df = df[df["TIME"].isin(TIMES_08_20)].copy()           # 08~20시
        for c in NUM_COLS:
            df[c] = pd.to_numeric(df[c], errors="coerce")      # '*' → NaN
        parts.append(df)
        print(f"  loaded {Path(f).name}: {len(df):,}행")
    out = pd.concat(parts, ignore_index=True)
    out["MID_POP"] = out[MID_COLS].sum(axis=1, skipna=True, min_count=1)
    out["MID_RATIO"] = out["MID_POP"] / out["SPOP"]
    out.loc[out["SPOP"].isna(), "MID_RATIO"] = pd.NA
    out["BAND"] = out["TIME"].map(time_to_band)
    out["DOW"] = out["YMD"].dt.dayofweek.map(lambda x: DOW_KOR[x])
    out["dong_nm"] = out["H_DNG_CD"].map(DONG_NAME_MAP).fillna(out["H_DNG_CD"])
    return out


print("\n[1] raw parquet 12개월 로드 (은평구 + 08~20시)")
df = load_eunpyeong()
print(f"  → 총 {len(df):,}행, 행정동 {df['H_DNG_CD'].nunique()}개, "
      f"집계구 {df['OA_CD'].nunique()}개")


# === 2) 단일 지표 + 순위로 저장하는 헬퍼 ===============================
def save_one(df_avg: pd.DataFrame, key_cols: list[str], metric: str,
             out_name: str, sub_dir: str) -> None:
    """sub_dir(예: '행정동/시간대별') 안에 단일 지표 + 순위 CSV 저장."""
    # 지표 NaN인 행은 순위 매길 수 없으므로 제외 (요일 분리 시 일부 OA 발생)
    out = df_avg[key_cols + [metric]].dropna(subset=[metric]).copy()
    out["rank"] = out[metric].rank(ascending=False, method="min").astype(int)
    out = out.sort_values("rank")

    target_dir = OUT_DIR / sub_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(target_dir / out_name, index=False, encoding="utf-8-sig")
    print(f"  → {sub_dir}/{out_name} ({len(out):,}행)")


# === 3) 전체 순위 (4 CSV) ==============================================
print("\n[2] 전체 순위 (08~20시 평균)")
dong_total = (
    df.groupby(["H_DNG_CD", "dong_nm"], as_index=False)
      .agg(MID_POP=("MID_POP", "mean"),
           MID_RATIO=("MID_RATIO", "mean"))
)
oa_total = (
    df.groupby(["OA_CD", "H_DNG_CD", "dong_nm"], as_index=False)
      .agg(MID_POP=("MID_POP", "mean"),
           MID_RATIO=("MID_RATIO", "mean"))
)
save_one(dong_total, ["H_DNG_CD", "dong_nm"], "MID_POP",   "행정동_전체_절대인구.csv", "행정동/시간대별")
save_one(dong_total, ["H_DNG_CD", "dong_nm"], "MID_RATIO", "행정동_전체_비율.csv",     "행정동/시간대별")
save_one(oa_total,   ["OA_CD", "H_DNG_CD", "dong_nm"], "MID_POP",   "집계구_전체_절대인구.csv", "집계구/시간대별")
save_one(oa_total,   ["OA_CD", "H_DNG_CD", "dong_nm"], "MID_RATIO", "집계구_전체_비율.csv",     "집계구/시간대별")


# === 4) 시간대별 순위 (16 CSV) =========================================
print("\n[3] 시간대별 순위 (4밴드)")
dong_band = (
    df.groupby(["H_DNG_CD", "dong_nm", "BAND"], as_index=False)
      .agg(MID_POP=("MID_POP", "mean"),
           MID_RATIO=("MID_RATIO", "mean"))
)
oa_band = (
    df.groupby(["OA_CD", "H_DNG_CD", "dong_nm", "BAND"], as_index=False)
      .agg(MID_POP=("MID_POP", "mean"),
           MID_RATIO=("MID_RATIO", "mean"))
)
for band in BAND_DEF.keys():
    sub_d = dong_band[dong_band["BAND"] == band].drop(columns=["BAND"])
    sub_o = oa_band[oa_band["BAND"] == band].drop(columns=["BAND"])
    for metric, label in METRIC_LABEL.items():
        save_one(sub_d.copy(), ["H_DNG_CD", "dong_nm"], metric,
                 f"행정동_{band}_{label}.csv", "행정동/시간대별")
        save_one(sub_o.copy(), ["OA_CD", "H_DNG_CD", "dong_nm"], metric,
                 f"집계구_{band}_{label}.csv", "집계구/시간대별")


# === 5) 요일별 순위 (28 CSV) — 시간대 미분리, 08~20시 평균 ============
print("\n[4] 요일별 순위 (월~일, 시간대 미분리)")
dong_dow = (
    df.groupby(["H_DNG_CD", "dong_nm", "DOW"], as_index=False)
      .agg(MID_POP=("MID_POP", "mean"),
           MID_RATIO=("MID_RATIO", "mean"))
)
oa_dow = (
    df.groupby(["OA_CD", "H_DNG_CD", "dong_nm", "DOW"], as_index=False)
      .agg(MID_POP=("MID_POP", "mean"),
           MID_RATIO=("MID_RATIO", "mean"))
)
for dow in DOW_KOR:
    sub_d = dong_dow[dong_dow["DOW"] == dow].drop(columns=["DOW"])
    sub_o = oa_dow[oa_dow["DOW"] == dow].drop(columns=["DOW"])
    for metric, label in METRIC_LABEL.items():
        save_one(sub_d.copy(), ["H_DNG_CD", "dong_nm"], metric,
                 f"행정동_{dow}요일_{label}.csv", "행정동/요일별")
        save_one(sub_o.copy(), ["OA_CD", "H_DNG_CD", "dong_nm"], metric,
                 f"집계구_{dow}요일_{label}.csv", "집계구/요일별")

print("\n[완료] eunpyeong/data/ 안의 4개 하위 폴더에 CSV 48개 생성됨")
print("       (행정동/시간대별 10 + 행정동/요일별 14 + 집계구/시간대별 10 + 집계구/요일별 14)")
