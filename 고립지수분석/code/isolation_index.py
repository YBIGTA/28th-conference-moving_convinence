# isolation_index.py
# 서울시 중장년(40-64세) 사회적 고립지수 산출
# 방법론: small-23-03 청년 고립지수 논문 기반 + 중장년 수정
#   ① 인구 가중 집계 → ② min-max 정규화 → ③ 요인분석 가중치 → ④ 가중 선형 합산
# 추가: 관심집단수 비율 병합 (외부 타당성 검증), 12개월 시계열, 연령집단 비교

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import FactorAnalysis
from scipy.stats import zscore
import glob, re, os, warnings
warnings.filterwarnings('ignore')

DATA_DIR   = r'D:\서울시 데이터'
OUTPUT_DIR = r'D:\서울시 데이터\outputs'

MID_AGE   = [40, 45, 50, 55, 60]   # 중장년 40~64세 (메인)
YOUTH_AGE = [20, 25, 30, 35]        # 청년 20~39세  (비교용)
ELDER_AGE = [65, 70, 75]            # 노년 65+      (비교용)

# ── 변수 정의 ──────────────────────────────────────────────────
# (내부 컬럼명, 원본 컬럼명)
COUNT_VARS = [   # 인원수 → 비율로 변환 (count / 총인구)
    ('출근_미추정_비율',   '출근 소요시간 미추정 인구수'),   # 비경제활동 proxy (청년 대비 추가)
    ('근무_미추정_비율',   '근무시간 미추정 인구수'),         # 동일
    ('카카오톡_비사용률',  '카카오톡 비사용 인구수'),
]
WTMEAN_VARS = [  # 인구 가중 평균
    ('소액결제_금액',      '소액결재 사용금액 평균'),
    ('소액결제_횟수',      '소액결재 사용횟수 평균'),
    ('요금_연체_비율',     '최근 3개월 내 요금 연체 비율'),
    ('주간_상주지_변경',   '주간상주지 변경횟수 평균'),
    ('평일_이동횟수',      '평일 총 이동 횟수'),
    ('휴일_이동횟수',      '휴일 총 이동 횟수 평균'),
    ('지하철_이동일수',    '지하철이동일수 합계'),
    ('평일_집체류시간',    '집 추정 위치 평일 총 체류시간'),
    ('휴일_집체류시간',    '집 추정 위치 휴일 총 체류시간'),
    ('동영상_사용일수',    '동영상/방송 서비스 사용일수'),
    ('통화대상자수',       '평균 통화대상자 수'),
    ('문자대상자수',       '평균 문자대상자 수'),
    ('통화량',             '평균 통화량'),
]

# 4개 차원 구성: (변수명, 고립방향) True=높을수록 고립, False=낮을수록 고립
DIMS = {
    '경제적_불안정성': [        # 수정 모형: 요금 연체율 단독
        # 원본 논문의 출근·근무 미추정 변수는 청년(20~39세) 대상 proxy.
        # 중장년 적용 시 자가용 출퇴근·고소득 자영업자도 동일하게 미추정으로 분류되어
        # construct validity 역전 (강남 1위). → 직접 지표인 연체율만 사용.
        ('요금_연체_비율',    True),
    ],
    '사회활동': [               # 논문과 동일 (근무시간 제거 → 미추정으로 대체)
        ('주간_상주지_변경',  False),
        ('평일_이동횟수',     False),
        ('휴일_이동횟수',     False),
        ('지하철_이동일수',   False),
    ],
    '고립형_생활': [            # 논문 대비: 게임 제거 (중장년 부적합), 동영상 유지
        ('평일_집체류시간',   True),
        ('휴일_집체류시간',   True),
        ('동영상_사용일수',   True),
    ],
    '사회적_관계': [            # 논문과 동일
        ('통화대상자수',      False),
        ('문자대상자수',      False),
        ('카카오톡_비사용률', True),
        ('통화량',            False),
    ],
}


# ════════════════════════════════════════════════════════════════
# 1. 파일 탐색
# ════════════════════════════════════════════════════════════════
def find_files():
    telecom, group = {}, {}
    for f in glob.glob(os.path.join(DATA_DIR, '2025.*월_29개 통신정보.xlsx')):
        if '~$' not in f:
            m = re.search(r'\.(\d+)월_', os.path.basename(f))
            if m:
                telecom[int(m.group(1))] = f
    for f in glob.glob(os.path.join(DATA_DIR, '2025.*월_10개 관심집단*.xlsx')):
        if '~$' not in f:
            m = re.search(r'\.(\d+)월_', os.path.basename(f))
            if m:
                group[int(m.group(1))] = f
    return dict(sorted(telecom.items())), dict(sorted(group.items()))


