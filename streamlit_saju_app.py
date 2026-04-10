"""
AI 명리학자 — LangGraph 조건부 분기 + Streamlit (일반 사주 전용)
실행: 프로젝트 루트에서  streamlit run streamlit_saju_app.py
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

import streamlit as st

from saju_agent_core import run_phase1, run_phase2_tikitaka_finish

st.set_page_config(
    page_title="오늘의 기운",
    page_icon="🌤️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# 한지·먹·청동 톤 — 가독 위주, 과한 장식 없음
st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;700&family=Noto+Sans+KR:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    .stApp {
        background: linear-gradient(165deg, #f7f4ee 0%, #ebe4d8 48%, #e8e2d6 100%);
    }
    [data-testid="stAppViewContainer"] > .main .block-container {
        max-width: 40rem;
        padding-top: 1.75rem;
        padding-bottom: 3rem;
    }
    [data-testid="stSidebarNav"] { display: none; }
    h1, h2, h3 {
        font-family: "Noto Serif KR", "Apple SD Gothic Neo", serif !important;
        font-weight: 700 !important;
        color: #1c1816 !important;
        letter-spacing: -0.03em;
    }
    h1 {
        font-size: 1.85rem !important;
        line-height: 1.35 !important;
        padding-bottom: 0.5rem;
        margin-bottom: 0.35rem !important;
        border-bottom: 1px solid rgba(92, 64, 51, 0.22);
    }
    h3 {
        font-size: 1.05rem !important;
        margin-top: 1.35rem !important;
        margin-bottom: 0.45rem !important;
        color: #3d3530 !important;
    }
    .stCaption, [data-testid="stCaption"] {
        font-family: "Noto Sans KR", sans-serif !important;
        color: #5c534c !important;
        font-size: 0.88rem !important;
        line-height: 1.55 !important;
    }
    /* span 제외: Streamlit 머티리얼 아이콘이 span + Material Symbols Rounded 인데,
       span까지 Noto로 덮으면 아이콘 대신 keyboard_double_arrow_right 같은 글자가 보임 */
    p, label, input, textarea {
        font-family: "Noto Sans KR", sans-serif !important;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown td, .stMarkdown th {
        font-family: "Noto Sans KR", sans-serif !important;
    }
    [data-testid="stIconMaterial"],
    [data-testid="stIconEmoji"] {
        font-family: "Material Symbols Rounded", sans-serif !important;
    }
    [data-testid="stTextInput"] label,
    [data-testid="stDateInput"] label {
        font-weight: 500 !important;
        color: #2d2825 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: none !important;
    }
    [data-testid="stButton"] button {
        font-family: "Noto Sans KR", sans-serif !important;
        font-weight: 500 !important;
        border-radius: 9999px !important;
        padding: 0.5rem 1.35rem !important;
        letter-spacing: -0.02em !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.15s ease;
    }
    [data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(165deg, #8a7f74 0%, #6b625a 52%, #5a534c 100%) !important;
        color: #fffdf9 !important;
        border: 1px solid rgba(255, 252, 248, 0.22) !important;
        box-shadow:
            0 2px 10px rgba(62, 54, 48, 0.12),
            0 1px 2px rgba(62, 54, 48, 0.06),
            inset 0 1px 0 rgba(255, 255, 255, 0.12);
    }
    [data-testid="stButton"] button[kind="primary"]:hover {
        opacity: 1;
        transform: translateY(-1px);
        box-shadow:
            0 6px 18px rgba(62, 54, 48, 0.14),
            0 2px 4px rgba(62, 54, 48, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.14);
    }
    [data-testid="stButton"] button[kind="secondary"] {
        background: rgba(255, 253, 248, 0.72) !important;
        color: #4d4540 !important;
        border: 1px solid rgba(77, 69, 64, 0.14) !important;
        box-shadow: 0 1px 6px rgba(62, 54, 48, 0.06);
    }
    [data-testid="stButton"] button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.88) !important;
        border-color: rgba(77, 69, 64, 0.2) !important;
        transform: translateY(-1px);
    }
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(92, 64, 51, 0.2), transparent) !important;
        margin: 1.75rem 0 !important;
    }
    div[data-baseweb="input"] input, div[data-baseweb="select"] {
        border-radius: 12px !important;
    }
    .saju-lede {
        font-family: "Noto Sans KR", sans-serif;
        font-size: 0.9rem;
        line-height: 1.65;
        color: #4a433c;
        margin: 0 0 1.25rem 0;
        padding: 0.65rem 0 0.85rem 0;
        border-left: 3px solid rgba(139, 125, 112, 0.55);
        padding-left: 0.9rem;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f2ede4 0%, #e8e2d6 100%) !important;
        border-right: 1px solid rgba(92, 64, 51, 0.12) !important;
    }
    div[data-testid="stAlert"] {
        border-radius: 14px !important;
        border: 1px solid rgba(107, 98, 90, 0.12) !important;
        background: rgba(255, 253, 248, 0.72) !important;
        box-shadow: 0 2px 12px rgba(62, 54, 48, 0.05);
    }
</style>
""",
    unsafe_allow_html=True,
)

