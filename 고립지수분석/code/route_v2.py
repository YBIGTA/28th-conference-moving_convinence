# route_v2.py
# 이동형 마음편의점 노선 v2
#   컨셉: 기존 19개소 거점 → 반경 내 복합취약형 동을 1일 1개씩 순환 방문
#   타겟: 복합취약형 + 1km 사각지대
#   할당: 각 동을 가장 가까운 기존 거점에 배정
#   스케줄: 고립지수 높은 순서대로 방문 우선순위

import pandas as pd
import numpy as np
import json, os
from math import radians, sin, cos, sqrt, atan2
import folium
import geopandas as gpd

DATA_DIR   = r'D:\서울시 데이터'
OUTPUT_DIR = r'D:\서울시 데이터\outputs'

MAX_ASSIGN_KM = 8.0    # 거점에서 이 거리 이상이면 미할당 처리
TARGET_TYPE   = '복합취약형'
TOP_N         = 20     # 고립지수 상위 N개 동만 커버


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))


def get_dong_centroids():
    with open(os.path.join(DATA_DIR, 'seoul_dong.geojson'), encoding='utf-8') as f:
        geo = json.load(f)
    gdf = gpd.GeoDataFrame.from_features(geo['features'], crs='EPSG:4326')
    code_key = next(k for k in ['adm_cd','emd_cd','ADM_DR_CD','HDONG_CD','adm_cd2']
                    if k in gdf.columns)
    gdf['_code'] = gdf[code_key].astype(str).str[:8]
    gdf['lat']   = gdf.geometry.centroid.y
    gdf['lon']   = gdf.geometry.centroid.x
    return gdf[['_code','lat','lon']]


def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── 1. 타겟 동 (복합취약형 + 사각지대) ───────────────────────
    df_quad = pd.read_csv(os.path.join(OUTPUT_DIR, '중장년_고립유형_사분면.csv'))
    df_acc  = pd.read_csv(os.path.join(OUTPUT_DIR, '중장년_접근성_분석.csv'))
    df_acc['covered_1km'] = df_acc['covered_1km'].fillna(False).astype(bool)

    df_quad['_code'] = df_quad['행정동코드'].astype(str).str[:8]
    df_acc['_code']  = df_acc['행정동코드'].astype(str).str[:8]

    df = df_quad.merge(df_acc[['_code','covered_1km','min_dist_km']], on='_code', how='left')
    df['covered_1km'] = df['covered_1km'].fillna(False).astype(bool)

    target = df[
        (df['유형'] == TARGET_TYPE) & ~df['covered_1km']
    ].copy()

    # 행정동 중심 좌표
    centroids = get_dong_centroids()
    target = target.merge(centroids, on='_code', how='left').dropna(subset=['lat','lon'])
    # 고립지수 상위 TOP_N개만
    target = target.nlargest(TOP_N, '고립지수_종합').reset_index(drop=True)

    # ── 2. 기존 거점 로드 ─────────────────────────────────────────
    shops = pd.read_csv(os.path.join(DATA_DIR, '마음편의점_19개소.csv'))
    shops = shops.dropna(subset=['lat','lon']).reset_index(drop=True)

    # ── 3. 각 동 → 가장 가까운 거점 배정 ─────────────────────────
    def nearest_shop(row):
        dists = shops.apply(
            lambda s: haversine(row['lat'], row['lon'], s['lat'], s['lon']), axis=1
        )
        idx = dists.idxmin()
        return shops.loc[idx, 'name'], dists[idx]

    target[['거점명', '거점_거리km']] = target.apply(
        lambda r: pd.Series(nearest_shop(r)), axis=1
    )

    # 거점 거리 초과 동 분리
    unassigned = target[target['거점_거리km'] > MAX_ASSIGN_KM].copy()
    target     = target[target['거점_거리km'] <= MAX_ASSIGN_KM].copy()

    # ── 4. 거점별 방문 스케줄 (고립지수 높은 순) ─────────────────
    target = target.sort_values(['거점명','고립지수_종합'], ascending=[True, False])
    target['방문순서'] = target.groupby('거점명').cumcount() + 1

    # ── 5. 결과 출력 ─────────────────────────────────────────────
    active_shops = target['거점명'].unique()
    print('=' * 68)
    print(f'  이동형 마음편의점 노선 (거점 기반, {TARGET_TYPE})')
    print('=' * 68)
    print(f'  복합취약형 사각지대 총 {len(target) + len(unassigned)}개 동')
    print(f'    → 거점 배정 완료: {len(target)}개 동  ({len(active_shops)}개 거점)')
    print(f'    → 거점 8km 초과 미할당: {len(unassigned)}개 동')

    total_days = 0
    for shop_name in sorted(active_shops):
        sub = target[target['거점명'] == shop_name].sort_values('방문순서')
        shop_row = shops[shops['name'] == shop_name].iloc[0]
        gu = shop_name.split('(')[0]
        weeks = len(sub)
        total_days += weeks
        print(f'\n  [{shop_name}]  담당 {len(sub)}개 동 → {weeks}주 순환')
        print(f'  {"순":<3} {"자치구":<5} {"행정동":<10} {"고립지수":>6}  {"거점까지":>6}  {"기존거점까지":>8}')
        print('  ' + '-' * 52)
        for _, r in sub.iterrows():
            print(f'  {int(r["방문순서"]):<3} {r["자치구"]:<5} {r["행정동"]:<10} '
                  f'{r["고립지수_종합"]:>6.4f}  {r["거점_거리km"]:>5.2f}km'
                  f'  {r["min_dist_km"]:>6.2f}km')

    print(f'\n  전체 {len(active_shops)}개 거점 운용, {len(target)}개 동 커버')
    if len(unassigned) > 0:
        print(f'\n  미할당 {len(unassigned)}개 동 (거점 8km 초과):')
        for _, r in unassigned.sort_values('고립지수_종합', ascending=False).iterrows():
            print(f'    {r["자치구"]} {r["행정동"]}  고립지수={r["고립지수_종합"]:.4f}'
                  f'  최근접거점={r["거점_거리km"]:.2f}km')

    # ── 6. 거점별 요약표 ─────────────────────────────────────────
    print('\n' + '=' * 68)
    print('  거점별 운영 요약')
    print('=' * 68)
    print(f'  {"거점명":<18} {"담당 동수":>6}  {"평균 고립지수":>10}  {"최대 고립지수":>10}  {"평균 거리km":>9}')
    print('  ' + '-' * 60)
    summary = (
        target.groupby('거점명')
        .agg(동수=('행정동','count'),
             평균고립=('고립지수_종합','mean'),
             최대고립=('고립지수_종합','max'),
             평균거리=('거점_거리km','mean'))
        .sort_values('최대고립', ascending=False)
    )
    for name, row in summary.iterrows():
        print(f'  {name:<18} {int(row["동수"]):>6}  {row["평균고립"]:>10.4f}'
              f'  {row["최대고립"]:>10.4f}  {row["평균거리"]:>9.2f}')

    # ── 7. CSV 저장 ───────────────────────────────────────────────
    out_path = os.path.join(OUTPUT_DIR, '이동형_마음편의점_노선v2.csv')
    target.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f'\n저장: {out_path}')

    # ── 8. 지도 ───────────────────────────────────────────────────
    plot_map(target, shops, unassigned)
    return target, summary


