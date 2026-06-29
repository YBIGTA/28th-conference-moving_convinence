# -*- coding: utf-8 -*-

# 은평구 내 6개 복합취약형 동 우선순위
# Jenks 경제축 임계값 ≈0.41 적용 → 6개 동 (대조동·신사1동·신사2동 경제축 미달로 제외)
PRIORITY_DATA = [
    {"dong": "역촌동",  "isolation": 0.638, "population": 14110, "score": 8997, "visits": "주 2회", "peak": "저녁"},
    {"dong": "응암3동", "isolation": 0.690, "population": 8034,  "score": 5543, "visits": "주 1회", "peak": "저녁"},
    {"dong": "구산동",  "isolation": 0.571, "population": 7951,  "score": 4542, "visits": "주 1회", "peak": "저녁"},
    {"dong": "갈현2동", "isolation": 0.582, "population": 7243,  "score": 4215, "visits": "주 1회", "peak": "저녁"},
    {"dong": "불광2동", "isolation": 0.644, "population": 6235,  "score": 4017, "visits": "주 1회", "peak": "오전"},
    {"dong": "갈현1동", "isolation": 0.619, "population": 6056,  "score": 3750, "visits": "주 1회", "peak": "저녁"},
]

# 마음편의점 미운영 자치구 중 복합취약형 사각지대 동 수 (상위 10개 구)
GU_COMPARISON = [
    {"gu": "은평구",  "count": 6},
    {"gu": "강북구",  "count": 5},
    {"gu": "관악구",  "count": 4},
    {"gu": "금천구",  "count": 4},
    {"gu": "구로구",  "count": 3},
    {"gu": "중랑구",  "count": 3},
    {"gu": "도봉구",  "count": 2},
    {"gu": "동대문구","count": 2},
    {"gu": "강서구",  "count": 2},
    {"gu": "양천구",  "count": 1},
]

# 고립지수 4개 차원 설명
DIMENSIONS = [
    {"name": "경제적 불안정성", "desc": "소득 감소, 소비 위축, 경제활동 중단 등 경제적 고립 신호"},
    {"name": "사회활동",       "desc": "외출 빈도, 이동 패턴, 사회적 참여 감소 신호"},
    {"name": "고립형 생활",    "desc": "야간 외출 부재, 비활동 시간대 증가 등 은둔 패턴"},
    {"name": "사회적 관계",    "desc": "통신 빈도, 데이터 사용량으로 추정한 관계망 축소"},
]

# ── 동선 2안: 고립 차원 이원화 ───────────────────────────────────────────────
# 사회적연결결핍 = (지수_사회활동 + 지수_사회적_관계) / 2
# 6개 복합취약형 동 내부 z-score 기준 비교
# 분류: z_사회 >= z_경제 → 관계 회복 트랙 / z_사회 < z_경제 → 복지 연계 트랙
TRACK_DATA_V2 = [
    {"dong": "역촌동",  "track": "관계 회복", "isolation": 0.638, "social": 0.673, "economic": 0.422, "z_diff": +1.16},
    {"dong": "불광2동", "track": "관계 회복", "isolation": 0.644, "social": 0.700, "economic": 0.471, "z_diff": +0.30},
    {"dong": "갈현2동", "track": "복지 연계", "isolation": 0.582, "social": 0.607, "economic": 0.427, "z_diff": -0.14},
    {"dong": "응암3동", "track": "복지 연계", "isolation": 0.690, "social": 0.758, "economic": 0.527, "z_diff": -0.25},
    {"dong": "구산동",  "track": "복지 연계", "isolation": 0.571, "social": 0.591, "economic": 0.430, "z_diff": -0.51},
    {"dong": "갈현1동", "track": "복지 연계", "isolation": 0.619, "social": 0.636, "economic": 0.461, "z_diff": -0.55},
]

# 동선 2안 주간 스케줄 (표시용) — 월~목 4일제
SCHEDULE_V2_DISPLAY = [
    {"day": "월", "track": "관계 회복", "morning": "불광2동 (불광2동 주민센터)", "afternoon": "역촌동 (역촌동 주민센터)"},
    {"day": "화", "track": "복지 연계", "morning": "갈현1동 (갈현1동 주민센터)", "afternoon": "응암3동 (응암3동 주민센터)"},
    {"day": "수", "track": "복지 연계", "morning": "갈현2동 (갈현2동 주민센터)", "afternoon": "구산동 (구산동도서관마을)"},
    {"day": "목", "track": "관계 회복", "morning": "역촌동 (역촌동 주민센터) ★전일 08–18시 (주 2회)", "afternoon": "—"},
]