# ════════════════════════════════════════════════════════════════
# 2. 집계 함수
# ════════════════════════════════════════════════════════════════
def aggregate_telecom(df, age_group):
    """연령 필터 → 행정동별 인구 가중 집계 (논문 p.18 방식)"""
    df = df[df['연령대'].isin(age_group)].copy()
    pop = '총인구수'

    pop_sum  = df.groupby('행정동코드')[pop].sum()
    dong_info = df.groupby('행정동코드').first()[['자치구', '행정동']]

    result = (
        pd.DataFrame({'총인구수': pop_sum})
        .join(dong_info)
        .reset_index()
    )
    result = result[result['총인구수'] > 0].set_index('행정동코드')

    for new_col, src in COUNT_VARS:
        cnt = df.groupby('행정동코드')[src].sum()
        result[new_col] = (cnt / result['총인구수']).clip(0, 1)

    for new_col, src in WTMEAN_VARS:
        df['_w'] = df[src] * df[pop]
        wsum = df.groupby('행정동코드')['_w'].sum()
        result[new_col] = wsum / result['총인구수']

    return result.reset_index()


def aggregate_group(df, age_group):
    """관심집단수: 연령 필터 → 행정동별 비율 집계"""
    df = df[df['연령대'].isin(age_group)].copy()
    pop = '총인구'

    pop_sum = df.groupby('행정동코드')[pop].sum()
    result  = pd.DataFrame({'총인구': pop_sum}).reset_index()
    result  = result[result['총인구'] > 0].set_index('행정동코드')

    group_map = {
        '복합고립_비율':          '외출-커뮤니케이션이 모두 적은 집단(전체)',
        '커뮤니케이션고립_비율':  '커뮤니케이션이 적은 집단',
        '평일외출고립_비율':      '평일 외출이 적은 집단',
        '휴일외출고립_비율':      '휴일 외출이 적은 집단',
    }
    for new_col, src in group_map.items():
        cnt = df.groupby('행정동코드')[src].sum()
        result[new_col] = (cnt / result['총인구']).clip(0, 1)

    return result.reset_index()


# ════════════════════════════════════════════════════════════════
# 3. 요인분석 가중치 (논문 p.18: 공통성 / 고유치 합계)
# ════════════════════════════════════════════════════════════════
def fa_weights(X: np.ndarray) -> np.ndarray:
    """
    FA는 상관행렬 기준으로 작동해야 하므로 min-max 스케일된 X를 z-score 재표준화 후 적용.
    communality = 1 - noise_variance_ (z-score 기준에서만 유효한 공식).
    """
    n_vars = X.shape[1]
    if n_vars < 2:
        return np.ones(n_vars) / n_vars
    try:
        Xz = np.nan_to_num(zscore(X, axis=0), nan=0.0)
        fa = FactorAnalysis(n_components=1, random_state=42, max_iter=1000)
        fa.fit(Xz)
        communalities = np.clip(1 - fa.noise_variance_, 0.01, 1.0)
        return communalities / communalities.sum()
    except Exception:
        return np.ones(n_vars) / n_vars


# ════════════════════════════════════════════════════════════════
# 4. 고립지수 산출
# ════════════════════════════════════════════════════════════════
def compute_isolation_index(df_telecom, df_group=None):
    df = df_telecom.copy().reset_index(drop=True)
    result = df[['행정동코드', '자치구', '행정동', '총인구수']].copy()

    all_vars, all_dirs = [], []

    for dim_name, var_dir_list in DIMS.items():
        available = [(v, d) for v, d in var_dir_list if v in df.columns]
        if not available:
            continue

        vnames = [v for v, _ in available]
        vdirs  = [d for _, d in available]

        X = df[vnames].fillna(df[vnames].median())

        scaler   = MinMaxScaler()
        X_scaled = pd.DataFrame(
            scaler.fit_transform(X), columns=vnames, index=df.index
        )
        for v, d in zip(vnames, vdirs):
            if not d:
                X_scaled[v] = 1 - X_scaled[v]

        w = fa_weights(X_scaled.values)
        result[f'지수_{dim_name}'] = (X_scaled.values * w).sum(axis=1)

        all_vars.extend(vnames)
        all_dirs.extend(vdirs)

    # 종합 지수: 전체 변수 요인분석 (논문 p.18 종합 모형)
    X_all = df[all_vars].fillna(df[all_vars].median())
    scaler_all   = MinMaxScaler()
    X_all_scaled = pd.DataFrame(
        scaler_all.fit_transform(X_all), columns=all_vars, index=df.index
    )
    for v, d in zip(all_vars, all_dirs):
        if not d:
            X_all_scaled[v] = 1 - X_all_scaled[v]

    w_all = fa_weights(X_all_scaled.values)
    result['고립지수_종합'] = (X_all_scaled.values * w_all).sum(axis=1)

    # 관심집단수 병합
    if df_group is not None:
        group_cols = ['행정동코드', '복합고립_비율', '커뮤니케이션고립_비율',
                      '평일외출고립_비율', '휴일외출고립_비율']
        result = result.merge(df_group[group_cols], on='행정동코드', how='left')

    return result



