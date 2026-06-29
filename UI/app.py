# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from openai import OpenAI

import math
import streamlit.components.v1 as components
from streamlit_geolocation import streamlit_geolocation
from data.schedule import (
    SCHEDULE, SCHEDULE_V2,
    DONG_SPOT, HUB_NAME, HUB_COORD, PEAK,
    DAY_COLORS, DAY_KR,
    get_dong_schedule, get_dong_schedule_v2,
    DONG_TRACK_V2, TRACK_COLORS_V2,
)
from data.districts import DISTRICTS
from data.analysis_data import PRIORITY_DATA, GU_COMPARISON, DIMENSIONS, TRACK_DATA_V2, SCHEDULE_V2_DISPLAY
from data.programs import PROGRAMS, PROGRAMS_V2

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="이동형 마음편의점",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Hide Streamlit default chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}

/* Global font */
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
}

/* ── Card containers ── */
.card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 20px 24px;
    box-shadow: 0 2px 10px rgba(74,127,191,0.10);
    margin-bottom: 14px;
    border: 1px solid #E8EFF8;
}
.card-soft {
    background: #F7FAFF;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
    border: 1px solid #DDE9F7;
    min-height: 130px;
    box-sizing: border-box;
}

/* Streamlit 헤딩 앵커 링크 숨기기 */
h1 a, h2 a, h3 a, a.anchor-link { display: none !important; }