# 만세력·규칙 엔진 JSON, LangGraph 상태 일부 — 개발·검증용 (기본 숨김)
st.sidebar.checkbox(
    "디버그: 원시 JSON / 그래프 스냅샷",
    value=False,
    key="show_saju_debug",
    help="삼주·일진·hard_verdict 등 도구 출력과 그래프 상태를 볼 때만 켜세요.",
)

MIN_BIRTH = date(1900, 1, 1)
ADULT_AGE = 19


def _max_birth_date_for_adult() -> date:
    t = date.today()
    try:
        return t.replace(year=t.year - ADULT_AGE)
    except ValueError:
        return t.replace(year=t.year - ADULT_AGE, month=2, day=28)


def _default_birth() -> date:
    sample = date(1990, 5, 20)
    hi = _max_birth_date_for_adult()
    if sample <= hi:
        return sample
    return hi


def _init_dates() -> None:
    mx = _max_birth_date_for_adult()
    if "birth_pick" not in st.session_state:
        st.session_state.birth_pick = _default_birth()
    else:
        b = st.session_state.birth_pick
        if b < MIN_BIRTH or b > mx:
            st.session_state.birth_pick = max(MIN_BIRTH, min(b, mx))


def _snapshot_for_debug(state: Dict[str, Any]) -> Dict[str, Any]:
    keys = (
        "birth_date",
        "target_date",
        "hard_verdict",
        "final_branch",
        "tikitaka_question",
        "user_followup_text",
        "verdict_line",
        "rule_engine",
    )
    return {k: state.get(k) for k in keys if k in state}


def _render_result(state: Dict[str, Any], *, show_facts: bool) -> None:
    st.success(state.get("verdict_line", "오늘의 판"))
    st.markdown("### 요약")
    st.info(state.get("summary_md", ""))
    body = (state.get("analysis_md") or "").strip()
    if not body:
        body = state.get("advice_md", "")
    st.markdown("### 풀이")
    st.markdown(body or "풀이를 불러오지 못했습니다. 다시 시도해 주세요.")
    adv = (state.get("advice_md") or "").strip()
    if adv and adv != body.strip():
        st.markdown("### 오늘의 실천")
        st.markdown(adv)
    if show_facts and state.get("facts_md"):
        st.markdown("---")
        st.markdown("#### 시스템 팩트(참고)")
        st.markdown(state.get("facts_md", ""))


_init_dates()

st.title("오늘의 기운")
st.markdown(
    '<p class="saju-lede">연·월·일주와 오늘 일진, 충·합은 규칙 엔진이 정합니다. '
    "그 위에 얹는 말풍선만 생성 AI입니다. 놀이로 보시면 됩니다.</p>",
    unsafe_allow_html=True,
)

_max_birth = _max_birth_date_for_adult()
_today = date.today()

st.date_input(
    "양력 생년월일",
    key="birth_pick",
    format="YYYY-MM-DD",
    min_value=MIN_BIRTH,
    max_value=_max_birth,
    help=f"만 {ADULT_AGE}세 이상(생일 상한: {_max_birth.isoformat()})",
)
st.caption(f"기준일: **KST {_today.isoformat()}** (오늘)")

birth: date = st.session_state.birth_pick

st.text_input("출생 시각 (추후)", value="—", disabled=True)

if st.button("오늘 풀이 보기", type="primary"):
    st.session_state.pop("phase1", None)
    st.session_state.pop("final_state", None)
    target = date.today()
    use_mcp = False
    gender_mcp = 1
    spin_msg = "풀이 짓는 중…"
    with st.spinner(spin_msg):
        try:
            st.session_state.phase1 = run_phase1(
                birth.isoformat(),
                target.isoformat(),
                use_mcp=use_mcp,
                gender=gender_mcp,
            )
        except Exception as e:
            st.error(f"실행 실패: {e}")
            st.stop()
    st.rerun()

phase1: Optional[Dict[str, Any]] = st.session_state.get("phase1")

if phase1:
    if st.session_state.get("show_saju_debug"):
        raw = phase1.get("raw_tool_json", {})
        with st.expander("원시 JSON / 그래프 스냅샷 (디버그)"):
            st.json(raw)
            st.json(_snapshot_for_debug(phase1))

    final_state: Optional[Dict[str, Any]] = st.session_state.get("final_state")
    show_facts_main = False

    if final_state:
        _render_result(final_state, show_facts=show_facts_main)
    elif phase1.get("tikitaka_question") and not phase1.get("summary_md"):
        st.warning("오늘은 판이 갈리는 지점이에요. 한 가지만 골라 주세요.")
        st.markdown(f"**{phase1['tikitaka_question']}**")
        ans = st.text_input("답변", key="tikitaka_ans")
        if st.button("반영하기"):
            if not (ans or "").strip():
                st.error("답을 입력해 주세요.")
            else:
                with st.spinner("반영하는 중…"):
                    try:
                        st.session_state.final_state = run_phase2_tikitaka_finish(phase1, ans.strip())
                    except Exception as e:
                        st.error(f"실패: {e}")
                st.rerun()
    else:
        _render_result(phase1, show_facts=show_facts_main)

if st.button("처음부터", type="secondary"):
    for k in ("phase1", "final_state"):
        st.session_state.pop(k, None)
    st.rerun()

st.markdown("---")
st.caption(
    "엔터테인먼트입니다. 의학·법률·재무 등 중요한 판단의 근거로 쓰지 마세요."
)
