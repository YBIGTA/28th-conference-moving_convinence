# quadrant_analysis.py
# 2×2 고립 유형 분류
#   Y축 (심각도): 사회적 연결 결핍 = (사회활동 + 사회관계) / 2  → 중앙값 기준
#   X축 (개입방향): 경제적 불안정성 (요금연체비율)              → Jenks natural breaks 기준
#
# 경제 축에 Jenks를 쓰는 이유:
#   요금연체비율은 단일 변수로 오른쪽으로 치우친 분포(왜도 0.65)를 보인다.
#   중앙값 적용 시 낮은 연체율 동(0.37)이 기계적으로 경제불안정에 포함되는 문제.
#   Jenks natural breaks(군집 내 분산 최소화)로 자연 경계(~0.41)를 탐색하여 적용.
#
# 사회 축에 중앙값을 쓰는 이유:
#   두 지수의 합성값(평균)으로 분포가 대칭에 가까워(왜도 -0.55) 중앙값이 적합.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.font_manager as fm
import matplotlib.patheffects as pe
import matplotlib.colors as mcolors
import folium
import json, os, warnings
from math import pi

warnings.filterwarnings('ignore')

DATA_DIR   = r'D:\서울시 데이터'
OUTPUT_DIR = r'D:\서울시 데이터\outputs'

# ── 한글 폰트 ────────────────────────────────────────────────────
def set_korean_font():
    for name in ['Malgun Gothic', 'NanumGothic', 'AppleGothic']:
        if any(name.lower() in f.name.lower() for f in fm.fontManager.ttflist):
            plt.rcParams['font.family'] = name
            plt.rcParams['axes.unicode_minus'] = False
            return
set_korean_font()

# ── 데이터 로드 ──────────────────────────────────────────────────
df = pd.read_csv(os.path.join(OUTPUT_DIR, '중장년_연간_고립지수.csv'))
df = df[df['총인구수'] >= 500].copy().reset_index(drop=True)

df['축_경제'] = df['지수_경제적_불안정성']
df['축_사회'] = (df['지수_사회활동'] + df['지수_사회적_관계']) / 2

# ── Jenks natural breaks (k=2): 군집 내 분산 최소화 단일 컷 ─────
def jenks_k2(data):
    s = np.sort(data)
    best_cut, best_score = None, np.inf
    for i in range(1, len(s)):
        lo, hi = s[:i], s[i:]
        score = lo.var() * len(lo) + hi.var() * len(hi)
        if score < best_score:
            best_score = score
            best_cut = (s[i - 1] + s[i]) / 2
    return best_cut

# ── 분류 기준값 산출 ─────────────────────────────────────────────
threshold_경제 = jenks_k2(df['축_경제'].values)   # Jenks
threshold_사회 = df['축_사회'].median()            # 중앙값

df['hi_경제'] = df['축_경제'] >= threshold_경제
df['hi_사회'] = df['축_사회'] >= threshold_사회

def classify(row):
    if     row['hi_경제'] and     row['hi_사회']: return '복합취약형'
    if not row['hi_경제'] and     row['hi_사회']: return '사회단절형'
    if     row['hi_경제'] and not row['hi_사회']: return '경제취약형'
    return '비교적안정형'

df['유형'] = df.apply(classify, axis=1)

TYPE_ORDER  = ['복합취약형', '경제취약형', '사회단절형', '비교적안정형']
TYPE_COLORS = {'복합취약형': '#C00000', '경제취약형': '#E07B54',
               '사회단절형': '#5B9BD5', '비교적안정형': '#70AD47'}
TYPE_DESC = {
    '복합취약형':   '사회적 고립 심각 (1순위 개입)\n경제 불안정까지 겹침 → 소득·일자리 + 관계 회복 복합 프로그램',
    '사회단절형':   '사회적 고립 심각 (1순위 개입)\n경제는 상대적 안정 → 커뮤니티·관계 맺기 프로그램 집중',
    '경제취약형':   '사회적 고립 낮음 (예방적 접근)\n경제 불안정 있음 → 취·창업 연계로 고립 진입 사전 차단',
    '비교적안정형': '사회적 고립 낮음 (예방적 접근)\n경제도 안정 → 정기 모니터링, 커뮤니티 유지',
}
DIM_COLS   = ['지수_경제적_불안정성', '지수_사회활동', '지수_고립형_생활', '지수_사회적_관계']
DIM_LABELS = ['경제적\n불안정성', '사회활동', '고립형\n생활', '사회적\n관계']