/* ── Badges ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 6px;
}
.badge-blue   { background:#EBF2FF; color:#2563EB; }
.badge-green  { background:#ECFDF5; color:#059669; }
.badge-orange { background:#FFF7ED; color:#D97706; }
.badge-red    { background:#FEF2F2; color:#DC2626; }
.badge-purple { background:#F5F3FF; color:#7C3AED; }
.badge-teal   { background:#F0FDFA; color:#0D9488; }
.badge-gray   { background:#F3F4F6; color:#6B7280; }

/* ── Day color badges ── */
.day-월 { background:#EEF2FF; color:#4F46E5; border:1.5px solid #818CF8; }
.day-화 { background:#ECFDF5; color:#059669; border:1.5px solid #34D399; }
.day-수 { background:#FFFBEB; color:#D97706; border:1.5px solid #FCD34D; }
.day-목 { background:#FEF2F2; color:#DC2626; border:1.5px solid #FCA5A5; }
.day-금 { background:#F5F3FF; color:#7C3AED; border:1.5px solid #C4B5FD; }

/* ── Page title ── */
.page-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #1E3A5F;
    text-align: center;
    margin-bottom: 6px;
}
.page-tagline {
    font-size: 1.15rem;
    color: #4A7FBF;
    text-align: center;
    margin-bottom: 4px;
    font-weight: 500;
}
.page-desc {
    font-size: 0.95rem;
    color: #6B7280;
    text-align: center;
    margin-bottom: 28px;
}

/* ── Feature cards on home ── */
.feature-card {
    background: linear-gradient(135deg, #F0F7FF 0%, #FFFFFF 100%);
    border-radius: 16px;
    padding: 22px 18px;
    text-align: center;
    border: 1.5px solid #C7DEFF;
    transition: box-shadow 0.2s;
}
.feature-icon { font-size: 2.2rem; margin-bottom: 8px; }
.feature-title { font-size: 1rem; font-weight: 700; color: #1E3A5F; }
.feature-desc  { font-size: 0.82rem; color: #6B7280; margin-top: 4px; }

/* ── Program card ── */
.prog-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 18px 22px;
    border: 1px solid #E0ECF8;
    margin-bottom: 12px;
    box-shadow: 0 1px 6px rgba(74,127,191,0.07);
}
.prog-name { font-size: 1.05rem; font-weight: 700; color: #1E3A5F; margin-bottom: 4px; }
.prog-desc { font-size: 0.9rem; color: #4B5563; line-height: 1.5; margin-bottom: 10px; }

/* ── Visit card ── */
.visit-card {
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 12px;
    border-left: 5px solid #4A7FBF;
}

/* ── Section header ── */
.section-header {
    font-size: 1.2rem;
    font-weight: 700;
    color: #1E3A5F;
    border-bottom: 2px solid #C7DEFF;
    padding-bottom: 6px;
    margin-bottom: 16px;
    margin-top: 24px;
}

/* ── Info box ── */
.info-box {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 10px;
    padding: 14px 18px;
    color: #1E40AF;
    font-size: 0.92rem;
    line-height: 1.6;
    margin-bottom: 16px;
}
.warn-box {
    background: #FFF7ED;
    border: 1px solid #FDE68A;
    border-radius: 10px;
    padding: 14px 18px;
    color: #92400E;
    font-size: 0.92rem;
    line-height: 1.6;
    margin-bottom: 16px;
}

/* ── Tab overrides ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #F0F5FB;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 6px 16px;
    font-weight: 600;
    color: #6B7280;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #1E3A5F !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

/* ── Chat ── */
.chat-system-msg {
    background: #F0F5FB;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.88rem;
    color: #4B5563;
    margin-bottom: 12px;
}

/* ── Star badge ── */
.star-badge {
    background: linear-gradient(90deg,#FEF3C7,#FDE68A);
    color: #92400E;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 700;
    display: inline-block;
    margin-bottom: 6px;
}

/* ── 프로그램 빠른 이동 버튼 ── */
.nav-btn {
    display: inline-block;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    text-decoration: none !important;
    margin-right: 4px;
    margin-bottom: 6px;
    border: 1.5px solid #C7DEFF;
    color: #1E3A5F;
    background: #F0F7FF;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
}
.nav-btn:hover {
    background: #C7DEFF;
    color: #1E3A5F;
    text-decoration: none !important;
}

/* 앵커 스크롤 시 상단 여백 (sticky 헤더 고려) */
div[id^="prog-"] {
    scroll-margin-top: 60px;
}

/* ── Divider ── */
.soft-divider {
    border: none;
    border-top: 1px solid #E5EAF2;
    margin: 18px 0;
}

/* ── 맨 위로 버튼 ── */
.back-to-top {
    position: fixed;
    bottom: 32px;
    right: 32px;
    width: 46px;
    height: 46px;
    border-radius: 50%;
    background: #1E3A5F;
    color: white !important;
    font-size: 22px;
    line-height: 46px;
    text-align: center;
    text-decoration: none !important;
    box-shadow: 0 3px 12px rgba(30,58,95,0.35);
    z-index: 99999;
    display: block;
    transition: background 0.2s, transform 0.15s;
}
.back-to-top:hover {
    background: #2E5494;
    transform: translateY(-2px);
    color: white !important;
    text-decoration: none !important;
}


/* ── Analysis dimension card ── */
.dim-card {
    background: linear-gradient(135deg,#F0F7FF,#FFFFFF);
    border-radius: 12px;
    padding: 16px 20px;
    border: 1.5px solid #BFDBFE;
    height: 100%;
}
.dim-name { font-size: 0.98rem; font-weight: 700; color: #1E3A5F; margin-bottom: 6px; }
.dim-desc { font-size: 0.86rem; color: #4B5563; line-height: 1.5; }
</style>
""", unsafe_allow_html=True)

BACK_TO_TOP_HTML = '<a id="st-back-to-top" href="#page-top" class="back-to-top">↑</a>'

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALISATION
# ──────────────────────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "page": "login",
        "selected_gu": None,
        "selected_dong": None,
        "chat_history": [],
        "reg_program": None,
        "user_name": "",
        "user_phone": "",
        "user_gu": "",
        "user_dong": "",
        "user_birth": "",
        "logged_in": False,
        "plan_version": "1안",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


def get_plan_data():
    """현재 plan_version에 맞는 (schedule, programs, get_dong_schedule_fn) 반환"""
    if st.session_state.get("plan_version", "1안") == "2안":
        return SCHEDULE_V2, PROGRAMS_V2, get_dong_schedule_v2
    return SCHEDULE, PROGRAMS, get_dong_schedule


# ──────────────────────────────────────────────────────────────────────────────
# HELPER: 거리 계산 (Haversine)
# ──────────────────────────────────────────────────────────────────────────────
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))

# ──────────────────────────────────────────────────────────────────────────────
# HELPER: REGISTRATION DIALOG
# ──────────────────────────────────────────────────────────────────────────────
@st.dialog("프로그램 신청")
def registration_dialog(program: dict):
    st.markdown(f"**{program['name']}**")
    st.markdown(f"<span class='badge badge-gray'>{program['duration']}</span>", unsafe_allow_html=True)
    st.divider()

    name_input  = st.text_input("이름 *",  value=st.session_state.get("user_name", ""),  placeholder="홍길동")
    phone_input = st.text_input("연락처 *", value=st.session_state.get("user_phone", ""), placeholder="010-0000-0000")

    # Build date options from schedule
    dong = st.session_state.get("selected_dong", "")
    _, _, _get_sched = get_plan_data()
    sched = _get_sched(dong) if dong in DONG_SPOT else []
    if sched:
        date_options = [f"{DAY_KR[s['day']]} ({s['time']})" for s in sched]
    else:
        date_options = ["월요일 (오전 08:00–13:00)", "화요일 (오전 08:00–13:00)",
                        "수요일 (오전 08:00–13:00)", "목요일 (오전 08:00–13:00)"]

    selected_date = st.selectbox("방문 희망 요일 *", date_options)
    notes = st.text_area("기타 요청 사항 (선택)", placeholder="알레르기, 거동 불편 등 특이사항을 적어주세요.")

    col_submit, col_cancel = st.columns([2, 1])
    with col_submit:
        if st.button("신청 완료", type="primary", use_container_width=True):
            if not name_input.strip():
                st.warning("이름을 입력해 주세요.")
            elif not phone_input.strip():
                st.warning("연락처를 입력해 주세요.")
            else:
                st.success(f"✅ {name_input}님의 신청이 완료되었습니다!\n\n"
                           f"**프로그램**: {program['name']}\n\n"
                           f"**방문 일정**: {selected_date}")
                st.balloons()
    with col_cancel:
        if st.button("닫기", use_container_width=True):
            st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# LOGIN PAGE
# ──────────────────────────────────────────────────────────────────────────────
def show_login():
    st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("""
        <div style='text-align:center;margin-bottom:28px;'>
            <div style='font-size:2.8rem;'>🏪</div>
            <div style='font-size:1.7rem;font-weight:800;color:#1E3A5F;margin-top:4px;'>이동형 마음편의점</div>
            <div style='font-size:0.95rem;color:#6B7280;margin-top:6px;'>은평구 중장년 이동형 심리상담 서비스</div>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            st.markdown("#### 로그인")

            login_name = st.text_input("이름", placeholder="홍길동", key="login_name")
            phone      = st.text_input("연락처 (아이디)", placeholder="010-0000-0000", key="login_phone")
            password   = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", key="login_pw")

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            if st.button("로그인", type="primary", use_container_width=True):
                if not login_name.strip():
                    st.warning("이름을 입력해 주세요.")
                elif not phone.strip():
                    st.warning("연락처를 입력해 주세요.")
                elif not password.strip():
                    st.warning("비밀번호를 입력해 주세요.")
                else:
                    DEMO = {"name": "홍길동", "phone": "010-0000-0000",
                            "password": "0000", "gu": "은평구", "dong": "역촌동"}
                    if (login_name.strip() == DEMO["name"]
                            and phone.strip() == DEMO["phone"]
                            and password == DEMO["password"]):
                        st.session_state.user_name     = DEMO["name"]
                        st.session_state.user_phone    = DEMO["phone"]
                        st.session_state.user_gu       = DEMO["gu"]
                        st.session_state.user_dong     = DEMO["dong"]
                        st.session_state.selected_gu   = DEMO["gu"]
                        st.session_state.selected_dong = DEMO["dong"]
                        st.session_state.logged_in     = True
                        st.session_state.page          = "main"
                        st.rerun()
                    else:
                        st.error("이름, 연락처 또는 비밀번호가 일치하지 않습니다.")

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown("""
            <div style='text-align:center;font-size:0.88rem;color:#6B7280;'>
                처음 이용하시나요?
            </div>
            """, unsafe_allow_html=True)
            if st.button("이용 등록하기 →", use_container_width=True):
                st.session_state.page = "register"
                st.rerun()

        st.markdown("""
        <div style='text-align:center;font-size:0.8rem;color:#9CA3AF;margin-top:16px;'>
            이동형 마음편의점은 최초 1회 이용 등록 후 이용 가능합니다.<br>
            등록하신 정보는 프로그램 신청 시 자동으로 입력됩니다.
        </div>
        """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# REGISTER PAGE
# ──────────────────────────────────────────────────────────────────────────────
def show_register():
    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("""
        <div style='text-align:center;margin-bottom:24px;'>
            <div style='font-size:2rem;'>📝</div>
            <div style='font-size:1.5rem;font-weight:800;color:#1E3A5F;margin-top:4px;'>이용 등록</div>
            <div style='font-size:0.88rem;color:#6B7280;margin-top:4px;'>최초 1회 등록 후 서비스를 이용하실 수 있습니다</div>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            r_name  = st.text_input("이름 *", placeholder="홍길동")
            r_birth = st.text_input("생년월일 *", placeholder="예) 1965-03-15")
            r_phone = st.text_input("연락처 * (아이디로 사용)", placeholder="010-0000-0000")

            st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
            st.markdown("<span style='font-size:0.88rem;color:#374151;font-weight:600;'>거주지</span>", unsafe_allow_html=True)
            gu_list  = ["구를 선택하세요"] + list(DISTRICTS.keys())
            r_gu     = st.selectbox("구", gu_list, label_visibility="collapsed")
            if r_gu != "구를 선택하세요":
                dong_list = ["동을 선택하세요"] + DISTRICTS[r_gu]
                r_dong = st.selectbox("동", dong_list, label_visibility="collapsed")
            else:
                st.selectbox("동", ["동을 선택하세요"], disabled=True, label_visibility="collapsed")
                r_dong = "동을 선택하세요"

            st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)
            r_pw  = st.text_input("비밀번호 *", type="password", placeholder="6자 이상")
            r_pw2 = st.text_input("비밀번호 확인 *", type="password", placeholder="비밀번호를 다시 입력하세요")

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

            if st.button("등록 완료", type="primary", use_container_width=True):
                if not r_name.strip():
                    st.warning("이름을 입력해 주세요.")
                elif not r_birth.strip():
                    st.warning("생년월일을 입력해 주세요.")
                elif not r_phone.strip():
                    st.warning("연락처를 입력해 주세요.")
                elif r_gu == "구를 선택하세요":
                    st.warning("거주 구를 선택해 주세요.")
                elif r_dong == "동을 선택하세요":
                    st.warning("거주 동을 선택해 주세요.")
                elif not r_pw.strip() or len(r_pw) < 6:
                    st.warning("비밀번호를 6자 이상 입력해 주세요.")
                elif r_pw != r_pw2:
                    st.warning("비밀번호가 일치하지 않습니다.")
                else:
                    st.session_state.user_name  = r_name.strip()
                    st.session_state.user_birth = r_birth.strip()
                    st.session_state.user_phone = r_phone.strip()
                    st.session_state.user_gu    = r_gu
                    st.session_state.user_dong  = r_dong
                    st.session_state.logged_in  = True
                    st.session_state.selected_gu   = r_gu
                    st.session_state.selected_dong = r_dong
                    st.success(f"✅ {r_name}님, 이용 등록이 완료되었습니다!")
                    import time; time.sleep(1)
                    st.session_state.page = "main"
                    st.rerun()

        if st.button("← 로그인으로 돌아가기", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# USER PROFILE POPOVER (공통)
# ──────────────────────────────────────────────────────────────────────────────
def render_user_profile():
    """로그인 상태일 때 우측 상단에 환영 메시지 + 프로필 팝오버 표시"""
    if not st.session_state.get("logged_in"):
        return

    user_name = st.session_state.get("user_name", "")
    _, col_profile = st.columns([4, 1])
    with col_profile:
        label = f"👤 {user_name}님" if user_name else "👤 내 정보"
        with st.popover(label, use_container_width=True):
            if user_name:
                st.markdown(f"""
                <div style='background:#EFF6FF;border-radius:10px;padding:12px 14px;margin-bottom:12px;'>
                    <div style='font-size:1rem;font-weight:700;color:#1E3A5F;'>
                        {user_name}님, 환영합니다! 👋
                    </div>
                    <div style='font-size:0.82rem;color:#4A7FBF;margin-top:4px;'>
                        {st.session_state.get("user_phone","")}
                    </div>
                    <div style='font-size:0.82rem;color:#6B7280;margin-top:2px;'>
                        {st.session_state.get("user_gu","")} {st.session_state.get("user_dong","")}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("**거주지 변경**")

            gu_list = ["구를 선택하세요"] + list(DISTRICTS.keys())
            cur_gu  = st.session_state.get("user_gu", "")
            gu_idx  = gu_list.index(cur_gu) if cur_gu in gu_list else 0
            new_gu  = st.selectbox("구", gu_list, index=gu_idx,
                                   label_visibility="collapsed", key="prof_gu")

            if new_gu != "구를 선택하세요":
                dong_list  = ["동을 선택하세요"] + DISTRICTS[new_gu]
                cur_dong   = st.session_state.get("user_dong", "")
                same_gu    = (new_gu == st.session_state.get("user_gu", ""))
                dong_idx   = (dong_list.index(cur_dong)
                              if (same_gu and cur_dong in dong_list) else 0)
                new_dong   = st.selectbox("동", dong_list, index=dong_idx,
                                          label_visibility="collapsed", key="prof_dong")
            else:
                st.selectbox("동", ["동을 선택하세요"], disabled=True,
                             label_visibility="collapsed", key="prof_dong_dis")
                new_dong = "동을 선택하세요"

            if st.button("저장", type="primary", use_container_width=True, key="prof_save"):
                if new_gu == "구를 선택하세요":
                    st.warning("구를 선택해 주세요.")
                elif new_dong == "동을 선택하세요":
                    st.warning("동을 선택해 주세요.")
                else:
                    st.session_state.user_gu       = new_gu
                    st.session_state.user_dong     = new_dong
                    st.session_state.selected_gu   = new_gu
                    st.session_state.selected_dong = new_dong
                    st.success("저장되었습니다!")

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button("로그아웃", use_container_width=True, key="prof_logout"):
                for k in ["logged_in", "user_name", "user_phone",
                          "user_gu", "user_dong", "user_birth"]:
                    st.session_state[k] = "" if k != "logged_in" else False
                st.session_state.page = "login"
                st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# HOME PAGE
# ──────────────────────────────────────────────────────────────────────────────
def show_home():
    render_user_profile()
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Title block ──
    _, col_mid, _ = st.columns([1, 2.4, 1])
    with col_mid:
        st.markdown("<div class='page-title'>🏪 이동형 마음편의점</div>", unsafe_allow_html=True)
        st.markdown("<div class='page-tagline'>마음이 필요할 때, 우리가 찾아갑니다</div>", unsafe_allow_html=True)
        st.markdown("<div class='page-desc'>은평구 중장년 대상 이동형 심리상담 서비스<br>매주 찾아가는 마음 건강 편의점입니다.</div>",
                    unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # ── Selection form ──
        st.markdown("**📍 지역을 선택해 주세요**")

        gu_list = ["구를 선택하세요"] + list(DISTRICTS.keys())
        gu_idx = 0
        if st.session_state.selected_gu in DISTRICTS:
            gu_idx = gu_list.index(st.session_state.selected_gu)

        selected_gu = st.selectbox("구 (자치구)", gu_list, index=gu_idx, label_visibility="collapsed")

        if selected_gu and selected_gu != "구를 선택하세요":
            dong_list = ["동을 선택하세요"] + DISTRICTS[selected_gu]
            dong_idx = 0
            if (st.session_state.selected_dong in DISTRICTS.get(selected_gu, [])
                    and st.session_state.selected_gu == selected_gu):
                dong_idx = dong_list.index(st.session_state.selected_dong)
            selected_dong = st.selectbox("동 (행정동)", dong_list, index=dong_idx, label_visibility="collapsed")
        else:
            st.selectbox("동 (행정동)", ["동을 선택하세요"], disabled=True, label_visibility="collapsed")
            selected_dong = "동을 선택하세요"

        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        if st.button("입장하기 →", type="primary", use_container_width=True):
            if selected_gu == "구를 선택하세요":
                st.warning("구를 선택해 주세요.")
            elif selected_dong == "동을 선택하세요":
                st.warning("동을 선택해 주세요.")
            else:
                st.session_state.selected_gu = selected_gu
                st.session_state.selected_dong = selected_dong
                st.session_state.page = "main"
                st.rerun()

    # ── Feature preview cards ──
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    _, c1, c2, c3, _ = st.columns([0.5, 1, 1, 1, 0.5])
    feature_items = [
        (c1, "📅", "방문 일정", "매주 6개 동을 직접 찾아가는\n주간 스케줄을 확인하세요."),
        (c2, "📋", "프로그램", "심리상담부터 명상·원예 치료까지\n다양한 프로그램을 신청하세요."),
        (c3, "🤖", "AI 상담", "AI 챗봇에게 서비스 정보나\n마음 건강 관련 질문을 해보세요."),
    ]
    for col, icon, title, desc in feature_items:
        with col:
            st.markdown(f"""
            <div class='feature-card'>
                <div class='feature-icon'>{icon}</div>
                <div class='feature-title'>{title}</div>
                <div class='feature-desc'>{desc.replace(chr(10), '<br>')}</div>
            </div>
            """, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1: 방문 일정
# ──────────────────────────────────────────────────────────────────────────────
def render_visit_schedule(selected_gu, selected_dong):
    plan_sched, _, get_dong_sched_fn = get_plan_data()
    plan_v = st.session_state.get("plan_version", "1안")
    is_eunpyeong = (selected_gu == "은평구")
    in_service = (selected_dong in DONG_SPOT)

    if in_service:
        dong_sched = get_dong_sched_fn(selected_dong)
        if plan_v == "1안" and len(dong_sched) >= 2:
            st.markdown("""
            <div class='star-badge'>⭐ 주 2회 방문 지역</div>
            """, unsafe_allow_html=True)
        elif plan_v == "2안" and selected_dong in DONG_TRACK_V2:
            track = DONG_TRACK_V2[selected_dong]
            track_color = TRACK_COLORS_V2[track]
            st.markdown(
                f"<div style='display:inline-block;padding:3px 12px;border-radius:20px;"
                f"font-size:12px;font-weight:700;background:{track_color}22;"
                f"color:{track_color};border:1.5px solid {track_color};"
                f"margin-bottom:8px;'>{track} 트랙</div>",
                unsafe_allow_html=True,
            )

        for entry in dong_sched:
            day = entry["day"]
            color = DAY_COLORS.get(day, "#4A7FBF")
            spot = entry["spot_name"]
            time_str = entry["time"]
            st.markdown(f"""
            <div class='visit-card' style='background:#FAFCFF; border-left-color:{color};'>
                <span class='badge day-{day}'>{DAY_KR[day]}</span>
                <span class='badge badge-blue'>{time_str}</span>
                <div style='margin-top:10px;'>
                    <span style='font-size:1rem;font-weight:700;color:#1E3A5F;'>📍 {spot}</span>
                </div>
                <div style='font-size:0.85rem;color:#6B7280;margin-top:4px;'>{selected_dong}</div>
            </div>
            """, unsafe_allow_html=True)

    elif is_eunpyeong:
        st.markdown("""
        <div class='info-box'>
            ℹ️ 현재 해당 동은 시범 운영 대상 지역이 아닙니다.<br>
            내 위치를 허용하면 가장 가까운 서비스 지역 순서로 보여드립니다.
        </div>
        """, unsafe_allow_html=True)

        loc = streamlit_geolocation()
        user_lat = loc.get("latitude") if loc else None
        user_lon = loc.get("longitude") if loc else None

        # 거리 계산 후 정렬 (위치 허용 시) 또는 기본 순서
        dong_list_sorted = []
        for dong_name, (spot_name, lat, lon) in DONG_SPOT.items():
            sched_entries = get_dong_sched_fn(dong_name)
            dist = haversine_km(user_lat, user_lon, lat, lon) if (user_lat and user_lon) else None
            dong_list_sorted.append((dong_name, spot_name, sched_entries, dist))

        if user_lat and user_lon:
            dong_list_sorted.sort(key=lambda x: x[3])
            st.markdown("**📍 내 위치에서 가까운 서비스 지역 순서**")
        else:
            st.markdown("**📍 현재 서비스 운영 동 목록**")

        cols = st.columns(3)
        for i, (dong_name, spot_name, sched_entries, dist) in enumerate(dong_list_sorted):
            # 요일 + 시간대 뱃지 (방문 횟수만큼 줄 생성)
            sched_html = "".join([
                f"<div style='margin-top:5px;'>"
                f"<span class='badge badge-blue'>{DAY_KR[e['day']]}</span>"
                f"<span class='badge badge-gray'>{e['time']}</span>"
                f"</div>"
                for e in sched_entries
            ])
            dist_text = (
                f"<div style='margin-top:6px;'><span class='badge badge-teal'>📏 {dist*1000:.0f}m</span></div>"
                if dist is not None and dist < 1
                else f"<div style='margin-top:6px;'><span class='badge badge-teal'>📏 {dist:.1f}km</span></div>"
                if dist is not None
                else ""
            )
            rank_text = f"<span style='font-size:0.78rem;color:#9CA3AF;'>#{i+1}</span> " if (user_lat and user_lon) else ""
            with cols[i % 3]:
                st.markdown(f"""
                <div class='card-soft'>
                    {rank_text}<b>{dong_name}</b><br>
                    <span style='font-size:0.82rem;color:#6B7280;'>{spot_name}</span>
                    {sched_html}
                    {dist_text}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='warn-box'>
            🗺️ 이동형 마음편의점은 현재 <b>은평구</b>에서 시범 운영 중입니다.<br>
            은평구 내 6개 복합취약형 동을 매주 방문하여 심리상담 서비스를 제공합니다.
        </div>
        """, unsafe_allow_html=True)

    # ── Full weekly schedule table ──
    st.markdown("<div class='section-header'>📆 주간 전체 운영 일정</div>", unsafe_allow_html=True)
    for day, dong1, time1, dong2, time2 in plan_sched:
        color = DAY_COLORS[day]
        spot1 = DONG_SPOT[dong1][0] if dong1 in DONG_SPOT else dong1
        morning_div = (
            "<div style='flex:1;min-width:180px;'>"
            + f"<span class='badge badge-blue'>{time1}</span>"
            + "<div style='margin-top:6px;'>"
            + f"<b style='color:#1E3A5F;'>{dong1}</b>"
            + f"<span style='color:#6B7280;font-size:0.85rem;'> · {spot1}</span>"
            + "</div></div>"
        )
        if dong2:
            spot2 = DONG_SPOT[dong2][0] if dong2 in DONG_SPOT else dong2
            afternoon_div = (
                "<div style='flex:1;min-width:180px;'>"
                + f"<span class='badge badge-orange'>{time2}</span>"
                + "<div style='margin-top:6px;'>"
                + f"<b style='color:#1E3A5F;'>{dong2}</b>"
                + f"<span style='color:#6B7280;font-size:0.85rem;'> · {spot2}</span>"
                + "</div></div>"
            )
        else:
            afternoon_div = ""
        card_html = (
            f"<div class='card' style='border-left:4px solid {color}; padding:14px 20px;'>"
            + f"<span class='badge day-{day}' style='font-size:0.95rem;padding:4px 14px;'>{DAY_KR[day]}</span>"
            + "<div style='display:flex;gap:16px;margin-top:10px;flex-wrap:wrap;'>"
            + morning_div
            + afternoon_div
            + "</div></div>"
        )
        st.markdown(card_html, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2: 프로그램 — 헬퍼
# ──────────────────────────────────────────────────────────────────────────────
CAT_ICONS = {
    "상담":         "💬",
    "심리 검사":    "🧠",
    "취미 활동":    "🎨",
    "소그룹 활동":  "🎵",
    "개인형 프로그램": "🌱",
    "지역사회 활동":"🌍",
    "집단 프로그램":"👥",
    "정보 제공":    "📢",
    "신체·마음 연계":"🌿",
}

def _prog_card(prog, key_prefix="cat"):
    """프로그램 카드 HTML + 상세 expander + 신청 버튼 렌더링"""
    cap_text = f"{prog['capacity']}명" if prog["capacity"] else "인원 제한 없음"
    reg_badge = (
        "<span class='badge badge-orange'>사전 신청 필요</span>"
        if prog["requires_registration"]
        else "<span class='badge badge-green'>현장 참여 가능</span>"
    )
    sched = prog.get("schedule")
    if sched == "매일":
        sched_badge = "<span class='badge badge-purple'>매일 운영</span>"
    elif isinstance(sched, list):
        days_str = "·".join([f"{DAY_KR[e['day']]}" for e in sched])
        sched_badge = f"<span class='badge badge-blue'>{days_str}</span>"
    else:
        sched_badge = ""

    st.markdown(f"""
    <div class='prog-card' style='margin-bottom:4px;border-bottom-left-radius:4px;border-bottom-right-radius:4px;'>
        <div class='prog-name'>{prog['name']}</div>
        <div class='prog-desc' style='color:#6B7280;font-size:0.88rem;margin-bottom:8px;'>{prog['summary']}</div>
        <span class='badge badge-gray'>⏱ {prog['duration']}</span>
        <span class='badge badge-blue'>👤 {cap_text}</span>
        {reg_badge}
        {sched_badge}
        <div style='font-size:0.8rem;color:#9CA3AF;margin-top:6px;'>📌 {prog.get("note","")}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("자세히 보기"):
        for para in prog.get("description", "").split("\n\n"):
            st.markdown(para)
        if prog["requires_registration"]:
            if st.button("신청하기", key=f"reg_{key_prefix}_{prog['name']}"):
                registration_dialog(prog)

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)


def _build_day_map(schedule=None, programs=None):
    """요일별 → {dong: [prog, ...]} 매핑 생성"""
    if schedule is None:
        schedule = SCHEDULE
    if programs is None:
        programs = PROGRAMS
    # 구조: {day: {dong: [progs]}}
    day_map = {}
    for day, dong1, _, dong2, _ in schedule:
        day_map[day] = {dong1: []}
        if dong2:
            day_map[day][dong2] = []

    for prog in programs:
        sched = prog.get("schedule")
        if sched == "매일":
            for day, dongs in day_map.items():
                for dong in dongs:
                    dongs[dong].append(prog)
        elif isinstance(sched, list):
            for entry in sched:
                d, dong = entry["day"], entry["dong"]
                if d in day_map and dong in day_map[d]:
                    day_map[d][dong].append(prog)
    return day_map


# ──────────────────────────────────────────────────────────────────────────────
# TAB 2: 프로그램
# ──────────────────────────────────────────────────────────────────────────────
def render_programs(selected_dong):
    plan_sched, plan_progs, _ = get_plan_data()
    plan_v = st.session_state.get("plan_version", "1안")

    view = st.radio(
        "보기 방식",
        ["📅 요일별", "🗂 카테고리별"],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # ── 요일별 보기 ──────────────────────────────────────────────────────────
    if view == "📅 요일별":
        # 빠른 이동 네비게이션
        nav_html = "<div style='margin-bottom:14px;display:flex;flex-wrap:wrap;gap:4px;align-items:center;'>"
        nav_html += "<span style='font-size:0.82rem;color:#9CA3AF;margin-right:4px;'>바로가기</span>"
        for day, _, _, _, _ in plan_sched:
            color = DAY_COLORS[day]
            nav_html += (
                f"<a href='#prog-{day}' class='nav-btn' "
                f"style='border-color:{color};color:{color};background:#FAFCFF;'>"
                f"{DAY_KR[day]}</a>"
            )
        nav_html += "</div>"
        st.markdown(nav_html, unsafe_allow_html=True)

        day_map = _build_day_map(schedule=plan_sched, programs=plan_progs)
        for day, dong1, time1, dong2, time2 in plan_sched:
            st.markdown(f"<div id='prog-{day}'></div>", unsafe_allow_html=True)
            color = DAY_COLORS[day]
            day_badge_extra = ""
            if plan_v == "2안" and not dong2:
                day_badge_extra = "<span class='badge badge-purple' style='margin-left:8px;'>전일 집중</span>"
            st.markdown(
                f"<div class='section-header' style='border-color:{color};'>"
                f"<span class='badge day-{day}' style='font-size:1rem;padding:4px 14px;'>{DAY_KR[day]}</span>"
                f"{day_badge_extra}</div>",
                unsafe_allow_html=True,
            )

            if not dong2:
                # 전일 집중 — dong1만 전체 너비로 렌더링
                spot_name = DONG_SPOT[dong1][0] if dong1 in DONG_SPOT else dong1
                track = DONG_TRACK_V2.get(dong1, "")
                track_color = TRACK_COLORS_V2.get(track, "#4A7FBF")
                st.markdown(f"""
                <div style='background:#F7FAFF;border-radius:10px;padding:10px 14px;
                            border:1px solid #DDE9F7;margin-bottom:8px;'>
                    <span class='badge badge-purple'>{time1}</span>
                    <b style='color:#1E3A5F;margin-left:6px;'>{dong1}</b>
                    <span style='margin-left:8px;font-size:11px;font-weight:700;
                                 color:{track_color};'>{track} 트랙</span>
                    <div style='font-size:0.8rem;color:#9CA3AF;margin-top:2px;'>{spot_name}</div>
                </div>
                """, unsafe_allow_html=True)
                progs = day_map[day].get(dong1, [])
                if progs:
                    for prog in progs:
                        _prog_card(prog, key_prefix=f"{day}_{dong1}")
                else:
                    st.markdown(
                        "<div style='color:#9CA3AF;font-size:0.88rem;padding:8px 0;'>"
                        "등록된 프로그램이 없습니다.</div>",
                        unsafe_allow_html=True,
                    )
            else:
                col_am, col_pm = st.columns(2)
                for col, dong, time_str in [(col_am, dong1, time1), (col_pm, dong2, time2)]:
                    with col:
                        spot_name = DONG_SPOT[dong][0] if dong in DONG_SPOT else dong
                        time_badge_cls = "badge-blue" if "오전" in time_str else "badge-orange"
                        st.markdown(f"""
                        <div style='background:#F7FAFF;border-radius:10px;padding:10px 14px;
                                    border:1px solid #DDE9F7;margin-bottom:8px;'>
                            <span class='badge {time_badge_cls}'>{time_str}</span>
                            <b style='color:#1E3A5F;margin-left:6px;'>{dong}</b>
                            <div style='font-size:0.8rem;color:#9CA3AF;margin-top:2px;'>{spot_name}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        progs = day_map[day].get(dong, [])
                        if progs:
                            for prog in progs:
                                _prog_card(prog, key_prefix=f"{day}_{dong}")
                        else:
                            st.markdown(
                                "<div style='color:#9CA3AF;font-size:0.88rem;padding:8px 0;'>"
                                "등록된 프로그램이 없습니다.</div>",
                                unsafe_allow_html=True,
                            )

    # ── 카테고리별 보기 ───────────────────────────────────────────────────────
    else:
        categories: dict = {}
        for prog in plan_progs:
            categories.setdefault(prog["category"], []).append(prog)

        # 빠른 이동 네비게이션
        nav_html = "<div style='margin-bottom:14px;display:flex;flex-wrap:wrap;gap:4px;align-items:center;'>"
        nav_html += "<span style='font-size:0.82rem;color:#9CA3AF;margin-right:4px;'>바로가기</span>"
        for cat in categories:
            icon = CAT_ICONS.get(cat, "📌")
            anchor_id = f"prog-cat-{''.join(c for c in cat if c.isalnum())}"
            nav_html += f"<a href='#{anchor_id}' class='nav-btn'>{icon} {cat}</a>"
        nav_html += "</div>"
        st.markdown(nav_html, unsafe_allow_html=True)

        for cat, progs in categories.items():
            anchor_id = f"prog-cat-{''.join(c for c in cat if c.isalnum())}"
            st.markdown(f"<div id='{anchor_id}'></div>", unsafe_allow_html=True)
            icon = CAT_ICONS.get(cat, "📌")
            st.markdown(f"<div class='section-header'>{icon} {cat}</div>", unsafe_allow_html=True)
            for prog in progs:
                _prog_card(prog, key_prefix=f"cat_{cat}")

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3: 노선도
# ──────────────────────────────────────────────────────────────────────────────
def render_map(selected_dong):
    plan_sched, _, _ = get_plan_data()
    plan_v = st.session_state.get("plan_version", "1안")

    coord_map_l = {dong: (lat, lon) for dong, (_, lat, lon) in DONG_SPOT.items()}

    # 동별 방문 요일 수집
    dong_days_map = {}
    for day, dong1, _, dong2, _ in plan_sched:
        dong_days_map.setdefault(dong1, set()).add(day)
        if dong2:
            dong_days_map.setdefault(dong2, set()).add(day)

    # ── 요일 필터 (radio를 nav-btn pill 스타일로) ──
    day_options = ["전체"] + [DAY_KR[d] for d in DAY_COLORS]
    day_colors  = ["#9CA3AF"] + list(DAY_COLORS.values())

    # nth-of-type 으로 label 요소만 카운트 (다른 요소에 밀리지 않음)
    color_rules = ""
    for i, color in enumerate(day_colors, start=1):
        color_rules += (
            f"div:has(#mf-anchor)~div div[role='radiogroup'] label:nth-of-type({i})"
            f"{{border-color:{color}!important;color:{color}!important;}}"
            f"div:has(#mf-anchor)~div div[role='radiogroup'] label:nth-of-type({i}) p"
            f"{{color:{color}!important;}}"
            f"div:has(#mf-anchor)~div div[role='radiogroup'] label:nth-of-type({i}):has(input:checked)"
            f"{{background:{color}!important;color:white!important;}}"
            f"div:has(#mf-anchor)~div div[role='radiogroup'] label:nth-of-type({i}):has(input:checked) p"
            f"{{color:white!important;}}"
        )

    st.markdown(f"""
    <style>
    /* ── 지도 요일 필터: nav-btn 과 동일한 스타일 ── */
    div:has(#mf-anchor)~div div[role="radiogroup"] {{
        display:flex!important; flex-wrap:wrap!important;
        gap:0!important; align-items:center!important;
    }}
    /* radio circle 숨김 */
    div:has(#mf-anchor)~div div[role="radiogroup"] label > div:first-child {{
        display:none!important;
    }}
    /* 텍스트 wrapper div 투명화 */
    div:has(#mf-anchor)~div div[role="radiogroup"] label > div:last-child {{
        display:contents!important;
    }}
    div:has(#mf-anchor)~div div[role="radiogroup"] label > div:last-child p {{
        margin:0!important; padding:0!important;
        font-size:13px!important; font-weight:600!important;
    }}
    /* label → nav-btn 과 동일한 수치 */
    div:has(#mf-anchor)~div div[role="radiogroup"] label {{
        display:inline-block!important;
        padding:5px 14px!important; border-radius:20px!important;
        border:1.5px solid!important; font-size:13px!important;
        font-weight:600!important; background:#FAFCFF!important;
        margin-right:4px!important; margin-bottom:6px!important;
        cursor:pointer!important;
        transition:background 0.15s,color 0.15s!important;
        text-decoration:none!important;
    }}
    {color_rules}
    </style>
    <div style='margin-bottom:6px;'>
      <span style='font-size:0.82rem;color:#9CA3AF;'>요일 선택</span>
    </div>
    <div id='mf-anchor'></div>
    """, unsafe_allow_html=True)

    sel_label = st.radio("요일", day_options, horizontal=True,
                         label_visibility="collapsed", key="map_day_filter")

    # 선택된 요일 → day code
    day_kr_rev = {v: k for k, v in DAY_KR.items()}
    sel_day = None if sel_label == "전체" else day_kr_rev[sel_label]

    m = folium.Map(
        location=[37.610, 126.920],
        zoom_start=13,
        tiles="CartoDB positron",
        attr="© CartoDB © OpenStreetMap contributors",
    )

    # ── 거점 마커 ──
    folium.Marker(
        location=HUB_COORD,
        popup=folium.Popup(f"<b>⭐ {HUB_NAME}</b><br>거점 센터", max_width=200),
        tooltip=HUB_NAME,
        icon=folium.Icon(color="darkblue", icon="star", prefix="fa"),
    ).add_to(m)

    # ── 정류장 마커 (필터 적용) ──
    for dong_name, (spot_name, lat, lon) in DONG_SPOT.items():
        # 요일 필터: 해당 요일에 방문하지 않는 동은 생략
        if sel_day is not None and sel_day not in dong_days_map.get(dong_name, set()):
            continue

        is_sel = (dong_name == selected_dong)
        if is_sel:
            cc, fc, r = "#DC2626", "#FCA5A5", 14
        elif plan_v == "2안":
            track = DONG_TRACK_V2.get(dong_name, "관계 회복")
            if track == "관계 회복":
                cc, fc, r = "#6366F1", "#C7D2FE", 10
            else:
                cc, fc, r = "#F59E0B", "#FDE68A", 10
        else:
            peak_type = PEAK.get(dong_name, "오전")
            if peak_type == "오전":
                cc, fc, r = "#0EA5E9", "#BAE6FD", 10
            else:
                cc, fc, r = "#F97316", "#FED7AA", 10

        _, _, _get_sched_map = get_plan_data()
        sched_entries = _get_sched_map(dong_name)
        visit_text = "<br>".join([f"{DAY_KR[e['day']]} {e['time']}" for e in sched_entries])
        popup_html = (
            f"<div style='font-family:sans-serif;min-width:140px;'>"
            f"<b>{dong_name}</b><br><span style='color:#666;font-size:11px;'>{spot_name}</span>"
            f"<br><hr style='margin:4px 0;'>{visit_text}</div>"
        )
        folium.CircleMarker(
            location=[lat, lon], radius=r, color=cc, fill=True,
            fill_color=fc, fill_opacity=0.85, weight=2.5,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{dong_name} | {spot_name}",
        ).add_to(m)
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=(f"<div style='font-size:10px;font-weight:bold;color:#1E3A5F;"
                      f"white-space:nowrap;margin-top:14px;margin-left:-20px;"
                      f"text-shadow:1px 1px 2px #fff,-1px -1px 2px #fff;'>{dong_name}</div>"),
                icon_size=(80, 20), icon_anchor=(40, 0),
            ),
        ).add_to(m)

    # ── 노선 (필터 적용) ──
    for day, dong1, _, dong2, _ in plan_sched:
        if sel_day is not None and day != sel_day:
            continue
        color = DAY_COLORS[day]
        c_hub = list(HUB_COORD)
        c1 = list(coord_map_l.get(dong1, HUB_COORD))
        folium.PolyLine([c_hub, c1], color=color, weight=3, opacity=0.85,
                        tooltip=f"{DAY_KR[day]} 오전: {dong1}").add_to(m)
        if dong2:
            c2 = list(coord_map_l.get(dong2, HUB_COORD))
            folium.PolyLine([c1, c2], color=color, weight=3, opacity=0.85,
                            tooltip=f"{DAY_KR[day]} 저녁: {dong2}").add_to(m)
            folium.PolyLine([c2, c_hub], color=color, weight=1.5, opacity=0.4,
                            dash_array="6 4", tooltip=f"{DAY_KR[day]} 귀환").add_to(m)
        else:
            folium.PolyLine([c1, c_hub], color=color, weight=1.5, opacity=0.4,
                            dash_array="6 4", tooltip=f"{DAY_KR[day]} 귀환").add_to(m)

    # ── 범례 (지도 좌측 하단 고정) ──
    day_legend_lines = "".join([
        f"<div style='display:flex;align-items:center;margin-bottom:5px;'>"
        f"<span style='display:inline-block;width:26px;height:3px;background:{color};"
        f"border-radius:2px;margin-right:7px;flex-shrink:0;'></span>"
        f"<span>{DAY_KR[dk]}</span></div>"
        for dk, color in DAY_COLORS.items()
    ])
    if plan_v == "2안":
        track_legend_lines = "".join([
            f"<div style='display:flex;align-items:center;margin-bottom:5px;'>"
            f"<span style='width:11px;height:11px;border-radius:50%;"
            f"background:{color}44;border:2px solid {color};"
            f"display:inline-block;margin-right:7px;flex-shrink:0;'></span>"
            f"<span>{track}</span></div>"
            for track, color in TRACK_COLORS_V2.items()
        ])
        marker_section = f"""
      <hr style="margin:8px 0;border:none;border-top:1px solid #eee;">
      <b style="font-size:11px;color:#6B7280;display:block;margin-bottom:6px;">거점 유형</b>
      {track_legend_lines}
      <div style="display:flex;align-items:center;">
        <span style="width:11px;height:11px;border-radius:50%;background:#FCA5A5;
          border:2px solid #DC2626;display:inline-block;margin-right:7px;flex-shrink:0;"></span>현재 선택 동
      </div>"""
    else:
        marker_section = """
      <hr style="margin:8px 0;border:none;border-top:1px solid #eee;">
      <div style="display:flex;align-items:center;margin-bottom:5px;">
        <span style="width:11px;height:11px;border-radius:50%;background:#BAE6FD;
          border:2px solid #0EA5E9;display:inline-block;margin-right:7px;flex-shrink:0;"></span>오전 방문 동
      </div>
      <div style="display:flex;align-items:center;margin-bottom:5px;">
        <span style="width:11px;height:11px;border-radius:50%;background:#FED7AA;
          border:2px solid #F97316;display:inline-block;margin-right:7px;flex-shrink:0;"></span>저녁 방문 동
      </div>
      <div style="display:flex;align-items:center;">
        <span style="width:11px;height:11px;border-radius:50%;background:#FCA5A5;
          border:2px solid #DC2626;display:inline-block;margin-right:7px;flex-shrink:0;"></span>현재 선택 동
      </div>"""
    legend_html = f"""
    <div style="position:fixed;bottom:30px;left:30px;z-index:9999;
                background:white;padding:12px 16px;border-radius:10px;
                box-shadow:0 2px 10px rgba(0,0,0,0.18);
                font-family:sans-serif;font-size:12px;color:#374151;">
      <b style="font-size:13px;color:#1E3A5F;display:block;margin-bottom:8px;">노선 범례</b>
      {day_legend_lines}
      {marker_section}
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, use_container_width=True, height=520)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4: 챗봇
# ──────────────────────────────────────────────────────────────────────────────
def build_system_prompt():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    weekday_kr = ["월요일","화요일","수요일","목요일","금요일","토요일","일요일"][now.weekday()]
    now_str = f"{now.year}년 {now.month}월 {now.day}일 {weekday_kr} {now.strftime('%H:%M')}"

    user_name  = st.session_state.get("user_name", "")
    user_phone = st.session_state.get("user_phone", "")
    user_gu    = st.session_state.get("user_gu", "")
    user_dong  = st.session_state.get("user_dong", "")
    user_info  = f"- 이름: {user_name}\n- 연락처: {user_phone}\n- 거주지: {user_gu} {user_dong}" if user_name else "- (비로그인 상태)"

    schedule_text = "\n".join([
        f"  {DAY_KR[d]}: {dong1}({time1}) → {dong2}({time2})"
        for d, dong1, time1, dong2, time2 in SCHEDULE
    ])
    spots_text = "\n".join([
        f"  {dong}: {name} (위도 {lat}, 경도 {lon})"
        for dong, (name, lat, lon) in DONG_SPOT.items()
    ])
    programs_text = "\n".join([
        f"  [{p['category']}] {p['name']} ({p['duration']}, {('사전신청 필요' if p['requires_registration'] else '현장참여')})"
        for p in PROGRAMS
    ])

    return f"""당신은 '이동형 마음편의점' 서비스의 친절한 안내 챗봇입니다.
은평구 중장년 주민들을 위한 이동형 심리상담 서비스를 안내해 드립니다.

## 현재 이용자 정보
{user_info}
이용자의 이름을 알고 있다면 대화 중 자연스럽게 이름을 불러주세요. (예: "홍길동님, ...")

## 현재 날짜 및 시간
지금은 {now_str}입니다. 날짜·요일·시간과 관련된 질문에는 이 정보를 기준으로 답변하세요.
(예: "오늘 방문하나요?", "이번 주 언제 오나요?", "지금 운영 중인가요?" 등)

## 서비스 개요
- 거점: {HUB_NAME} (위도 {HUB_COORD[0]}, 경도 {HUB_COORD[1]})
- 운영 지역: 은평구 내 6개 복합취약형 동 (불광2동, 갈현1동, 갈현2동, 구산동, 역촌동, 응암3동)
- 운영 시간: 월~목 오전 08:00–13:00 / 오후 14:00–18:00

## 주간 방문 일정
{schedule_text}

## 방문 장소
{spots_text}

## 제공 프로그램
{programs_text}

## 안내 지침
- 따뜻하고 친절한 말투를 사용하세요.
- 마음 건강에 대한 질문에 공감하며 답변하세요.
- 서비스 외 지역 이용자에게는 현재 은평구 시범 운영 중임을 안내하세요.
- 전문 심리 치료가 필요한 경우, 정신건강 위기상담전화(1577-0199)를 안내하세요.
- 모든 답변은 한국어로 작성하세요.
"""


def render_chatbot():
    st.markdown("""
    <div class='chat-system-msg'>
        🤖 안녕하세요! 이동형 마음편의점 안내 챗봇입니다.<br>
        방문 일정, 프로그램, 신청 방법 등 궁금하신 점을 질문해 주세요.
    </div>
    """, unsafe_allow_html=True)

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Clear button
    if st.session_state.chat_history:
        if st.button("🗑 대화 초기화", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

    # Chat input
    user_input = st.chat_input("질문을 입력하세요...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("답변을 생성하는 중..."):
                try:
                    api_key = st.secrets["UPSTAGE_API_KEY"]
                    client = OpenAI(
                        api_key=api_key,
                        base_url="https://api.upstage.ai/v1",
                    )
                    messages = [{"role": "system", "content": build_system_prompt()}]
                    messages += [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.chat_history
                    ]
                    response = client.chat.completions.create(
                        model="solar-pro",
                        messages=messages,
                        stream=False,
                    )
                    answer = response.choices[0].message.content
                except Exception as e:
                    answer = f"죄송합니다. 일시적인 오류가 발생했습니다.\n\n`{type(e).__name__}: {e}`"

            answer = answer.replace("~", "–")

            st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

# ──────────────────────────────────────────────────────────────────────────────
# MAIN PAGE
# ──────────────────────────────────────────────────────────────────────────────
def show_main():
    selected_gu   = st.session_state.selected_gu
    selected_dong = st.session_state.selected_dong
    is_eunpyeong  = (selected_gu == "은평구")

    # ── Header ──
    render_user_profile()

    # 1안/2안 토글 — 별도 줄 (위치명과 같은 행에 있으면 레이아웃 혼잡)
    plan_v = st.session_state.get("plan_version", "1안")
    col_p1, col_p2, _ = st.columns([0.7, 0.7, 4.6])
    with col_p1:
        if st.button(
            "동선 1안",
            type="primary" if plan_v == "1안" else "secondary",
            use_container_width=True,
            key="toggle_plan1",
        ):
            st.session_state.plan_version = "1안"
            st.rerun()
    with col_p2:
        if st.button(
            "동선 2안",
            type="primary" if plan_v == "2안" else "secondary",
            use_container_width=True,
            key="toggle_plan2",
        ):
            st.session_state.plan_version = "2안"
            st.rerun()

    col_loc, col_btns = st.columns([3, 2])
    with col_loc:
        st.markdown(
            f"<div style='font-size:1.6rem;font-weight:700;color:#1E3A5F;margin-bottom:0;line-height:1.3;'>📍 {selected_gu} {selected_dong}</div>",
            unsafe_allow_html=True,
        )
    with col_btns:
        # 동네 변경은 우측 상단 프로필 팝오버에서 가능 — 별도 버튼 미표시
        # (show_home() 코드는 보존, 필요 시 아래 주석 해제하여 활성화)
        # if st.button("🔄 동네 변경", key="back_home"):
        #     st.session_state.page = "home"; st.rerun()
        if is_eunpyeong:
            if st.button("📊 선정 근거", key="go_analysis"):
                st.session_state.page = "analysis"
                st.rerun()

    st.markdown("<a id='page-top'></a>", unsafe_allow_html=True)
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown(BACK_TO_TOP_HTML, unsafe_allow_html=True)

    # 노선도 탭(인덱스 2)에서 ↑ 버튼 자동 숨김
    components.html("""<script>
    (function(){
        if(window._btWatcher) clearInterval(window._btWatcher);
        window._btWatcher = setInterval(function(){
            try {
                var tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
                var activeIdx = -1;
                tabs.forEach(function(t,i){ if(t.getAttribute('aria-selected')==='true') activeIdx=i; });
                var btn = window.parent.document.getElementById('st-back-to-top');
                if(!btn) return;
                btn.style.display = (activeIdx === 2) ? 'none' : 'block';
            } catch(e) {}
        }, 400);
    })();
    </script>""", height=0)

    # ── Tabs ──
    tab1, tab2, tab3, tab4 = st.tabs(["📅 방문 일정", "📋 프로그램", "🗺️ 노선도", "🤖 챗봇"])

    with tab1:
        render_visit_schedule(selected_gu, selected_dong)

    with tab2:
        render_programs(selected_dong)

    with tab3:
        render_map(selected_dong)

    with tab4:
        render_chatbot()

# ──────────────────────────────────────────────────────────────────────────────
# ANALYSIS PAGE
# ──────────────────────────────────────────────────────────────────────────────
def show_analysis():
    render_user_profile()
    st.markdown("<a id='page-top'></a>", unsafe_allow_html=True)
    if st.button("← 메인으로 돌아가기", key="back_main"):
        st.session_state.page = "main"
        st.rerun()
    st.markdown(BACK_TO_TOP_HTML, unsafe_allow_html=True)

    st.markdown("<h1 style='color:#1E3A5F;'>📊 은평구 선정 근거</h1>", unsafe_allow_html=True)
    st.markdown("<hr class='soft-divider'>", unsafe_allow_html=True)

    # ── Section 1: 왜 은평구인가? ──
    st.markdown("<div class='section-header'>1. 왜 은평구인가?</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='info-box'>
        서울시 25개 자치구 중 마음편의점 미운영 구를 대상으로 분석한 결과,
        <b>은평구</b>가 복합취약형 사각지대 동 수에서 <b>1위(6개 동)</b>를 기록했습니다.
        고립지수와 생활인구를 함께 고려할 때 이동형 서비스의 필요성이 가장 높은 지역입니다.
    </div>
    """, unsafe_allow_html=True)

    gu_labels = [d["gu"] for d in GU_COMPARISON]
    gu_counts = [d["count"] for d in GU_COMPARISON]
    bar_colors = ["#1E3A5F" if g == "은평구" else "#93C5FD" for g in gu_labels]

    fig_gu = go.Figure(go.Bar(
        x=gu_counts[::-1],
        y=gu_labels[::-1],
        orientation="h",
        marker_color=bar_colors[::-1],
        text=gu_counts[::-1],
        textposition="outside",
        hovertemplate="%{y}: %{x}개 동<extra></extra>",
    ))
    fig_gu.update_layout(
        title="복합취약형 사각지대 동 수 (마음편의점 미운영 구, 상위 10개)",
        xaxis_title="동 수",
        height=380,
        margin=dict(l=10, r=40, t=50, b=10),
        plot_bgcolor="#FAFCFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="sans-serif", size=13, color="#1E3A5F"),
        xaxis=dict(gridcolor="#E5EAF2"),
    )
    st.plotly_chart(fig_gu, use_container_width=True)

    # ── Section 2: 고립지수란? ──
    st.markdown("<div class='section-header'>2. 고립지수란?</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='info-box'>
        고립지수는 <b>KT 통신 데이터</b>를 기반으로 개발된 지표로,
        4개 차원의 신호를 요인 분석(Factor Analysis)하여 산출합니다.
        값이 높을수록 사회적 고립 위험이 크다는 것을 의미합니다.
    </div>
    """, unsafe_allow_html=True)

    dim_cols = st.columns(4)
    dim_icons = ["💰", "🚶", "🏠", "📱"]
    for i, (col, dim) in enumerate(zip(dim_cols, DIMENSIONS)):
        with col:
            st.markdown(f"""
            <div class='dim-card'>
                <div style='font-size:1.8rem;margin-bottom:6px;'>{dim_icons[i]}</div>
                <div class='dim-name'>{dim['name']}</div>
                <div class='dim-desc'>{dim['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Section 3: 은평구 방문 우선순위 ──
    st.markdown("<div class='section-header'>3. 은평구 방문 우선순위</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='info-box'>
        <b>우선순위 점수 = 고립지수 × 총생활인구</b>로 계산하여 방문 빈도를 결정했습니다.
        역촌동은 가장 높은 점수와 함께 주 2회 방문 지역으로 지정되었습니다.
    </div>
    """, unsafe_allow_html=True)

    p_dongs  = [d["dong"]       for d in PRIORITY_DATA]
    p_scores = [d["score"]      for d in PRIORITY_DATA]
    p_iso    = [d["isolation"]  for d in PRIORITY_DATA]
    p_pop    = [d["population"] for d in PRIORITY_DATA]
    p_peak   = [d["peak"]       for d in PRIORITY_DATA]

    bar_clr = []
    for d in PRIORITY_DATA:
        if d["dong"] == "역촌동":
            bar_clr.append("#DC2626")
        elif d["peak"] == "오전":
            bar_clr.append("#0EA5E9")
        else:
            bar_clr.append("#F97316")

    fig_pri = go.Figure()
    fig_pri.add_trace(go.Bar(
        x=p_scores[::-1],
        y=p_dongs[::-1],
        orientation="h",
        marker_color=bar_clr[::-1],
        name="우선순위 점수",
        text=[f"{s:,}" for s in p_scores[::-1]],
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "점수: %{x:,}<br>"
            "<extra></extra>"
        ),
    ))
    fig_pri.update_layout(
        title="은평구 방문 우선순위 (고립지수 × 생활인구)",
        xaxis_title="우선순위 점수",
        height=380,
        margin=dict(l=10, r=60, t=50, b=10),
        plot_bgcolor="#FAFCFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="sans-serif", size=13, color="#1E3A5F"),
        xaxis=dict(gridcolor="#E5EAF2"),
    )
    st.plotly_chart(fig_pri, use_container_width=True)

    # Detail table
    import pandas as pd
    df = pd.DataFrame([{
        "동": d["dong"],
        "고립지수": f"{d['isolation']:.3f}",
        "총생활인구": f"{d['population']:,}",
        "우선순위 점수": f"{d['score']:,}",
        "방문 빈도": d["visits"],
        "방문 시간대": d["peak"],
    } for d in PRIORITY_DATA])
    st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Section 4: 주간 스케줄 도출 과정 ──
    st.markdown("<div class='section-header'>4. 주간 스케줄 도출 과정</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='info-box'>
        <b>스케줄 설계 원칙:</b><br>
        ① Jenks 자연분류(경제축 임계값 ≈0.41) 적용 → 6개 복합취약형 동 확정<br>
        ② 6개 동 × 1일 2거점 + 1·2순위(역촌·응암3) 추가 슬롯 = 총 8슬롯 → 주 4일 운영(월~목)<br>
        ③ 오전/저녁 방문 최적 시간대(PEAK)를 반영해 1일 2개 동 방문<br>
        ④ 최고 우선순위 역촌동은 화·목 2회 편성 (주 2회 방문)<br>
        ⑤ 거점(신사종합사회복지관)에서 출발·복귀하는 최단 이동 경로 고려<br>
        ⑥ 오전 방문 동(불광2동)은 상대적으로 이른 시간대 수요가 높은 동
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**최종 주간 운영 일정 (동선 1안)**")
    sched_df = pd.DataFrame([{
        "요일": DAY_KR[d],
        "오전 방문 동": dong1,
        "오전 방문 장소": DONG_SPOT[dong1][0] if dong1 in DONG_SPOT else "-",
        "오후 방문 동": dong2 if dong2 else "—",
        "오후 방문 장소": DONG_SPOT[dong2][0] if dong2 in DONG_SPOT else "-",
    } for d, dong1, _, dong2, _ in SCHEDULE])
    st.dataframe(sched_df, use_container_width=True, hide_index=True)

    # ── Section 5: 동선 2안 — 고립 차원 이원화 ──
    st.markdown("<hr class='soft-divider'>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>5. 동선 2안 — 고립 차원 이원화</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='info-box'>
        동선 1안이 <b>고립 규모(점수 크기)</b> 기준으로 방문 순번을 정했다면,
        동선 2안은 <b>고립의 성격</b>에 따라 6개 동을 두 트랙으로 나눠 운영합니다.<br><br>
        <b>분류 방법:</b> 사분면 X축(경제적 불안정성)과 Y축(사회적 연결 결핍)을 6개 동 내부에서
        z-score로 비교 → z_사회 ≥ z_경제면 <b style='color:#6366F1;'>관계 회복 트랙</b>,
        z_사회 &lt; z_경제면 <b style='color:#F59E0B;'>복지 연계 트랙</b>으로 분류
    </div>
    """, unsafe_allow_html=True)

    # 트랙 설명 카드 2개
    col_tr1, col_tr2 = st.columns(2)
    with col_tr1:
        st.markdown("""
        <div class='dim-card' style='border-color:#A5B4FC;'>
            <div style='font-size:1.4rem;margin-bottom:6px;'>🤝</div>
            <div class='dim-name' style='color:#4F46E5;'>관계 회복 트랙 (2개 동)</div>
            <div class='dim-desc'>사회적 연결 결핍이 상대적으로 더 심각한 동.<br>
            커뮤니티 모임, 소그룹 상담, 사회적 연결 프로그램 중점 운영. 역촌동은 전일 집중 배정.</div>
            <div style='margin-top:10px;font-size:0.82rem;color:#6366F1;font-weight:600;'>
                역촌동 · 불광2동
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_tr2:
        st.markdown("""
        <div class='dim-card' style='border-color:#FCD34D;'>
            <div style='font-size:1.4rem;margin-bottom:6px;'>🏥</div>
            <div class='dim-name' style='color:#D97706;'>복지 연계 트랙 (4개 동)</div>
            <div class='dim-desc'>경제적 불안정성이 상대적으로 더 심각한 동.<br>
            취업·의료·생활복지 서비스 연계 중점 운영.</div>
            <div style='margin-top:10px;font-size:0.82rem;color:#F59E0B;font-weight:600;'>
                응암3동 · 갈현1동 · 갈현2동 · 구산동
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # z_diff 수평 막대 차트
    track_sorted = sorted(TRACK_DATA_V2, key=lambda x: x["z_diff"])
    dongs_sorted = [d["dong"] for d in track_sorted]
    zdiffs_sorted = [d["z_diff"] for d in track_sorted]
    bar_clr_track = ["#6366F1" if d["track"] == "관계 회복" else "#F59E0B" for d in track_sorted]

    fig_zdiff = go.Figure(go.Bar(
        x=zdiffs_sorted,
        y=dongs_sorted,
        orientation="h",
        marker_color=bar_clr_track,
        text=[f"{v:+.2f}" for v in zdiffs_sorted],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>z_diff: %{x:+.2f}<extra></extra>",
    ))
    fig_zdiff.add_vline(x=0, line_width=1.5, line_dash="dash", line_color="#9CA3AF")
    fig_zdiff.update_layout(
        title="사회적 연결 결핍 z-score − 경제적 불안정성 z-score (z_diff)",
        xaxis_title="z_diff (양수: 사회 고립 우세 / 음수: 경제 불안정 우세)",
        height=360,
        margin=dict(l=10, r=60, t=50, b=10),
        plot_bgcolor="#FAFCFF",
        paper_bgcolor="#FFFFFF",
        font=dict(family="sans-serif", size=13, color="#1E3A5F"),
        xaxis=dict(gridcolor="#E5EAF2", zeroline=False),
    )
    st.plotly_chart(fig_zdiff, use_container_width=True)

    # 트랙 분류 상세 테이블
    track_df = pd.DataFrame([{
        "트랙":          d["track"],
        "동":            d["dong"],
        "고립지수":      f"{d['isolation']:.3f}",
        "사회적연결결핍": f"{d['social']:.3f}",
        "경제적불안정성": f"{d['economic']:.3f}",
        "z_diff":        f"{d['z_diff']:+.2f}",
    } for d in sorted(TRACK_DATA_V2, key=lambda x: (x["track"] != "관계 회복", -x["z_diff"]))])
    st.dataframe(track_df, use_container_width=True, hide_index=True)

    # ── Section 6: 동선 2안 주간 운영 일정 ──
    st.markdown("<div class='section-header'>6. 동선 2안 주간 운영 일정</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='info-box'>
        <b>설계 원칙:</b> 같은 트랙의 두 동을 하루에 묶어 동일 맥락 프로그램 연속 운영.<br>
        관계 회복 트랙 역촌동(1순위)은 1:1 깊은 상담을 위해 목요일 전일(08–18시) 집중 배정 (주 2회).<br>
        지리적 특징: 복지 연계 트랙 4개 동 중 갈현1·갈현2·구산은 북서 권역에 집중, 응암3동은 남쪽.
    </div>
    """, unsafe_allow_html=True)

    TRACK_COLOR_MAP = {"관계 회복": "#6366F1", "복지 연계": "#F59E0B"}
    DAY_KR_LOCAL = {"월": "월요일", "화": "화요일", "수": "수요일", "목": "목요일"}
    for row in SCHEDULE_V2_DISPLAY:
        tc = TRACK_COLOR_MAP[row["track"]]
        day_color = DAY_COLORS.get(row["day"], "#4A7FBF")
        is_fullday = row["afternoon"] == "—"
        afternoon_cell = (
            "<div style='flex:1;min-width:180px;'>"
            + "<span class='badge badge-gray'>전일 집중</span>"
            + "</div>"
        ) if is_fullday else (
            "<div style='flex:1;min-width:180px;'>"
            + f"<span class='badge badge-orange'>오후 14:00–18:00</span>"
            + f"<div style='margin-top:6px;'><b style='color:#1E3A5F;'>{row['afternoon']}</b></div>"
            + "</div>"
        )
        card = (
            f"<div class='card' style='border-left:4px solid {day_color};padding:14px 20px;'>"
            + f"<span class='badge day-{row['day']}' style='font-size:0.95rem;padding:4px 14px;'>{DAY_KR_LOCAL[row['day']]}</span>"
            + f"<span style='margin-left:8px;font-size:11px;font-weight:700;color:{tc};'>{row['track']} 트랙</span>"
            + "<div style='display:flex;gap:16px;margin-top:10px;flex-wrap:wrap;'>"
            + "<div style='flex:1;min-width:180px;'>"
            + f"<span class='badge badge-blue'>오전 08:00–13:00</span>"
            + f"<div style='margin-top:6px;'><b style='color:#1E3A5F;'>{row['morning']}</b></div>"
            + "</div>"
            + afternoon_cell
            + "</div></div>"
        )
        st.markdown(card, unsafe_allow_html=True)

    # 1안 vs 2안 비교 박스
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='warn-box'>
        <b>동선 1안 vs 동선 2안 비교</b><br>
        · <b>1안</b>: 고립지수 × 생활인구 <b>곱셈점수</b> 기준 순번 배정 — 고립 규모가 큰 동 우선 (역촌·응암3 주 2회)<br>
        · <b>2안</b>: <b>트랙 기반</b> 묶음 배정 — 같은 성격 프로그램 두 지역 연속 운영 (역촌 전일집중 주 2회)
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# ROUTER
# ──────────────────────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "login":
    show_login()
elif page == "register":
    show_register()
elif page == "home":
    show_home()
elif page == "main":
    show_main()
elif page == "analysis":
    show_analysis()