# ════════════════════════════════════════════════════════════════
# 6. 전체 파이프라인
# ════════════════════════════════════════════════════════════════
def run_pipeline():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    telecom_files, group_files = find_files()
    print(f"통신정보 {len(telecom_files)}개월, 관심집단수 {len(group_files)}개월 발견\n")

    # ── A. 월별 고립지수 ──
    monthly = []
    for month in sorted(telecom_files.keys()):
        print(f"  {month:2d}월 처리 중...", end=' ')
        df_t   = pd.read_excel(telecom_files[month])
        df_agg = aggregate_telecom(df_t, MID_AGE)

        df_g = None
        if month in group_files:
            df_g_raw = pd.read_excel(group_files[month])
            df_g     = aggregate_group(df_g_raw, MID_AGE)

        idx = compute_isolation_index(df_agg, df_g)
        idx['월'] = month
        monthly.append(idx)
        print(f"{len(idx)}개 행정동")

    df_monthly = pd.concat(monthly, ignore_index=True)
    df_monthly.to_csv(
        os.path.join(OUTPUT_DIR, '중장년_월별_고립지수.csv'),
        index=False, encoding='utf-8-sig'
    )

    # ── B. 연간 요약 ──
    score_cols = [c for c in df_monthly.columns if c.startswith('지수_') or c == '고립지수_종합']
    ratio_cols = [c for c in df_monthly.columns if '비율' in c]

    agg_dict = {'총인구수': 'mean'}
    for c in score_cols + ratio_cols:
        agg_dict[c] = 'mean'

    df_annual = (
        df_monthly
        .groupby(['행정동코드', '자치구', '행정동'])
        .agg(agg_dict)
        .reset_index()
    )

    # 12개월 OLS 기울기 → 악화 추세 파악
    def ols_slope(x):
        return np.polyfit(range(len(x)), x.values, 1)[0] if len(x) >= 3 else np.nan

    df_trend = (
        df_monthly.groupby('행정동코드')['고립지수_종합']
        .apply(ols_slope)
        .rename('고립지수_추세')
        .reset_index()
    )
    df_annual = df_annual.merge(df_trend, on='행정동코드')
    df_annual.to_csv(
        os.path.join(OUTPUT_DIR, '중장년_연간_고립지수.csv'),
        index=False, encoding='utf-8-sig'
    )

    # ── 결과 요약 출력 ──
    print('\n' + '='*60)
    print('중장년 연간 고립지수 상위 15 행정동')
    print('='*60)
    top15 = df_annual.nlargest(15, '고립지수_종합')[
        ['자치구', '행정동', '고립지수_종합', '고립지수_추세',
         '커뮤니케이션고립_비율', '평일외출고립_비율']
    ]
    print(top15.round(4).to_string(index=False))

    print('\n' + '='*60)
    print('악화 추세 상위 10 행정동 (12개월 기울기 큰 순)')
    print('='*60)
    top_trend = df_annual.nlargest(10, '고립지수_추세')[
        ['자치구', '행정동', '고립지수_종합', '고립지수_추세']
    ]
    print(top_trend.round(4).to_string(index=False))

    # 관심집단수와 상관관계 (외부 타당성)
    corr_cols = ['고립지수_종합', '커뮤니케이션고립_비율', '평일외출고립_비율', '휴일외출고립_비율']
    corr_cols = [c for c in corr_cols if c in df_annual.columns]
    if len(corr_cols) > 1:
        print('\n' + '='*60)
        print('고립지수 × 관심집단 비율 상관관계 (외부 타당성)')
        print('='*60)
        print(df_annual[corr_cols].corr().round(3).to_string())

    print(f'\n저장 완료 → {OUTPUT_DIR}')
    return df_monthly, df_annual


if __name__ == '__main__':
    df_monthly, df_annual = run_pipeline()
