# visualize.py
# 중장년 고립지수 시각화
#   ① 연간 고립지수 상위 15 (차원별 누적 바)
#   ② 월별 추이 (서울 평균 + 상위 5개 동)
#   ③ 악화 추세 상위 10
#   ④ 자치구별 평균 히트맵
#   ⑤ 행정동 choropleth 지도 (folium)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import folium
import requests, json, os, warnings
warnings.filterwarnings('ignore')

DATA_DIR   = r'D:\서울시 데이터'
OUTPUT_DIR = r'D:\서울시 데이터\outputs'

# ── 한글 폰트 ──────────────────────────────────────────────────
def set_korean_font():
    candidates = ['Malgun Gothic', 'NanumGothic', 'AppleGothic', 'Noto Sans CJK KR']
    for name in candidates:
        if any(name.lower() in f.name.lower() for f in fm.fontManager.ttflist):
            plt.rcParams['font.family'] = name
            plt.rcParams['axes.unicode_minus'] = False
            return name
    return None

font_name = set_korean_font()

# ── 데이터 로드 ────────────────────────────────────────────────
df_a = pd.read_csv(os.path.join(OUTPUT_DIR, '중장년_연간_고립지수.csv'))
df_m = pd.read_csv(os.path.join(OUTPUT_DIR, '중장년_월별_고립지수.csv'))

# 소인구 행정동 제외 (500명 미만 → 명동 등 노이즈)
df_a = df_a[df_a['총인구수'] >= 500].copy()

DIM_COLS   = ['지수_경제적_불안정성', '지수_사회활동', '지수_고립형_생활', '지수_사회적_관계']
DIM_LABELS = ['경제적 불안정성', '사회활동', '고립형 생활', '사회적 관계']
DIM_COLORS = ['#E07B54', '#5B9BD5', '#70AD47', '#9E6FC0']

MONTH_KR = {1:'1월',2:'2월',3:'3월',4:'4월',5:'5월',6:'6월',
            7:'7월',8:'8월',9:'9월',10:'10월',11:'11월',12:'12월'}


# ════════════════��═══════════════════════════════════════��═══════
# ① 연간 고립지수 상위 15 — 차원별 누적 수평 바
# ══════════════════════════════════��═════════════════════════════
def plot_top15(df):
    top = df.nlargest(15, '고립지수_종합').iloc[::-1].copy()
    top['label'] = top['자치구'].str[:2] + ' ' + top['행정동']

    fig, ax = plt.subplots(figsize=(10, 7))
    lefts = np.zeros(len(top))
    for col, label, color in zip(DIM_COLS, DIM_LABELS, DIM_COLORS):
        vals = top[col].values
        ax.barh(top['label'], vals, left=lefts, color=color, label=label, height=0.65)
        lefts += vals

    ax.set_xlabel('고립지수 (누적)', fontsize=11)
    ax.set_title('중장년(40-64세) 연간 사회적 고립지수 상위 15 행정동', fontsize=13, fontweight='bold', pad=12)
    ax.legend(loc='lower right', fontsize=9)
    ax.set_xlim(0, lefts.max() * 1.08)
    ax.tick_params(axis='y', labelsize=9)
    ax.spines[['top', 'right']].set_visible(False)

    # 종합 점수 텍스트
    for i, (_, row) in enumerate(top.iterrows()):
        ax.text(lefts[i] + 0.005, i, f'{row["고립지수_종합"]:.3f}', va='center', fontsize=8, color='#333')

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '01_고립지수_상위15.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'저장: {path}')