# ════════════════════════════════════════════════════════════════
# ① 2×2 산점도 (사분면 배경 + 기준선)
# ════════════════════════════════════════════════════════════════
def plot_scatter():
    fig, ax = plt.subplots(figsize=(9, 8))

    # ── 사분면 배경색 ──
    x_lo = df['축_경제'].min() - 0.03;  x_hi = df['축_경제'].max() + 0.03
    y_lo = df['축_사회'].min() - 0.03;  y_hi = df['축_사회'].max() + 0.03

    quad_bg = [
        # (x0, x1, y0, y1, 유형)
        (threshold_경제, x_hi, threshold_사회, y_hi, '복합취약형'),
        (x_lo, threshold_경제, threshold_사회, y_hi, '사회단절형'),
        (threshold_경제, x_hi, y_lo, threshold_사회, '경제취약형'),
        (x_lo, threshold_경제, y_lo, threshold_사회, '비교적안정형'),
    ]
    for x0, x1, y0, y1, typ in quad_bg:
        ax.fill_between([x0, x1], y0, y1,
                        color=TYPE_COLORS[typ], alpha=0.08, zorder=0)

    # ── 기준선 ──
    ax.axvline(threshold_경제, color='#888', linewidth=1.2,
               linestyle='--', zorder=1,
               label=f'경제 기준 {threshold_경제:.3f} (Jenks)')
    ax.axhline(threshold_사회, color='#555', linewidth=1.2,
               linestyle=':', zorder=1,
               label=f'사회 기준 {threshold_사회:.3f} (중앙값)')

    # ── 산점도 ──
    for typ in TYPE_ORDER:
        sub = df[df['유형'] == typ]
        ax.scatter(sub['축_경제'], sub['축_사회'],
                   c=TYPE_COLORS[typ], alpha=0.70, s=45,
                   label=f'{typ} ({len(sub)}개)', zorder=3)

    # ── 사분면 레이블 ──
    quad_labels = [
        (threshold_경제 + (x_hi - threshold_경제) * 0.5,
         threshold_사회 + (y_hi - threshold_사회) * 0.55, '복합취약형'),
        (x_lo + (threshold_경제 - x_lo) * 0.5,
         threshold_사회 + (y_hi - threshold_사회) * 0.55, '사회단절형'),
        (threshold_경제 + (x_hi - threshold_경제) * 0.5,
         y_lo + (threshold_사회 - y_lo) * 0.45, '경제취약형'),
        (x_lo + (threshold_경제 - x_lo) * 0.5,
         y_lo + (threshold_사회 - y_lo) * 0.45, '비교적안정형'),
    ]
    for lx, ly, typ in quad_labels:
        ax.text(lx, ly, typ, ha='center', va='center',
                fontsize=9, color=TYPE_COLORS[typ], fontweight='bold',
                alpha=0.5, zorder=2)

    # ── 상위 10 동 이름 ──
    top10 = df.nlargest(10, '고립지수_종합')
    for _, row in top10.iterrows():
        ax.annotate(row['행정동'],
                    xy=(row['축_경제'], row['축_사회']),
                    xytext=(4, 4), textcoords='offset points',
                    fontsize=7, color='#333',
                    path_effects=[pe.withStroke(linewidth=2, foreground='white')])

    ax.set_xlabel('경제적 불안정성 지수 (요금 연체 비율)\n'
                  '← 개입 방향 차별화 기준  |  기준: Jenks natural breaks',
                  fontsize=10, color='#555')
    ax.set_ylabel('사회적 연결 결핍 지수 (사회활동 + 사회관계 평균)\n'
                  '← 고립 심각도 결정 기준  |  기준: 중앙값  (Cohen d=2.36)',
                  fontsize=10, color='#C00000')
    ax.set_title('서울시 중장년 행정동 고립 유형 분류 (2025년 연평균)\n'
                 '사회 축: 중앙값  |  경제 축: Jenks natural breaks',
                 fontsize=12, fontweight='bold', pad=14)
    ax.yaxis.label.set_color('#C00000')
    ax.legend(fontsize=9, loc='upper left', framealpha=0.9)
    ax.spines[['top', 'right']].set_visible(False)

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '07_사분면_산점도.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'저장: {path}')


