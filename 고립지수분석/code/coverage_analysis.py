# coverage_analysis.py
# Stage 2: 기존 마음편의점 19개소 접근성 사각지대 분석
#   - Nominatim 지오코딩 → 행정동 중심점 거리 계산 (EPSG:5179, 미터)
#   - 1km 도보권 밖 중장년 인구 및 고립 사각지대 교집합 산출

import pandas as pd
import numpy as np
import geopandas as gpd
import json, os, requests, time
from shapely.geometry import Point

DATA_DIR     = r'D:\서울시 데이터'
OUTPUT_DIR   = r'D:\서울시 데이터\outputs'
GEOJSON_PATH = os.path.join(DATA_DIR, 'seoul_dong.geojson')
SHOPS_CSV    = os.path.join(DATA_DIR, '마음편의점_19개소.csv')

# 사용자 제공 정확 주소 (2026-05)
SHOPS = [
    {'name': '관악1(호암로)',    'address': '서울 관악구 호암로 549'},
    {'name': '동대문(약령시)',   'address': '서울 동대문구 약령시로5길 22'},
    {'name': '강북(오현로)',     'address': '서울 강북구 오현로 208'},
    {'name': '도봉1(덕릉로)',    'address': '서울 도봉구 덕릉로 329'},
    {'name': '구로(벚꽃로)',     'address': '서울 구로구 벚꽃로 484'},
    {'name': '강동(성안로)',     'address': '서울 강동구 성안로13길 56'},
    {'name': '성북1(오패산로)',  'address': '서울 성북구 오패산로 21'},
    {'name': '광진(능동로)',     'address': '서울 광진구 능동로 400'},
    {'name': '도봉2(시루봉로)', 'address': '서울 도봉구 시루봉로17길 42'},
    {'name': '송파1(마천로)',    'address': '서울 송파구 마천로51길 7'},
    {'name': '송파2(가락로)',    'address': '서울 송파구 가락로 87'},
    {'name': '관악2(관악로)',    'address': '서울 관악구 관악로 254'},
    {'name': '양천1(목동북로)', 'address': '서울 양천구 목동중앙북로8길 104'},
    {'name': '양천2(신정중앙)', 'address': '서울 양천구 신정중앙로 36'},
    {'name': '성북2(솔샘로)',    'address': '서울 성북구 솔샘로5길 92'},
    {'name': '중랑(상봉로)',     'address': '서울 중랑구 상봉로15길 5'},
    {'name': '금천1(금하로)',    'address': '서울 금천구 금하로29길 36'},
    {'name': '금천2(가산로)',    'address': '서울 금천구 가산로 129'},
    {'name': '성동(마장로)',     'address': '서울 성동구 마장로39길 31'},
]

# 지오코딩 실패 시 사용할 fallback 좌표 (기존 CSV 기반 + 수정)
FALLBACK_COORDS = {
    '관악1(호암로)':   (37.4597, 126.9228),
    '동대문(약령시)':  (37.5827, 127.0432),
    '강북(오현로)':    (37.6296, 127.0394),
    '도봉1(덕릉로)':   (37.6427, 127.0419),
    '구로(벚꽃로)':    (37.4953, 126.8800),
    '강동(성안로)':    (37.5294, 127.1315),
    '성북1(오패산로)': (37.6031, 127.0371),
    '광진(능동로)':    (37.5537, 127.0780),
    '도봉2(시루봉로)': (37.6688, 127.0355),
    '송파1(마천로)':   (37.5073, 127.1290),
    '송파2(가락로)':   (37.5006, 127.1071),
    '관악2(관악로)':   (37.4735, 126.9530),
    '양천1(목동북로)': (37.5443, 126.8664),
    '양천2(신정중앙)': (37.5262, 126.8637),
    '성북2(솔샘로)':   (37.6080, 127.0047),
    '중랑(상봉로)':    (37.5909, 127.0936),
    '금천1(금하로)':   (37.4534, 126.8971),
    '금천2(가산로)':   (37.4711, 126.8970),   # 가산로 가산디지털단지 인근
    '성동(마장로)':    (37.5666, 127.0319),
}


def geocode_nominatim(address, retries=2):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {'q': address, 'format': 'json', 'limit': 1, 'countrycodes': 'kr'}
    headers = {'User-Agent': 'SeoulIsolationAnalysis/1.0 (research)'}
    for _ in range(retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=8)
            data = r.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
        except Exception:
            time.sleep(1)
    return None, None


def load_shops():
    rows = []
    print("  주소 → 좌표 변환 중...")
    for shop in SHOPS:
        lat, lon = geocode_nominatim(shop['address'])
        if lat is None:
            lat, lon = FALLBACK_COORDS[shop['name']]
            src = 'fallback'
        else:
            src = 'nominatim'
        rows.append({'name': shop['name'], 'address': shop['address'],
                     'lat': lat, 'lon': lon, 'source': src})
        print(f"    {shop['name']}: ({lat:.4f}, {lon:.4f}) [{src}]")
        time.sleep(1.1)   # Nominatim 1 req/s
    df = pd.DataFrame(rows)
    df.to_csv(SHOPS_CSV, index=False, encoding='utf-8-sig')
    print(f"  저장: {SHOPS_CSV}")
    return df


