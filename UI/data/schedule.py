# -*- coding: utf-8 -*-

HUB_NAME = "신사종합사회복지관"
HUB_COORD = (37.598056, 126.912212)

# 복합취약형 6개 동만 운영 대상
DONG_SPOT = {
    "불광2동": ("불광2동 주민센터",   37.626383, 126.927266),
    "갈현1동": ("갈현1동 주민센터",   37.623700, 126.916695),
    "갈현2동": ("갈현2동 주민센터",   37.618586, 126.915839),
    "구산동":  ("구산동도서관마을",   37.609518, 126.913097),
    "역촌동":  ("역촌동 주민센터",    37.604429, 126.915108),
    "응암3동": ("응암3동 주민센터",   37.592246, 126.915734),
}

PEAK = {
    "불광2동": "오전",
    "갈현1동": "저녁", "갈현2동": "저녁", "구산동": "저녁",
    "역촌동": "저녁", "응암3동": "저녁",
}

# 동선 1안 — 월~목 4일제, 하루 2거점
# 역촌동·응암3동(1·2순위)은 화·목 각 1회씩 총 주 2회 방문
# (요일, 첫번째동, 시간대1, 두번째동, 시간대2)
SCHEDULE = [
    ("월", "불광2동", "오전 08:00–13:00", "갈현1동", "오후 14:00–18:00"),
    ("화", "역촌동",  "오전 08:00–13:00", "응암3동", "오후 14:00–18:00"),
    ("수", "구산동",  "오전 08:00–13:00", "갈현2동", "오후 14:00–18:00"),
    ("목", "역촌동",  "오전 08:00–13:00", "응암3동", "오후 14:00–18:00"),
]

DAY_COLORS = {
    "월": "#10B981",  # 에메랄드
    "화": "#6366F1",  # 인디고
    "수": "#F59E0B",  # 앰버
    "목": "#EF4444",  # 레드
}

DAY_KR = {"월": "월요일", "화": "화요일", "수": "수요일", "목": "목요일"}


def get_dong_schedule(dong_name: str) -> list:
    """Return visit schedule entries for a given dong (동선 1안).

    Each entry is a dict with keys: day, time, order, spot_name.
    역촌동·응암3동은 화·목 2회 방문이므로 두 개 entry 반환.
    """
    results = []
    for row in SCHEDULE:
        day, dong1, time1, dong2, time2 = row
        if dong_name == dong1:
            spot_name = DONG_SPOT[dong_name][0] if dong_name in DONG_SPOT else dong_name
            results.append({
                "day": day,
                "time": time1,
                "order": 1,
                "spot_name": spot_name,
            })
        if dong_name == dong2:
            spot_name = DONG_SPOT[dong_name][0] if dong_name in DONG_SPOT else dong_name
            results.append({
                "day": day,
                "time": time2,
                "order": 2,
                "spot_name": spot_name,
            })
    return results


# ── 동선 2안 ──────────────────────────────────────────────────────────────────
# 트랙 기반 묶음 방문: 같은 트랙 두 동을 하루에 묶어 반나절씩 운영
# 역촌동(1순위)은 목요일 전일 집중 (주 2회)
# dong2가 빈 문자열("")이면 해당 요일은 dong1 전일 집중
SCHEDULE_V2 = [
    ("월", "불광2동", "오전 08:00–13:00", "역촌동",  "오후 14:00–18:00"),
    ("화", "갈현1동", "오전 08:00–13:00", "응암3동", "오후 14:00–18:00"),
    ("수", "갈현2동", "오전 08:00–13:00", "구산동",  "오후 14:00–18:00"),
    ("목", "역촌동",  "전일 08:00–18:00", "",        ""),
]

# 트랙 분류 (z_사회 vs z_경제 기준 — 6개 동 내부)
DONG_TRACK_V2 = {
    "역촌동":  "관계 회복", "불광2동": "관계 회복",
    "응암3동": "복지 연계", "갈현1동": "복지 연계",
    "갈현2동": "복지 연계", "구산동":  "복지 연계",
}

TRACK_COLORS_V2 = {
    "관계 회복": "#6366F1",  # indigo
    "복지 연계": "#F59E0B",  # amber
}


def get_dong_schedule_v2(dong_name: str) -> list:
    results = []
    for row in SCHEDULE_V2:
        day, dong1, time1, dong2, time2 = row
        if dong_name == dong1:
            spot_name = DONG_SPOT[dong_name][0] if dong_name in DONG_SPOT else dong_name
            results.append({"day": day, "time": time1, "order": 1, "spot_name": spot_name})
        if dong2 and dong_name == dong2:
            spot_name = DONG_SPOT[dong_name][0] if dong_name in DONG_SPOT else dong_name
            results.append({"day": day, "time": time2, "order": 2, "spot_name": spot_name})
    return results