# ════════════════════════════════════════════════════════════════
# ② 유형별 레이더 차트 (4개 패널)
# ════════════════════════════════════════════════════════════════
def plot_radar():
    N = len(DIM_LABELS)
    angles = [pi * 2 * i / N for i in range(N)] + [0]

    fig, axes = plt.subplots(2, 2, figsize=(10, 9),
                              subplot_kw=dict(polar=True))
    axes_flat = [axes[0,0], axes[0,1], axes[1,0], axes[1,1]]

    vmax = df[DIM_COLS].values.max() * 1.05

    for ax, typ in zip(axes_flat, TYPE_ORDER):
        sub   = df[df['유형'] == typ]
        means = sub[DIM_COLS].mean().values
        color = TYPE_COLORS[typ]

        avg_all  = df[DIM_COLS].mean().values
        vals_avg = list(avg_all) + [avg_all[0]]
        ax.fill(angles, vals_avg, color='#cccccc', alpha=0.35)
        ax.plot(angles, vals_avg, color='#999', linewidth=1, linestyle=':')

        vals = list(means) + [means[0]]
        ax.plot(angles, vals, color=color, linewidth=2.2)
        ax.fill(angles, vals, color=color, alpha=0.28)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(DIM_LABELS, fontsize=9)
        ax.set_ylim(0, vmax)
        ax.set_yticks([])
        ax.set_title(f'{typ}\n({len(sub)}개 동)',
                     fontsize=11, fontweight='bold', pad=14, color=color)

        for angle, val in zip(angles[:-1], means):
            ax.annotate(f'{val:.3f}', xy=(angle, val),
                        xytext=(0, 6), textcoords='offset points',
                        fontsize=8, ha='center', color=color, fontweight='bold')

    fig.text(0.5, -0.01,
             '회색: 서울 전체 평균 기준  |  색상 영역: 해당 유형 평균',
             ha='center', fontsize=9, color='#666')
    fig.suptitle('고립 유형별 4개 차원 프로파일', fontsize=14,
                 fontweight='bold', y=1.01)
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '07_사분면_레이더차트.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'저장: {path}')


# ════════════════════════════════════════════════════════════════
# ③ 유형별 요약 바 차트
# ════════════════════════════════════════════════════════════════
def plot_summary():
    summary = (
        df.groupby('유형')
        .agg(동수=('행정동', 'count'),
             중장년인구=('총인구수', 'sum'),
             평균고립지수=('고립지수_종합', 'mean'))
        .reindex(TYPE_ORDER)
    )

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    colors = [TYPE_COLORS[t] for t in TYPE_ORDER]

    axes[0].barh(TYPE_ORDER, summary['동수'], color=colors, height=0.6)
    for i, v in enumerate(summary['동수']):
        axes[0].text(v + 1, i, f'{v}개', va='center', fontsize=10)
    axes[0].set_xlim(0, summary['동수'].max() * 1.2)
    axes[0].set_xlabel('행정동 수', fontsize=11)
    axes[0].set_title('유형별 행정동 수', fontsize=12, fontweight='bold')
    axes[0].spines[['top', 'right']].set_visible(False)

    pop_k = summary['중장년인구'] / 10000
    axes[1].barh(TYPE_ORDER, pop_k, color=colors, height=0.6)
    for i, v in enumerate(pop_k):
        axes[1].text(v + 0.3, i, f'{v:.1f}만', va='center', fontsize=10)
    axes[1].set_xlim(0, pop_k.max() * 1.2)
    axes[1].set_xlabel('중장년 인구 (만 명)', fontsize=11)
    axes[1].set_title('유형별 중장년 인구', fontsize=12, fontweight='bold')
    axes[1].spines[['top', 'right']].set_visible(False)

    axes[2].barh(TYPE_ORDER, summary['평균고립지수'], color=colors, height=0.6)
    for i, v in enumerate(summary['평균고립지수']):
        axes[2].text(v + 0.003, i, f'{v:.3f}', va='center', fontsize=10)
    axes[2].set_xlim(0, summary['평균고립지수'].max() * 1.2)
    axes[2].set_xlabel('평균 종합 고립지수', fontsize=11)
    axes[2].set_title('유형별 평균 고립지수', fontsize=12, fontweight='bold')
    axes[2].spines[['top', 'right']].set_visible(False)

    plt.suptitle('서울시 중장년 고립 유형별 현황', fontsize=14,
                 fontweight='bold', y=1.02)
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '07_사분면_요약.png')
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'저장: {path}')