def get_dong_centroids():
    """GeoJSON → 행정동 중심점 GeoDataFrame (EPSG:5179)"""
    with open(GEOJSON_PATH, encoding='utf-8') as f:
        geo = json.load(f)
    gdf = gpd.GeoDataFrame.from_features(geo['features'], crs='EPSG:4326')
    gdf = gdf.to_crs('EPSG:5179')
    gdf['centroid'] = gdf.geometry.centroid

    code_key = next(
        (k for k in ['adm_cd', 'emd_cd', 'ADM_DR_CD', 'HDONG_CD', 'adm_cd2']
         if k in gdf.columns), None
    )
    gdf['_code'] = gdf[code_key].astype(str).str[:8]
    return gdf[['_code', 'centroid']].set_geometry('centroid', crs='EPSG:5179')


def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. 마음편의점 좌표
    print("1. 마음편의점 지오코딩")
    df_shops = load_shops()

    # 2. 행정동 중심점
    print("2. 행정동 중심점 (EPSG:5179)")
    centroids = get_dong_centroids()

    # 3. 마음편의점 → EPSG:5179
    print("3. 거리 행렬 계산")
    shop_geom = [Point(row.lon, row.lat) for _, row in df_shops.iterrows()]
    gdf_shops = gpd.GeoDataFrame(df_shops, geometry=shop_geom, crs='EPSG:4326')
    gdf_shops = gdf_shops.to_crs('EPSG:5179')
    shop_xy = np.array([(g.x, g.y) for g in gdf_shops.geometry])

    # 각 행정동 중심 → 가장 가까운 마음편의점 거리
    min_dists, nearest_names = [], []
    for _, row in centroids.iterrows():
        cx, cy = row['centroid'].x, row['centroid'].y
        dists = np.sqrt((shop_xy[:, 0] - cx)**2 + (shop_xy[:, 1] - cy)**2)
        idx = dists.argmin()
        min_dists.append(dists[idx])
        nearest_names.append(df_shops.iloc[idx]['name'])

    centroids = centroids.copy()
    centroids['min_dist_m']   = min_dists
    centroids['nearest_shop'] = nearest_names
    centroids['covered_1km']  = centroids['min_dist_m'] <= 1000

    # 4. 고립지수 연간 데이터 조인
    print("4. 고립지수 × 접근성 조인")
    df_ann = pd.read_csv(os.path.join(OUTPUT_DIR, '중장년_연간_고립지수.csv'))
    df_ann = df_ann[df_ann['총인구수'] >= 500].copy()
    df_ann['_code'] = df_ann['행정동코드'].astype(str).str[:8]

    df = df_ann.merge(
        centroids[['_code', 'min_dist_m', 'nearest_shop', 'covered_1km']],
        on='_code', how='left'
    )
    df['min_dist_km'] = df['min_dist_m'] / 1000
    # 조인 미매칭 행정동은 사각지대로 처리
    df['covered_1km'] = df['covered_1km'].fillna(False).astype(bool)

    # 5. 핵심 지표
    print()
    print("=" * 62)
    print("  기존 마음편의점 19개소 접근성 사각지대 분석 (2025년 기준)")
    print("=" * 62)

    total_pop  = df['총인구수'].sum()
    uncov_df   = df[~df['covered_1km']]
    cov_df     = df[df['covered_1km']]
    uncov_pop  = uncov_df['총인구수'].sum()
    cov_pop    = cov_df['총인구수'].sum()

    print(f"\n[전체]")
    print(f"  분석 행정동 수       : {len(df):>4d}개")
    print(f"  중장년 총인구         : {total_pop:>10,.0f}명")

    print(f"\n[1km 도보권 내]")
    print(f"  행정동 수            : {len(cov_df):>4d}개")
    print(f"  중장년 인구           : {cov_pop:>10,.0f}명  ({cov_pop/total_pop*100:.1f}%)")

    print(f"\n[1km 도보권 밖 - 사각지대]")
    print(f"  행정동 수            : {len(uncov_df):>4d}개")
    print(f"  중장년 인구           : {uncov_pop:>10,.0f}명  ({uncov_pop/total_pop*100:.1f}%)")

    # 고립지수 상위 25% × 사각지대 교집합 (타겟 행정동)
    q75     = df['고립지수_종합'].quantile(0.75)
    target  = df[(df['고립지수_종합'] >= q75) & ~df['covered_1km']]

    print(f"\n[타겟: 고립↑(상위25%) + 사각지대 교집합]")
    print(f"  고립지수 75분위 기준값: {q75:.4f}")
    print(f"  해당 행정동 수        : {len(target):>4d}개")
    print(f"  해당 중장년 인구       : {target['총인구수'].sum():>10,.0f}명")

    print(f"\n  타겟 행정동 상위 20 (고립지수 순):")
    top20 = (
        target.nlargest(20, '고립지수_종합')
        [['자치구', '행정동', '고립지수_종합', '총인구수', 'min_dist_km', 'nearest_shop']]
        .rename(columns={'min_dist_km': '최근접_km', 'nearest_shop': '가까운거점'})
    )
    print(top20.round({'고립지수_종합': 4, '최근접_km': 2}).to_string(index=False))

    # 자치구별 사각지대 요약
    print(f"\n[자치구별 사각지대 현황]")
    gu_sum = (
        uncov_df.groupby('자치구')
        .agg(사각지대_동수=('행정동', 'count'), 사각지대_인구=('총인구수', 'sum'))
        .sort_values('사각지대_인구', ascending=False)
    )
    print(gu_sum.to_string())

    # 6. 저장
    out_path = os.path.join(OUTPUT_DIR, '중장년_접근성_분석.csv')
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"\n저장: {out_path}")

    return df, target


if __name__ == '__main__':
    df_result, df_target = run()