# ════════════════════════════════════════════════════════════════
# ② 월별 추이 — 서울 전체 평균 + 상위 5개 동
# ════════════════════════════════════════════════════════════════
def plot_monthly_trend(df_m, df_a):
    top5 = df_a.nlargest(5, '고립지수_종합')['행정동코드'].tolist()
    df_m_filt = df_m[df_m['총인구수'] >= 500].copy()

    monthly_avg = df_m_filt.groupby('월')['고립지수_종합'].mean()
    months = sorted(monthly_avg.index)
    x = range(len(months))

    fig, ax = plt.subplots(figsize=(11, 5))

    # 상위 5개 동 개별 선 (연한 색)
    colors_top = ['#AECDE3', '#F4B183', '#A9D18E', '#C5A5D4', '#F2C76A']
    for code, color in zip(top5, colors_top):
        sub = df_m_filt[df_m_filt['행정동코드'] == code].set_index('월')['고립지수_종합']
        name = df_a[df_a['행정동코드'] == code]['행정동'].values[0]
        ys = [sub.get(m, np.nan) for m in months]
        ax.plot(x, ys, color=color, linewidth=1.5, linestyle='--', alpha=0.8, label=name)

    # 서울 전체 평균 (굵은 선)
    ax.plot(x, [monthly_avg[m] for m in months],
            color='#C00000', linewidth=2.5, label='서울 전체 평균', zorder=5)

    ax.set_xticks(list(x))
    ax.set_xticklabels([MONTH_KR[m] for m in months], fontsize=10)
    ax.set_ylabel('고립지수', fontsize=11)
    ax.set_title('중장년 사회적 고립지수 월별 추이 (2025)', fontsize=13, fontweight='bold', pad=12)
    ax.legend(fontsize=8, loc='upper left', framealpha=0.85)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', linestyle='--', alpha=0.4)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '02_월별_추이.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'저장: {path}')


# ════════════════════════════════════════════════════════════════
# ③ 악화 추세 상위 10 — 기울기 바 (버블 크기 = 고립지수 수준)
# ════════════════════════════════════════���═══════════════════════
def plot_trend_top10(df):
    top = df[df['총인구수'] >= 500].nlargest(10, '고립지수_추세').iloc[::-1].copy()
    top['label'] = top['자치구'].str[:2] + ' ' + top['행정동']

    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ['#C00000' if v > df['고립지수_추세'].quantile(0.9) else '#E07B54'
              for v in top['고립지수_추세']]
    bars = ax.barh(top['label'], top['고립지수_추세'], color=colors, height=0.6)

    ax.set_xlabel('고립지수 월별 증가 기울기 (OLS)', fontsize=11)
    ax.set_title('고립 악화 추세 상위 10 행정동 (2025년 1-12월)', fontsize=13, fontweight='bold', pad=12)
    ax.spines[['top', 'right']].set_visible(False)

    for bar, (_, row) in zip(bars, top.iterrows()):
        ax.text(bar.get_width() + 0.0002, bar.get_y() + bar.get_height()/2,
                f'현재 {row["고립지수_종합"]:.3f}', va='center', fontsize=8, color='#555')

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '03_악화추세_상위10.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'저장: {path}')


# ════════════════════════════════════════════��═══════════════════
# ④ 자치구별 평균 고립지수 — 히트맵 스타일 바
# ═════════════════════════════════════��══════════════════════════
def plot_by_gu(df):
    gu = (
        df[df['총인구수'] >= 500]
        .groupby('자치구')[DIM_COLS + ['고립지수_종합']]
        .mean()
        .sort_values('고립지수_종합', ascending=True)
    )

    fig, ax = plt.subplots(figsize=(10, 8))
    lefts = np.zeros(len(gu))
    for col, label, color in zip(DIM_COLS, DIM_LABELS, DIM_COLORS):
        ax.barh(gu.index, gu[col], left=lefts, color=color, label=label, height=0.7)
        lefts += gu[col].values

    ax.set_xlabel('고립지수 (누적)', fontsize=11)
    ax.set_title('자치구별 중장년 평균 고립지수', fontsize=13, fontweight='bold', pad=12)
    ax.legend(loc='lower right', fontsize=9)
    ax.spines[['top', 'right']].set_visible(False)
    ax.tick_params(axis='y', labelsize=9)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '04_자치구별_고립지수.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'저장: {path}')


# ════════════════════════════════════════════════════════════════
# ⑤ Folium choropleth 지도 — 종합 + 4개 차원 (총 5개)
# ════════════════════════════════════════════════════════════════
GEOJSON_URL  = 'https://raw.githubusercontent.com/vuski/admdongkor/master/ver20230701/HangJeongDong_ver20230701.geojson'
GEOJSON_PATH = os.path.join(DATA_DIR, 'seoul_dong.geojson')