def plot_map(target, shops, unassigned):
    # 거점별 고유 색상
    shop_names = sorted(target['거점명'].unique())
    palette = [
        '#C00000','#E07B54','#5B9BD5','#70AD47','#9E6FC0','#F2C76A',
        '#2E75B6','#FF6B6B','#4ECDC4','#45B7D1','#96CEB4','#FFEAA7',
        '#DDA0DD','#98D8C8','#F7DC6F','#BB8FCE','#85C1E9','#82E0AA','#F0B27A',
    ]
    color_map = {name: palette[i % len(palette)] for i, name in enumerate(shop_names)}

    m = folium.Map(location=[37.5665, 126.9780], zoom_start=11,
                   tiles='CartoDB positron')

    # 기존 거점 마커 (활성 거점만 강조)
    active_set = set(target['거점명'].unique())
    for _, s in shops.iterrows():
        is_active = s['name'] in active_set
        n_dong = len(target[target['거점명'] == s['name']]) if is_active else 0
        folium.Marker(
            location=[s['lat'], s['lon']],
            tooltip=(f"<b>{s['name']}</b><br>"
                     f"{'담당 ' + str(n_dong) + '개 동' if is_active else '담당 동 없음'}"),
            icon=folium.Icon(
                color='red' if is_active else 'lightgray',
                icon='home', prefix='fa'
            )
        ).add_to(m)

        # 활성 거점은 방사선 연결선 + 동 마커
        if is_active:
            sub = target[target['거점명'] == s['name']].sort_values('방문순서')
            color = color_map[s['name']]
            for _, r in sub.iterrows():
                # 거점 → 동 연결선
                folium.PolyLine(
                    [[s['lat'], s['lon']], [r['lat'], r['lon']]],
                    color=color, weight=1.8, opacity=0.55, dash_array='6 4'
                ).add_to(m)
                # 동 마커
                folium.CircleMarker(
                    location=[r['lat'], r['lon']],
                    radius=6 + r['고립지수_종합'] * 4,   # 고립지수 높을수록 크게
                    color=color, fill=True, fill_color=color, fill_opacity=0.8,
                    tooltip=(
                        f"<b>{r['자치구']} {r['행정동']}</b><br>"
                        f"방문순서: {int(r['방문순서'])}번째<br>"
                        f"거점: {r['거점명']}<br>"
                        f"고립지수: {r['고립지수_종합']:.4f}<br>"
                        f"거점까지: {r['거점_거리km']:.2f}km"
                    )
                ).add_to(m)

    # 미할당 동 (회색 X)
    for _, r in unassigned.iterrows():
        folium.CircleMarker(
            location=[r['lat'], r['lon']],
            radius=6, color='#aaa', fill=True, fill_color='#ddd', fill_opacity=0.6,
            tooltip=f"{r['자치구']} {r['행정동']} (미할당, 거점 {r['거점_거리km']:.1f}km)"
        ).add_to(m)

    # 범례
    legend_html = '''
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
                background:white;padding:14px 18px;border-radius:10px;
                border:1px solid #ccc;font-size:12px;line-height:1.9;">
      <b>이동형 마음편의점 노선 (거점 기반)</b><br>
      <span style="color:#C00000;">●</span> 기존 거점 (활성) &nbsp;
      <span style="color:#aaa;">●</span> 기존 거점 (비활성)<br>
      <span>— — 점선:</span> 거점 → 담당 동 연결<br>
      <span>● 원 크기:</span> 고립지수 비례<br>
      <span style="color:#aaa;">●</span> 회색: 미할당 동 (거점 8km↑)
    </div>'''
    m.get_root().html.add_child(folium.Element(legend_html))

    path = os.path.join(OUTPUT_DIR, '08_이동형_노선v2_지도.html')
    m.save(path)
    print(f'저장: {path}')


if __name__ == '__main__':
    target, summary = run()
