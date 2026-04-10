"""
AI 사주 풀이 — LangGraph + Streamlit
실행: streamlit run streamlit_saju_app.py
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

import streamlit as st

from saju_agent_core import run_phase1, run_phase2_tikitaka_finish

# ── 오행 매핑 ──
GAN_ELEMENT = {
    "甲": "wood", "乙": "wood",
    "丙": "fire", "丁": "fire",
    "戊": "earth", "己": "earth",
    "庚": "metal", "辛": "metal",
    "壬": "water", "癸": "water",
}
ZHI_ELEMENT = {
    "子": "water", "丑": "earth", "寅": "wood", "卯": "wood",
    "辰": "earth", "巳": "fire", "午": "fire", "未": "earth",
    "申": "metal", "酉": "metal", "戌": "earth", "亥": "water",
}
ELEMENT_KR = {"wood": "목", "fire": "화", "earth": "토", "metal": "금", "water": "수"}
ELEMENT_EMOJI = {"wood": "🌿", "fire": "🔥", "earth": "🪨", "metal": "⚙️", "water": "💧"}
ELEMENT_COLOR = {
    "wood": "#4ade80", "fire": "#f87171",
    "earth": "#fbbf24", "metal": "#94a3b8", "water": "#60a5fa",
}

GAN_KR = {
    "甲": "갑", "乙": "을", "丙": "병", "丁": "정", "戊": "무",
    "己": "기", "庚": "경", "辛": "신", "壬": "임", "癸": "계",
}
ZHI_KR = {
    "子": "자", "丑": "축", "寅": "인", "卯": "묘", "辰": "진", "巳": "사",
    "午": "오", "未": "미", "申": "신", "酉": "유", "戌": "술", "亥": "해",
}

st.set_page_config(
    page_title="오늘의 사주",
    page_icon="🔮",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ──
st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    :root {
        --bg: #13111a;
        --card: #1e1b2e;
        --card-light: #262339;
        --text: #eee8f5;
        --muted: #9a92b0;
        --accent: #a78bfa;
        --accent2: #c084fc;
        --accent-soft: rgba(167, 139, 250, 0.12);
        --accent-glow: rgba(167, 139, 250, 0.25);
        --positive: #4ade80;
        --negative: #f87171;
        --warm: rgba(251, 191, 36, 0.1);
        --line: rgba(255,255,255,0.06);
        --radius: 16px;
        --shadow: 0 4px 30px rgba(0,0,0,0.3);
    }

    .stApp {
        background: var(--bg) !important;
    }
    [data-testid="stAppViewContainer"] > .main {
        background: var(--bg);
    }
    [data-testid="stAppViewContainer"] > .main .block-container {
        max-width: 28rem;
        padding: 1.5rem 1.25rem 2rem 1.25rem;
        background: transparent;
        margin: 0 auto;
    }
    [data-testid="stSidebarNav"] { display: none; }
    [data-testid="stSidebar"] {
        background: var(--card) !important;
        border-right: 1px solid var(--line) !important;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label {
        color: var(--text) !important;
    }

    /* 타이포그래피 */
    h1, h2, h3, p, label, input, textarea, span, div,
    .stMarkdown, .stMarkdown p, .stMarkdown li {
        font-family: "Noto Sans KR", sans-serif !important;
        color: var(--text);
    }
    h1 { font-size: 1.5rem !important; font-weight: 800 !important; margin: 0 !important; padding: 0 !important; border: none !important; }
    h2 { font-size: 1.1rem !important; font-weight: 700 !important; margin-top: 1rem !important; }
    h3 { font-size: 0.95rem !important; font-weight: 600 !important; margin-top: 0.75rem !important; }
    .stCaption, [data-testid="stCaption"] {
        color: var(--muted) !important;
        font-size: 0.78rem !important;
    }

    /* 라벨 */
    [data-testid="stTextInput"] label,
    [data-testid="stDateInput"] label,
    [data-testid="stRadio"] label {
        font-weight: 500 !important;
        color: var(--muted) !important;
        font-size: 0.82rem !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] { border: none !important; }

    /* 인풋 */
    div[data-baseweb="input"] input, div[data-baseweb="select"] {
        border-radius: 12px !important;
        border-color: var(--line) !important;
        background: var(--card) !important;
        color: var(--text) !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-soft) !important;
    }

    /* 버튼 */
    [data-testid="stButton"] button {
        font-family: "Noto Sans KR", sans-serif !important;
        font-weight: 600 !important;
        border-radius: 14px !important;
        padding: 0.65rem 1.5rem !important;
        transition: all 0.2s ease;
        min-height: 48px;
        width: 100%;
    }
    [data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #7c6cf0 0%, #a78bfa 50%, #c084fc 100%) !important;
        color: #fff !important;
        border: none !important;
        box-shadow: 0 4px 20px var(--accent-glow);
        font-size: 0.95rem !important;
    }
    [data-testid="stButton"] button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(167, 139, 250, 0.4);
    }
    [data-testid="stButton"] button[kind="secondary"] {
        background: var(--card) !important;
        color: var(--muted) !important;
        border: 1px solid var(--line) !important;
        font-weight: 400 !important;
        font-size: 0.82rem !important;
        min-height: 40px;
    }
    [data-testid="stButton"] button[kind="secondary"]:hover {
        background: var(--card-light) !important;
        color: var(--text) !important;
    }

    hr { border: none !important; height: 1px !important; background: var(--line) !important; margin: 1.25rem 0 !important; }

    /* 알럿 */
    div[data-testid="stAlert"] {
        border-radius: var(--radius) !important;
        border: 1px solid var(--line) !important;
        background: var(--card) !important;
    }
    div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p { color: var(--text) !important; }
    div[data-testid="stAlert"] div[role="alert"] { background: transparent !important; }

    /* ===== 커스텀 컴포넌트 ===== */

    /* 히어로 */
    .hero {
        text-align: center;
        padding: 2rem 0 1.5rem 0;
    }
    .hero-emoji { font-size: 3rem; display: block; margin-bottom: 0.6rem; }
    .hero-title {
        font-size: 1.75rem; font-weight: 800;
        background: linear-gradient(135deg, #a78bfa, #c084fc, #f0abfc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0.25rem 0;
    }
    .hero-sub {
        font-size: 0.85rem; color: var(--muted); font-weight: 300;
        margin: 0.3rem 0 0 0;
    }

    /* 입력 카드 */
    .input-card {
        background: var(--card);
        border-radius: 20px;
        padding: 1.5rem 1.25rem;
        margin: 1rem 0;
        border: 1px solid var(--line);
    }
    .input-label {
        font-size: 0.78rem; font-weight: 500; color: var(--muted);
        margin-bottom: 0.5rem; letter-spacing: 0.02em;
    }

    /* 결과 헤더 */
    .result-hero {
        text-align: center;
        padding: 1.25rem 0;
        margin-bottom: 0.5rem;
    }
    .result-hero-emoji { font-size: 2.5rem; display: block; margin-bottom: 0.3rem; }
    .result-hero-date {
        font-size: 1.1rem; font-weight: 700; color: var(--text);
    }
    .result-hero-birth {
        font-size: 0.8rem; color: var(--muted); margin-top: 0.15rem;
    }

    /* 사주 기둥 */
    .pillars-wrap {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 1rem 0;
    }
    .pillar {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 0.7rem 0;
        width: 72px;
        text-align: center;
    }
    .pillar-label {
        font-size: 0.65rem; color: var(--muted); font-weight: 500;
        margin-bottom: 0.4rem; letter-spacing: 0.05em;
    }
    .pillar-gan {
        font-size: 1.3rem; font-weight: 700; line-height: 1.2;
    }
    .pillar-zhi {
        font-size: 1.3rem; font-weight: 700; line-height: 1.2;
        margin-top: 0.15rem;
    }
    .pillar-kr {
        font-size: 0.65rem; color: var(--muted); margin-top: 0.25rem;
    }
    .pillar-elem {
        font-size: 0.6rem; margin-top: 0.2rem; font-weight: 500;
    }
    .pillar.today {
        border-color: var(--accent);
        box-shadow: 0 0 16px var(--accent-soft);
        background: linear-gradient(180deg, var(--card-light), var(--card));
    }

    /* 충합 태그 */
    .tags-wrap {
        display: flex; flex-wrap: wrap; justify-content: center;
        gap: 6px; margin: 0.75rem 0;
    }
    .tag {
        font-size: 0.72rem; font-weight: 600;
        padding: 0.3rem 0.65rem;
        border-radius: 20px;
        display: inline-flex; align-items: center; gap: 4px;
    }
    .tag-chong {
        background: rgba(248, 113, 113, 0.12); color: #f87171;
        border: 1px solid rgba(248, 113, 113, 0.2);
    }
    .tag-he {
        background: rgba(74, 222, 128, 0.12); color: #4ade80;
        border: 1px solid rgba(74, 222, 128, 0.2);
    }

    /* verdict 배너 */
    .verdict-banner {
        text-align: center;
        padding: 1rem;
        border-radius: var(--radius);
        margin: 0.75rem 0;
        font-weight: 700;
        font-size: 1rem;
        line-height: 1.5;
    }
    .verdict-lucky {
        background: linear-gradient(135deg, rgba(74,222,128,0.1), rgba(167,139,250,0.1));
        color: var(--positive);
        border: 1px solid rgba(74,222,128,0.15);
    }
    .verdict-unlucky {
        background: linear-gradient(135deg, rgba(248,113,113,0.1), rgba(251,191,36,0.08));
        color: var(--negative);
        border: 1px solid rgba(248,113,113,0.15);
    }
    .verdict-neutral {
        background: var(--accent-soft);
        color: var(--accent);
        border: 1px solid rgba(167,139,250,0.15);
    }

    /* 점수 게이지 */
    .score-wrap {
        display: flex; align-items: center; justify-content: center;
        gap: 8px; margin: 0.6rem 0;
    }
    .score-bar-bg {
        width: 140px; height: 6px; background: var(--card-light);
        border-radius: 3px; overflow: hidden; position: relative;
    }
    .score-bar-fill {
        height: 100%; border-radius: 3px;
        transition: width 0.5s ease;
    }
    .score-label {
        font-size: 0.72rem; color: var(--muted); font-weight: 500;
        min-width: 28px; text-align: center;
    }
    .score-val {
        font-size: 0.85rem; font-weight: 700;
    }

    /* 결과 카드 */
    .result-section {
        background: var(--card);
        border-radius: var(--radius);
        padding: 1.15rem 1.1rem;
        margin: 0.6rem 0;
        border: 1px solid var(--line);
    }
    .section-label {
        font-size: 0.7rem; font-weight: 600; color: var(--accent);
        letter-spacing: 0.06em; text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    .section-body {
        font-size: 0.88rem; line-height: 1.7; color: var(--text);
    }
    .section-body p { margin: 0.4rem 0 !important; }

    /* 오행 분포 */
    .elem-dist {
        display: flex; justify-content: center; gap: 12px;
        margin: 0.75rem 0;
    }
    .elem-item {
        text-align: center; min-width: 44px;
    }
    .elem-emoji { font-size: 1.2rem; }
    .elem-name { font-size: 0.68rem; color: var(--muted); margin-top: 0.15rem; }
    .elem-count {
        font-size: 0.85rem; font-weight: 700; margin-top: 0.1rem;
    }

    /* 푸터 */
    .footer {
        text-align: center; font-size: 0.7rem; color: #555;
        margin-top: 1.5rem; padding-top: 0.75rem;
        border-top: 1px solid var(--line);
    }

    /* 티키타카 질문 카드 */
    .question-card {
        background: linear-gradient(135deg, var(--card-light), var(--card));
        border: 1px solid var(--accent);
        border-radius: var(--radius);
        padding: 1.25rem;
        margin: 0.75rem 0;
        text-align: center;
        box-shadow: 0 0 20px var(--accent-soft);
    }
    .question-icon { font-size: 1.5rem; margin-bottom: 0.4rem; }
    .question-text {
        font-size: 0.95rem; font-weight: 600; color: var(--text);
        line-height: 1.6;
    }
    .question-hint {
        font-size: 0.75rem; color: var(--muted); margin-top: 0.4rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ── 디버그 사이드바 ──
st.sidebar.checkbox(
    "디버그 데이터 표시",
    value=False,
    key="show_saju_debug",
)

# ── 상수 & 헬퍼 ──
MIN_BIRTH = date(1900, 1, 1)
ADULT_AGE = 19


def _max_birth() -> date:
    t = date.today()
    try:
        return t.replace(year=t.year - ADULT_AGE)
    except ValueError:
        return t.replace(year=t.year - ADULT_AGE, month=2, day=28)


def _init_dates() -> None:
    mx = _max_birth()
    if "birth_pick" not in st.session_state:
        st.session_state.birth_pick = date(1990, 5, 20)
    else:
        b = st.session_state.birth_pick
        if b < MIN_BIRTH or b > mx:
            st.session_state.birth_pick = max(MIN_BIRTH, min(b, mx))


def _pillar_html(label: str, gan: str, zhi: str, *, is_today: bool = False) -> str:
    g_elem = GAN_ELEMENT.get(gan, "earth")
    z_elem = ZHI_ELEMENT.get(zhi, "earth")
    g_color = ELEMENT_COLOR[g_elem]
    z_color = ELEMENT_COLOR[z_elem]
    g_kr = GAN_KR.get(gan, "")
    z_kr = ZHI_KR.get(zhi, "")
    cls = "pillar today" if is_today else "pillar"
    return (
        f'<div class="{cls}">'
        f'  <div class="pillar-label">{label}</div>'
        f'  <div class="pillar-gan" style="color:{g_color}">{gan}</div>'
        f'  <div class="pillar-zhi" style="color:{z_color}">{zhi}</div>'
        f'  <div class="pillar-kr">{g_kr}{z_kr}</div>'
        f'  <div class="pillar-elem" style="color:{g_color}">{ELEMENT_EMOJI[g_elem]}{ELEMENT_KR[g_elem]}</div>'
        f'</div>'
    )


def _count_elements(pillars: Dict, today_pillar: Dict) -> Dict[str, int]:
    counts: Dict[str, int] = {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0}
    for p in list(pillars.values()) + [today_pillar]:
        g = p.get("gan", "")
        z = p.get("zhi", "")
        if g in GAN_ELEMENT:
            counts[GAN_ELEMENT[g]] += 1
        if z in ZHI_ELEMENT:
            counts[ZHI_ELEMENT[z]] += 1
    return counts


def _render_pillars(state: Dict[str, Any]) -> None:
    pillars = state.get("pillars_samju", {})
    today = state.get("day_pillar_today", {})
    if not pillars:
        return

    year = pillars.get("year", {})
    month = pillars.get("month", {})
    day = pillars.get("day", {})

    html = '<div class="pillars-wrap">'
    html += _pillar_html("연주", year.get("gan", ""), year.get("zhi", ""))
    html += _pillar_html("월주", month.get("gan", ""), month.get("zhi", ""))
    html += _pillar_html("일주", day.get("gan", ""), day.get("zhi", ""))
    html += _pillar_html("오늘", today.get("gan", ""), today.get("zhi", ""), is_today=True)
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def _render_elements(state: Dict[str, Any]) -> None:
    pillars = state.get("pillars_samju", {})
    today = state.get("day_pillar_today", {})
    if not pillars:
        return
    counts = _count_elements(pillars, today)
    html = '<div class="elem-dist">'
    for elem in ("wood", "fire", "earth", "metal", "water"):
        c = counts[elem]
        color = ELEMENT_COLOR[elem]
        html += (
            f'<div class="elem-item">'
            f'  <div class="elem-emoji">{ELEMENT_EMOJI[elem]}</div>'
            f'  <div class="elem-name">{ELEMENT_KR[elem]}</div>'
            f'  <div class="elem-count" style="color:{color}">{c}</div>'
            f'</div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def _render_tags(state: Dict[str, Any]) -> None:
    rule = state.get("rule_engine", {})
    tags = rule.get("tags", [])
    if not tags:
        return
    html = '<div class="tags-wrap">'
    for tag in tags:
        if tag.startswith("冲") or "冲" in tag:
            html += f'<span class="tag tag-chong">충 {tag}</span>'
        else:
            html += f'<span class="tag tag-he">합 {tag}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def _render_score(state: Dict[str, Any]) -> None:
    rule = state.get("rule_engine", {})
    pos = rule.get("positive_score", 0)
    neg = rule.get("negative_score", 0)
    total = max(pos + neg, 1)

    pos_pct = int(pos / total * 100)
    neg_pct = int(neg / total * 100)

    html = (
        '<div class="score-wrap">'
        f'  <span class="score-label" style="color:var(--positive)">길</span>'
        f'  <div class="score-bar-bg">'
        f'    <div class="score-bar-fill" style="width:{pos_pct}%;background:var(--positive)"></div>'
        f'  </div>'
        f'  <span class="score-val" style="color:var(--positive)">{pos}</span>'
        f'  <span style="color:var(--line);margin:0 2px">|</span>'
        f'  <span class="score-val" style="color:var(--negative)">{neg}</span>'
        f'  <div class="score-bar-bg">'
        f'    <div class="score-bar-fill" style="width:{neg_pct}%;background:var(--negative)"></div>'
        f'  </div>'
        f'  <span class="score-label" style="color:var(--negative)">흉</span>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _verdict_class(state: Dict[str, Any]) -> str:
    v = state.get("hard_verdict", "balanced")
    if v == "strong_lucky":
        return "verdict-lucky"
    elif v == "strong_unlucky":
        return "verdict-unlucky"
    return "verdict-neutral"


def _render_result(state: Dict[str, Any], *, show_facts: bool) -> None:
    # 사주 기둥
    _render_pillars(state)

    # 오행 분포
    _render_elements(state)

    # 충합 태그
    _render_tags(state)

    # 길흉 점수
    _render_score(state)

    st.markdown("---")

    # verdict 배너
    verdict = state.get("verdict_line", "오늘의 기운")
    cls = _verdict_class(state)
    st.markdown(
        f'<div class="verdict-banner {cls}">{verdict}</div>',
        unsafe_allow_html=True,
    )

    # 요약
    summary = state.get("summary_md", "")
    if summary:
        st.markdown(
            f'<div class="result-section">'
            f'  <div class="section-label">한눈에 보기</div>'
            f'  <div class="section-body">{summary}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # 풀이
    body = (state.get("analysis_md") or "").strip()
    if not body:
        body = state.get("advice_md", "")
    if body:
        st.markdown(
            '<div class="result-section">'
            '  <div class="section-label">오늘의 풀이</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown(body)

    # 실천
    adv = (state.get("advice_md") or "").strip()
    if adv and adv != (body or "").strip():
        st.markdown(
            '<div class="result-section">'
            '  <div class="section-label">오늘의 실천 팁</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown(adv)

    if show_facts and state.get("facts_md"):
        with st.expander("시스템 팩트 (참고)"):
            st.markdown(state.get("facts_md", ""))


# ── 메인 ──
_init_dates()

phase1: Optional[Dict[str, Any]] = st.session_state.get("phase1")
has_result = phase1 is not None

if not has_result:
    # ===== 입력 화면 =====
    st.markdown(
        '<div class="hero">'
        '  <span class="hero-emoji">🔮</span>'
        '  <div class="hero-title">오늘의 사주</div>'
        '  <p class="hero-sub">생년월일로 오늘의 기운을 풀어 드려요</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    st.markdown('<div class="input-label">생년월일을 선택하세요</div>', unsafe_allow_html=True)
    st.date_input(
        "생년월일",
        key="birth_pick",
        format="YYYY-MM-DD",
        min_value=MIN_BIRTH,
        max_value=_max_birth(),
        label_visibility="collapsed",
    )
    _today = date.today()
    st.caption(f"{_today.strftime('%Y년 %m월 %d일')} 기준 풀이")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="height: 0.25rem"></div>', unsafe_allow_html=True)

    birth: date = st.session_state.birth_pick
    if st.button("오늘의 사주 보기", type="primary"):
        with st.spinner("사주를 분석하고 있어요..."):
            try:
                st.session_state.phase1 = run_phase1(
                    birth.isoformat(),
                    date.today().isoformat(),
                    use_mcp=False,
                    gender=1,
                )
            except Exception as e:
                st.error(f"실행 실패: {e}")
                st.stop()
        st.rerun()

    st.markdown(
        '<div class="footer">엔터테인먼트 목적이에요. 중요한 판단의 근거로 쓰지 마세요.</div>',
        unsafe_allow_html=True,
    )

else:
    # ===== 결과 화면 =====
    _today = date.today()
    birth = st.session_state.birth_pick

    st.markdown(
        f'<div class="result-hero">'
        f'  <span class="result-hero-emoji">🔮</span>'
        f'  <div class="result-hero-date">{_today.strftime("%Y년 %m월 %d일")} 풀이</div>'
        f'  <div class="result-hero-birth">{birth.strftime("%Y.%m.%d")}생</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # 디버그
    if st.session_state.get("show_saju_debug"):
        raw = phase1.get("raw_tool_json", {})
        with st.expander("디버그"):
            st.json(raw)

    final_state: Optional[Dict[str, Any]] = st.session_state.get("final_state")

    if final_state:
        _render_result(final_state, show_facts=False)
    elif phase1.get("tikitaka_question") and not phase1.get("summary_md"):
        # 사주 기둥은 먼저 보여줌
        _render_pillars(phase1)
        _render_elements(phase1)
        _render_tags(phase1)
        _render_score(phase1)
        st.markdown("---")

        # 티키타카 질문
        st.markdown(
            f'<div class="question-card">'
            f'  <div class="question-icon">🤔</div>'
            f'  <div class="question-text">{phase1["tikitaka_question"]}</div>'
            f'  <div class="question-hint">오늘의 기운이 갈리는 날이에요. 답변에 따라 풀이가 달라져요.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        ans = st.text_input(
            "답변",
            key="tikitaka_ans",
            label_visibility="collapsed",
            placeholder="여기에 답변을 입력하세요",
        )
        if st.button("풀이 이어가기", type="primary"):
            if not (ans or "").strip():
                st.error("답을 입력해 주세요.")
            else:
                with st.spinner("풀이를 이어가고 있어요..."):
                    try:
                        st.session_state.final_state = run_phase2_tikitaka_finish(phase1, ans.strip())
                    except Exception as e:
                        st.error(f"실패: {e}")
                st.rerun()
    else:
        _render_result(phase1, show_facts=False)

    st.markdown('<div style="height: 0.5rem"></div>', unsafe_allow_html=True)
    if st.button("다시 풀어보기", type="secondary"):
        for k in ("phase1", "final_state"):
            st.session_state.pop(k, None)
        st.rerun()

    st.markdown(
        '<div class="footer">엔터테인먼트 목적이에요. 중요한 판단의 근거로 쓰지 마세요.</div>',
        unsafe_allow_html=True,
    )