MAP_TARGETS = [
    ('고립지수_종합',        'YlOrRd', '종합 고립지수',       '05_지도_종합.html'),
    ('지수_경제적_불안정성', 'OrRd',   '경제적 불안정성 지수', '05_지도_경제.html'),
    ('지수_사회활동',        'PuBu',   '사회활동 지수',        '05_지도_사회활동.html'),
    ('지수_고립형_생활',     'YlOrBr', '고립형 생활 지수',     '05_지도_고립생활.html'),
    ('지수_사회적_관계',     'RdPu',   '사회적 관계 지수',     '05_지도_사회관계.html'),
]

def get_geojson():
    if os.path.exists(GEOJSON_PATH):
        with open(GEOJSON_PATH, encoding='utf-8') as f:
            return json.load(f)
    print('  GeoJSON 다운로드 중...')
    try:
        r = requests.get(GEOJSON_URL, timeout=30)
        r.raise_for_status()
        data = r.json()
        data['features'] = [
            ft for ft in data['features']
            if ft['properties'].get('sidonm') == '서울특별시'
        ]
        with open(GEOJSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        return data
    except Exception as e:
        print(f'  GeoJSON 다운로드 실패: {e}')
        return None

def _make_single_map(geo, df_map, score_col, color_scheme, legend_name, code_key):
    for ft in geo['features']:
        ft['properties']['_code'] = str(ft['properties'][code_key])[:8]

    tooltip_data = {row['_code']: row for _, row in df_map.iterrows()}
    for ft in geo['features']:
        code = ft['properties']['_code']
        if code in tooltip_data:
            row = tooltip_data[code]
            ft['properties']['점수'] = round(row[score_col], 3)
            ft['properties']['순위'] = int(row['_rank'])
            ft['properties']['동명'] = row['자치구'] + ' ' + row['행정동']

    m = folium.Map(location=[37.5665, 126.9780], zoom_start=11, tiles='CartoDB positron')
    folium.Choropleth(
        geo_data=geo,
        data=df_map,
        columns=['_code', score_col],
        key_on='feature.properties._code',
        fill_color=color_scheme,
        fill_opacity=0.75,
        line_opacity=0.25,
        legend_name=f'중장년 {legend_name} (2025년 연평균)',
        nan_fill_color='#eeeeee',
    ).add_to(m)
    folium.GeoJson(
        geo,
        style_function=lambda x: {'fillOpacity': 0, 'weight': 0},
        tooltip=folium.GeoJsonTooltip(
            fields=['동명', '점수', '순위'],
            aliases=['행정동', '지수값', '서울 순위'],
            localize=True,
        ),
    ).add_to(m)
    return m

def plot_maps(df):
    geo = get_geojson()
    if geo is None:
        print('  지도 스킵 (GeoJSON 없음)')
        return

    code_key = next(
        (k for k in ['adm_cd', 'emd_cd', 'ADM_DR_CD', 'HDONG_CD', 'adm_cd2']
         if k in geo['features'][0]['properties']),
        None
    )
    if not code_key:
        print('  코드 컬럼 없음')
        return

    df_map = df[df['총인구수'] >= 500].copy()
    df_map['행정동코드'] = df_map['행정동코드'].astype(str)
    df_map['_code'] = df_map['행정동코드'].str[:8]

    for score_col, color, legend, fname in MAP_TARGETS:
        if score_col not in df_map.columns:
            print(f'  {score_col} 없음, 스킵')
            continue
        df_map['_rank'] = df_map[score_col].rank(ascending=False).astype(int)
        m = _make_single_map(geo, df_map, score_col, color, legend, code_key)
        path = os.path.join(OUTPUT_DIR, fname)
        m.save(path)
        print(f'  저장: {path}')


# ════════════════════════════════════════════════════════════════
# 실행
# ════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f'한글 폰트: {font_name}\n')

    print('① 상위 15 바 차트')
    plot_top15(df_a)

    print('② 월별 추이')
    plot_monthly_trend(df_m, df_a)

    print('③ 악화 추세')
    plot_trend_top10(df_a)

    print('④ 자치구별')
    plot_by_gu(df_a)

    print('⑤ 지도 (5개)')
    plot_maps(df_a)

    print('\n완료')
