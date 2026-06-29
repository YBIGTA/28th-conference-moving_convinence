# -*- coding: utf-8 -*-
# 보통/불일치 거점 -> 동 내 밀집 집계구 거리 분석

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from pyproj import Transformer

COMPLEX_RISK = {"응암3동","불광2동","역촌동","갈현1동","갈현2동","구산동"}

# 판정 기준 (상위%)
THRESHOLD_GOOD = 25   # 25% 이내 = 밀집/양호 -> 거리 확인 불필요
DIST_CLOSE     = 400  # 400m 이내 = 도보 5분, 가까움
DIST_MID       = 800  # 400~800m = 도보 10분, 보통

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
tf_back = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

# 집계구 shapefile 로드
shp = gpd.read_file("통계지역경계(2016년+기준)/집계구.shp", encoding="cp949")
dong_shp = gpd.read_file("통계지역경계(2016년+기준)/행정구역.shp", encoding="cp949")
eunp_dongs = dong_shp[dong_shp["SIGUNGU_NM"] == "은평구"]["ADM_NM"].tolist()
shp = shp[shp["ADM_NM"].isin(eunp_dongs)].copy().reset_index(drop=True)
shp = shp.set_crs("EPSG:5179", allow_override=True).to_crs("EPSG:3857")

oa_df = pd.read_csv("eunpyeong/data/집계구_전체_절대인구.csv", dtype={"OA_CD": str})
shp = shp.merge(oa_df[["OA_CD","MID_POP"]], left_on="TOT_REG_CD", right_on="OA_CD", how="left")
shp["dong_rank"]  = shp.groupby("ADM_NM")["MID_POP"].rank(ascending=False, method="min")
shp["dong_total"] = shp.groupby("ADM_NM")["MID_POP"].transform("count")
shp["dong_pct"]   = shp["dong_rank"] / shp["dong_total"] * 100

# ── 거점별 소속 집계구 상위% 매핑 ─────────────────────────────────────────────
거점_info = {}
for name, lat, lon in candidates:
    x, y = tf.transform(lon, lat)
    pt = Point(x, y)
    matched = shp[shp.geometry.contains(pt)]
    if matched.empty:
        shp["_d"] = shp.geometry.distance(pt)
        matched = shp.nsmallest(1, "_d")
    row = matched.iloc[0]
    dong = row["ADM_NM"]
    if dong in COMPLEX_RISK:
        거점_info[name] = {
            "dong": dong, "x": x, "y": y,
            "pct": row["dong_pct"],
            "mid_pop": row["MID_POP"],
            "rank": int(row["dong_rank"]),
            "total": int(row["dong_total"]),
        }

# ── 상위% 25% 초과 거점만 거리 분석 ──────────────────────────────────────────
CHECK_TARGETS = {k: v for k, v in 거점_info.items() if v["pct"] > THRESHOLD_GOOD}

print("=" * 72)
print("  거점 -> 동내 생활인구 밀집 집계구 거리 분석")
print(f"  (상위 {THRESHOLD_GOOD}% 초과 거점 대상 / 기준: 상위 30% 집계구 중 최근접)")
print("=" * 72)

need_new = []

for name, info in sorted(CHECK_TARGETS.items(), key=lambda x: x[1]["dong"]):
    dong = info["dong"]
    pt   = Point(info["x"], info["y"])

    # 동 내 상위 30% 집계구
    dong_shp_sub = shp[shp["ADM_NM"] == dong].copy()
    top30 = dong_shp_sub[dong_shp_sub["dong_pct"] <= 30].copy()
    if top30.empty:
        top30 = dong_shp_sub.nsmallest(3, "dong_rank")

    top30["centroid"] = top30.geometry.centroid
    top30["dist_m"]   = top30["centroid"].apply(lambda c: pt.distance(c))
    nearest = top30.nsmallest(1, "dist_m").iloc[0]
    dist_m  = nearest["dist_m"]

    if dist_m <= DIST_CLOSE:
        dist_label = f"가까움 ({dist_m:.0f}m, 도보 ~{dist_m/80:.0f}분)"
        verdict = "유지"
    elif dist_m <= DIST_MID:
        dist_label = f"보통 ({dist_m:.0f}m, 도보 ~{dist_m/80:.0f}분)"
        verdict = "유지 검토"
    else:
        dist_label = f"멀다 ({dist_m:.0f}m, 도보 ~{dist_m/80:.0f}분)"
        verdict = "대안 필요"
        # 최근접 밀집 집계구 중심 좌표 (WGS84)
        cx, cy = nearest["centroid"].x, nearest["centroid"].y
        lon84, lat84 = tf_back.transform(cx, cy)
        need_new.append({
            "동": dong, "거점": name,
            "거리": f"{dist_m:.0f}m",
            "밀집집계구": nearest["TOT_REG_CD"],
            "밀집MID_POP": round(nearest["MID_POP"], 1),
            "밀집중심_lat": round(lat84, 6),
            "밀집중심_lon": round(lon84, 6),
        })

    print(f"\n  [{dong}] {name}")
    print(f"    현재 위치: 동내 {info['rank']}/{info['total']}위 (상위 {info['pct']:.0f}%)")
    print(f"    최근접 상위30% 집계구까지: {dist_label}")
    print(f"    판정: {verdict}")

if need_new:
    print()
    print("=" * 72)
    print("  대안 거점 필요 동 -- 밀집 집계구 중심 좌표")
    print("=" * 72)
    for r in need_new:
        print(f"\n  [{r['동']}]  현재 거점: {r['거점']}  ({r['거리']} 떨어짐)")
        print(f"    밀집 집계구: {r['밀집집계구']}  MID_POP={r['밀집MID_POP']}")
        print(f"    집계구 중심 좌표: lat={r['밀집중심_lat']}, lon={r['밀집중심_lon']}")
        print(f"    -> 이 좌표 주변 공공시설 확인 필요")
else:
    print()
    print("  -> 모든 거점이 밀집 지역 도보권 내에 위치합니다.")