# ════════════════════════════════════════════════════════════════
# ④ Folium 지도
# ════════════════════════════════════════════════════════════════
def plot_map():
    geojson_path = os.path.join(DATA_DIR, 'seoul_dong.geojson')
    if not os.path.exists(geojson_path):
        print('  GeoJSON 없음, 스킵')
        return

    with open(geojson_path, encoding='utf-8') as f:
        geo = json.load(f)

    code_key = next(
        (k for k in ['adm_cd', 'emd_cd', 'ADM_DR_CD', 'HDONG_CD', 'adm_cd2']
         if k in geo['features'][0]['properties']), None
    )

    df['_code'] = df['행정동코드'].astype(str).str[:8]
    lookup = {row['_code']: row for _, row in df.iterrows()}

    for ft in geo['features']:
        code = str(ft['properties'][code_key])[:8]
        if code in lookup:
            row = lookup[code]
            ft['properties']['유형']    = row['유형']
            ft['properties']['고립지수'] = round(row['고립지수_종합'], 4)
            ft['properties']['행정동명'] = row['자치구'] + ' ' + row['행정동']
            ft['properties']['_color']  = TYPE_COLORS[row['유형']]
        else:
            ft['properties']['유형']    = '데이터없음'
            ft['properties']['고립지수'] = None
            ft['properties']['행정동명'] = ft['properties'].get('adm_nm', '')
            ft['properties']['_color']  = '#eeeeee'

    m = folium.Map(location=[37.5665, 126.9780], zoom_start=11,
                   tiles='CartoDB positron')

    folium.GeoJson(
        geo,
        style_function=lambda x: {
            'fillColor':   x['properties']['_color'],
            'fillOpacity': 0.75,
            'color':       '#555',
            'weight':      0.4,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['행정동명', '유형', '고립지수'],
            aliases=['행정동', '고립 유형', '종합 고립지수'],
            localize=True,
        ),
    ).add_to(m)

    legend_html = f'''
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
                background:white;padding:14px 18px;border-radius:10px;
                border:1px solid #ccc;font-size:13px;line-height:1.8;">
      <b>중장년 고립 유형</b><br>
      <span style="font-size:11px;color:#888;">
        사회 기준 {threshold_사회:.3f} (중앙값)<br>
        경제 기준 {threshold_경제:.3f} (Jenks)
      </span><br>
    '''
    for typ in TYPE_ORDER:
        c = TYPE_COLORS[typ]
        legend_html += (f'<span style="background:{c};display:inline-block;'
                        f'width:14px;height:14px;margin-right:7px;'
                        f'border-radius:3px;vertical-align:middle;"></span>'
                        f'{typ}<br>')
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))

    path = os.path.join(OUTPUT_DIR, '07_사분면_지도.html')
    m.save(path)
    print(f'저장: {path}')


# ════════════════════════════════════════════════════════════════
# ⑤ 콘솔 요약 출력
# ════════════════════════════════════════════════════════════════
def print_summary():
    n_hi_e = df['hi_경제'].sum()
    n_hi_s = df['hi_사회'].sum()

    print('\n' + '=' * 65)
    print('  서울시 중장년 고립 유형 분류 결과 (2025년 연평균)')
    print('=' * 65)
    print('  분류 체계:')
    print(f'    Y축 사회적 연결 결핍  기준={threshold_사회:.4f} (중앙값)  → {n_hi_s}개 동({n_hi_s/len(df)*100:.1f}%)')
    print(f'    X축 경제적 불안정성  기준={threshold_경제:.4f} (Jenks)   → {n_hi_e}개 동({n_hi_e/len(df)*100:.1f}%)')

    for typ in TYPE_ORDER:
        sub = df[df['유형'] == typ]
        print(f'\n[{typ}]  {len(sub)}개 동  /  '
              f'중장년 {sub["총인구수"].sum():,.0f}명  /  '
              f'평균 고립지수 {sub["고립지수_종합"].mean():.4f}')
        print(f'  → {TYPE_DESC[typ]}')
        top5 = sub.nlargest(5, '고립지수_종합')[['자치구', '행정동', '고립지수_종합']]
        for _, r in top5.iterrows():
            print(f'     {r["자치구"]} {r["행정동"]:8s}  {r["고립지수_종합"]:.4f}')

    acc_path = os.path.join(OUTPUT_DIR, '중장년_접근성_분석.csv')
    if os.path.exists(acc_path):
        df_acc = pd.read_csv(acc_path)
        df_acc['_code'] = df_acc['행정동코드'].astype(str).str[:8]
        df['_code'] = df['행정동코드'].astype(str).str[:8]
        df2 = df.merge(df_acc[['_code', 'covered_1km']], on='_code', how='left')
        df2['covered_1km'] = df2['covered_1km'].fillna(False).astype(bool)

        print('\n' + '=' * 65)
        print('  유형 × 접근성 교차 (사각지대 내 중장년)')
        print('=' * 65)
        for typ in TYPE_ORDER:
            sub = df2[(df2['유형'] == typ) & ~df2['covered_1km']]
            print(f'  {typ:<10s}: {len(sub):3d}개 동  /  '
                  f'{sub["총인구수"].sum():>9,.0f}명 사각지대')


# ════════════════════════════════════════════════════════════════
# 실행
# ════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f'분류 기준 — 사회: {threshold_사회:.4f} (중앙값) / 경제: {threshold_경제:.4f} (Jenks)')

    print('① 2×2 산점도')
    plot_scatter()

    print('② 레이더 차트')
    plot_radar()

    print('③ 요약 바 차트')
    plot_summary()

    print('④ Folium 지도')
    plot_map()

    print_summary()

    out_path = os.path.join(OUTPUT_DIR, '중장년_고립유형_사분면.csv')
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f'\n저장: {out_path}')
    print('\n완료')
