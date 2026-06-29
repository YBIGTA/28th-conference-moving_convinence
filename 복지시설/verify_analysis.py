# -*- coding: utf-8 -*-
# 복합취약형 동 내 거점 — 집계구 생활인구 밀집도 검증

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from pyproj import Transformer

COMPLEX_RISK = {"응암3동","불광2동","역촌동","갈현1동","갈현2동","구산동"}

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

# 집계구 shapefile 로드
shp = gpd.read_file("통계지역경계(2016년+기준)/집계구.shp", encoding="cp949")
dong_shp = gpd.read_file("통계지역경계(2016년+기준)/행정구역.shp", encoding="cp949")
eunp_dongs = dong_shp[dong_shp["SIGUNGU_NM"] == "은평구"]["ADM_NM"].tolist()
shp = shp[shp["ADM_NM"].isin(eunp_dongs)].copy().reset_index(drop=True)
shp = shp.set_crs("EPSG:5179", allow_override=True).to_crs("EPSG:3857")

oa_df = pd.read_csv("eunpyeong/data/집계구_전체_절대인구.csv", dtype={"OA_CD": str})
shp = shp.merge(oa_df[["OA_CD", "MID_POP"]], left_on="TOT_REG_CD", right_on="OA_CD", how="left")

# 동별 순위 계산
shp["dong_rank"]  = shp.groupby("ADM_NM")["MID_POP"].rank(ascending=False, method="min")
shp["dong_total"] = shp.groupby("ADM_NM")["MID_POP"].transform("count")
shp["dong_pct"]   = shp["dong_rank"] / shp["dong_total"] * 100   # 낮을수록 상위

# 거점별 매핑
results = []
for name, lat, lon in candidates:
    x, y = tf.transform(lon, lat)
    pt = Point(x, y)
    matched = shp[shp.geometry.contains(pt)]
    if matched.empty:
        shp_copy = shp.copy()
        shp_copy["dist"] = shp_copy.geometry.distance(pt)
        matched = shp_copy.nsmallest(1, "dist")
        how = "최근접"
    else:
        matched = matched.iloc[[0]]
        how = "포함"
    row = matched.iloc[0]
    dong = row["ADM_NM"]
    results.append({
        "거점":     name,
        "소속동":   dong,
        "복합취약형": "★" if dong in COMPLEX_RISK else "-",
        "집계방법": how,
        "MID_POP":  round(row["MID_POP"], 1) if pd.notna(row["MID_POP"]) else None,
        "동내순위": f"{int(row['dong_rank'])}/{int(row['dong_total'])}",
        "상위%":    f"{row['dong_pct']:.0f}%",
    })

df = pd.DataFrame(results)

# 복합취약형 동 거점만 출력
risk_df = df[df["복합취약형"] == "★"].sort_values("소속동").reset_index(drop=True)

print("=" * 65)
print("  복합취약형 동 내 거점  집계구 생활인구 밀집도 검증")
print("  (MID_POP: 중장년 생활인구 명/집계구 평균, 08-20시)")
print("=" * 65)
print(risk_df[["거점","소속동","MID_POP","동내순위","상위%"]].to_string(index=False))

print()
print("  해석 기준: 상위% 낮을수록 거점이 밀집 지역에 위치")
print("  상위10% 이내 = 밀집, 25% 이내 = 양호, 50% 이상 = 분산 지역")

# 동별 상위 3개 집계구 목록 (거점이 없거나 분산 지역인 동 확인용)
print()
print("=" * 65)
print("  복합취약형 동별 생활인구 상위 3개 집계구")
print("=" * 65)
for dong in sorted(COMPLEX_RISK):
    sub = shp[shp["ADM_NM"] == dong].nsmallest(3, "dong_rank")[["TOT_REG_CD","MID_POP","dong_rank"]]
    print(f"\n  [{dong}]")
    for _, r in sub.iterrows():
        print(f"    집계구 {r['TOT_REG_CD']}  MID_POP={r['MID_POP']:.1f}  동내{int(r['dong_rank'])}위")
