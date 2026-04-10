"""
LangGraph StateGraph: 만세력 계산 → hard_verdict 조건부 분기 → LLM 문구 생성.
티키타카 2단계는 Streamlit에서 user_followup_text 유무로 resolve 노드를 별도 호출.
"""
from __future__ import annotations

import json
import os
from datetime import date
from typing import Any, Dict, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from saju_engine import compute_saju_payload, compute_saju_payload_custom

load_dotenv()

try:
    from saju_mcp_bridge import compute_saju_payload_mcp
except Exception:  # pragma: no cover — mcp 미설치·Node 없음 등
    compute_saju_payload_mcp = None  # type: ignore[misc, assignment]


class SajuGraphState(TypedDict, total=False):
    birth_date: str
    target_date: str
    use_mcp: bool
    gender: int
    pillars_samju: Dict[str, Any]
    day_pillar_today: Dict[str, Any]
    rule_engine: Dict[str, Any]
    hard_verdict: str
    raw_tool_json: Dict[str, Any]
    tikitaka_question: str
    user_followup_text: str
    final_branch: Literal["lucky", "healing"]
    verdict_line: str
    summary_md: str
    analysis_md: str
    facts_md: str
    advice_md: str


def _facts_block(payload: Dict[str, Any]) -> str:
    sj = payload["pillars_samju"]
    td = payload["day_pillar_today"]
    re = payload["rule_engine"]
    lines = [
        f"- 생년월일(양력): {payload['birth_iso']}",
        f"- 기준일(KST 달력): {payload['target_iso']}",
        f"- 삼주: 연{sj['year']['pillar']} 월{sj['month']['pillar']} 일{sj['day']['pillar']}",
        f"- 오늘 일진: {td['pillar']} ({td['gan']}{td['zhi']})",
        f"- 규칙 태그: {', '.join(re['tags']) if re['tags'] else '(없음)'}",
        f"- 규칙 점수: 총 {re['score']} (긍정 {re['positive_score']}, 부정 {re['negative_score']})",
        f"- 1차 판정(hard_verdict): **{payload['hard_verdict']}**",
        f"- 만세력 출처: **{payload.get('calendar_source', 'local')}**",
    ]
    if payload.get("mcp_unavailable"):
        lines.append("- MCP: **브리지 미로드(`saju_mcp_bridge`) — 로컬 엔진 사용**")
    if payload.get("mcp_error"):
        lines.append(f"- MCP 오류(로컬 대체): `{payload['mcp_error'][:200]}`")
    return "\n".join(lines)


def _build_llm() -> ChatOpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY가 필요합니다.")
    return ChatOpenAI(model="gpt-5-mini")


def node_ingest(state: SajuGraphState) -> Dict[str, Any]:
    b = date.fromisoformat(state["birth_date"][:10])
    t = date.fromisoformat(state["target_date"][:10])
    use_mcp = bool(state.get("use_mcp"))
    gender = int(state.get("gender", 1) or 1)
    payload: Dict[str, Any]
    if use_mcp and compute_saju_payload_mcp is None:
        payload = compute_saju_payload(b, t)
        payload["mcp_unavailable"] = True
    elif use_mcp:
        try:
            payload = compute_saju_payload_mcp(b, t, gender=gender)
        except Exception as e:
            payload = compute_saju_payload(b, t)
            payload["calendar_source"] = "local_fallback"
            payload["mcp_error"] = str(e)
    else:
        payload = compute_saju_payload(b, t)
    return {
        "pillars_samju": payload["pillars_samju"],
        "day_pillar_today": payload["day_pillar_today"],
        "rule_engine": payload["rule_engine"],
        "hard_verdict": payload["hard_verdict"],
        "raw_tool_json": payload,
        "facts_md": _facts_block(payload),
    }


def route_verdict(state: SajuGraphState) -> Literal["lucky", "healing", "tikitaka"]:
    v = state.get("hard_verdict", "ambiguous")
    if v in ("strong_lucky", "balanced"):
        return "lucky"
    if v == "strong_unlucky":
        return "healing"
    return "tikitaka"


VOICE_GUIDE = """말투·톤
- 친한 동갑내기 친구가 카톡으로 운세 풀어주는 느낌: **따뜻하고 가볍게**, 딱딱한 보고서체나 설명서 나열은 피한다.
- **반말** 또는 아주 가벼운 **해요체**로 통일해 부담 없게(예: "~한 거야", "~해봐", "~각이야", "오늘은 그냥 ~ 타임" 식). '귀하'·'해당'·'다음과 같습니다' 류는 쓰지 않는다.
- 문장은 짧게 끊고, 가끔 리액션처럼 한마디 덧붙여도 좋다.

밈·유행어
- **2023~2026년대** 한국 인터넷·SNS에서 통하는 밈, 짤 문화, 짧은 유행어를 **문맥에 맞게 적극** 녹인다(본문에서는 문단마다 0~1회 정도 자연스럽게; 억지로 끼워 넣지 않는다).
- 낡은 밈·과한 ㅋㅋ·혐오·차별·선정적 밈은 금지. 전 연령이 무리 없이 읽을 수 있는 선에서만 쓴다.

금지: 과학·의학·법률·투자 조언을 사실처럼 단정하는 말."""


def _system_base() -> str:
    return f"""당신은 오락용 AI 명리학 도우미입니다. 과학적·역학적 근거는 없습니다.
반드시 아래 팩트 블록의 간지·충합·판정을 바꾸거나 부정하지 마세요. 환각 금지.
{VOICE_GUIDE}
출력은 한국어. 선정적·혐오·차별 표현 금지."""


def node_final_lucky(state: SajuGraphState) -> Dict[str, Any]:
    llm = _build_llm()
    sys = _system_base()
    verdict = state.get("hard_verdict", "")
    balanced_note = ""
    if verdict == "balanced":
        balanced_note = """
판정이 **balanced**(규칙 태그 없음): 충·합 딱지는 없다고 **친구한테 말하듯** 풀고, 삼주+오늘 일진 분위기는 **무난·균형** 쪽으로. 초대박 길운 과장은 금지, 대신 분위기 묘사·밈은 풍성하게.
"""
    human = f"""다음 팩트는 시스템이 확정한 값입니다. 이 줄기 위에서만 **일반 사주·일상 운세**로 풀어쓰세요.
{balanced_note}
{state.get('facts_md', '')}

반드시 JSON만 출력 (값은 모두 한국어, 마크다운 허용 필드는 analysis만):
{{
  "summary": "2~3문장. 첫 문장부터 훅—친구한테 보내는 카톡처럼 가볍고 웃기거나 공감 가게.",
  "verdict_line": "오늘 한 줄 결론. 짧고 밈·유행어 한 스푼 섞어도 됨.",
  "analysis": "본문 **최소 5문단**. (1) 오늘 기운 한줄요약 (2) 연월일·일진 느낌을 일상·SNS 비유로 (3) 충·합 있으면 '오늘 이런 각 나올 수 있음' 식 쉬운 말 (4) 인간관계·소비·컨디션 팁 (5) 밈·트렌드·짤 감성으로 마무리. 문단마다 톤 살짝 살려 투박하지 않게. 팩트와 모순 금지.",
  "advice": "실천 팁 3~5개, 짧은 문자열 배열. 각 줄도 친구한테 추천하는 말투+가벼운 밈 OK: [\"...\", \"...\"]"
}}"""
    msg = llm.invoke([SystemMessage(content=sys), HumanMessage(content=human)])
    raw = (msg.content or "").strip()
    data = _parse_json_obj(raw)
    advice = data.get("advice", "")
    if isinstance(advice, list):
        advice = "\n".join(f"- {x}" for x in advice)
    return {
        "final_branch": "lucky",
        "summary_md": data.get("summary", ""),
        "verdict_line": data.get("verdict_line", ""),
        "analysis_md": data.get("analysis", ""),
        "advice_md": str(advice),
    }


def node_final_healing(state: SajuGraphState) -> Dict[str, Any]:
    llm = _build_llm()
    sys = _system_base()
    human = f"""다음 팩트는 시스템이 확정한 값입니다. **강한 흉 쪽**이므로 무리한 도전·큰 결정·과소비·갈등 확대를 **권하면 안 됩니다**. 위로·방어·휴식은 **친구가 진심으로 말려주는 톤**으로—차갑거나 훈계조 말고.

{state.get('facts_md', '')}

반드시 JSON만 출력:
{{
  "summary": "2~3문장. 공포 X, '오늘은 그냥 버티기/회복 각' 공감 + 가벼운 밈 한 방.",
  "verdict_line": "한 줄 결론. 방어·힐링인데도 밋밋하지 말고 친근하게.",
  "analysis": "본문 **최소 5문단**. (1) 오늘 기운 (2) 천천히 가도 된다는 비유—일상·SNS 감성 (3) 충·합 있으면 감정 탈선 각 예시 (4) 쉼·환불·연기 이득 (5) 위로하면서 밈·유행어로 톤 업. 투박한 위로 금지. 팩트와 모순 금지.",
  "advice": "지킬 것 3~5개 배열. 각각 친구가 옆에서 잔소리하는 느낌으로 짧게+밈 살짝: [\"...\", \"...\"]"
}}"""
    msg = llm.invoke([SystemMessage(content=sys), HumanMessage(content=human)])
    raw = (msg.content or "").strip()
    data = _parse_json_obj(raw)
    advice = data.get("advice", "")
    if isinstance(advice, list):
        advice = "\n".join(f"- {x}" for x in advice)
    return {
        "final_branch": "healing",
        "summary_md": data.get("summary", ""),
        "verdict_line": data.get("verdict_line", ""),
        "analysis_md": data.get("analysis", ""),
        "advice_md": str(advice),
    }


def node_tikitaka_question(state: SajuGraphState) -> Dict[str, Any]:
    llm = _build_llm()
    sys = _system_base()
    human = f"""오늘은 명리적으로 애매한 날입니다. 사용자에게 **한 문장** 질문만 하세요.
카톡으로 친구가 묻는 느낌: 일상·감정·컨디션·오늘 각. **요즘 밈·가벼운 유행어** 한 스푼 넣어도 좋다. 물음표로 끝내기.

팩트(참고만):
{state.get('facts_md', '')}

반드시 JSON만 출력: {{"question": "..."}}"""
    msg = llm.invoke([SystemMessage(content=sys), HumanMessage(content=human)])
    data = _parse_json_obj((msg.content or "").strip())
    return {"tikitaka_question": data.get("question", "오늘 컨디션은 어떤가요?")}


def _parse_json_obj(text: str) -> Dict[str, Any]:
    text = text.strip()
    if "```" in text:
        start = text.find("```")
        rest = text[start + 3 :]
        if rest.lstrip().lower().startswith("json"):
            rest = rest.lstrip()[4:].lstrip()
        end = rest.rfind("```")
        if end != -1:
            text = rest[:end]
        else:
            text = rest
    text = text.strip()
    if "{" in text:
        lo = text.find("{")
        hi = text.rfind("}")
        if hi > lo:
            text = text[lo : hi + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def resolve_tikitaka_branch(state: SajuGraphState) -> Dict[str, Any]:
    """사용자 자연어 답 → lucky | healing (애매 구간 전용)."""
    llm = _build_llm()
    sys = _system_base()
    human = f"""애매한 날입니다. 사용자 답변의 뉘앙스로 오늘 에너지를 **lucky** 또는 **healing** 중 하나만 고르세요.
피곤·우울·몸살·스트레스 → healing
상쾌·텐션·컨디션 좋음 → lucky
애매하면 보수적으로 healing.

질문: {state.get('tikitaka_question', '')}
답변: {state.get('user_followup_text', '')}

JSON만: {{"branch": "lucky" 또는 "healing", "reason": "한 줄 이유—친구한테 말하듯, 밈 한 스푼 가능"}}"""
    msg = llm.invoke([SystemMessage(content=sys), HumanMessage(content=human)])
    data = _parse_json_obj((msg.content or "").strip())
    br = data.get("branch", "healing")
    if br not in ("lucky", "healing"):
        br = "healing"
    return {"final_branch": br}


def build_saju_graph():
    g = StateGraph(SajuGraphState)
    g.add_node("ingest", node_ingest)
    g.add_node("lucky", node_final_lucky)
    g.add_node("healing", node_final_healing)
    g.add_node("tikitaka", node_tikitaka_question)
    g.set_entry_point("ingest")
    g.add_conditional_edges(
        "ingest",
        route_verdict,
        {"lucky": "lucky", "healing": "healing", "tikitaka": "tikitaka"},
    )
    g.add_edge("lucky", END)
    g.add_edge("healing", END)
    g.add_edge("tikitaka", END)
    return g.compile()


COMPILED_GRAPH = None


def get_graph():
    global COMPILED_GRAPH
    if COMPILED_GRAPH is None:
        COMPILED_GRAPH = build_saju_graph()
    return COMPILED_GRAPH


def run_phase1(
    birth_iso: str,
    target_iso: str,
    *,
    use_mcp: bool = False,
    gender: int = 1,
) -> SajuGraphState:
    graph = get_graph()
    init: SajuGraphState = {
        "birth_date": birth_iso,
        "target_date": target_iso,
        "use_mcp": use_mcp,
        "gender": int(gender),
    }
    return graph.invoke(init)  # type: ignore[return-value]


def run_phase2_tikitaka_finish(state: SajuGraphState, user_text: str) -> SajuGraphState:
    """질문까지 나온 상태 + 사용자 답 → 최종 lucky/healing 본문."""
    s = dict(state)
    s["user_followup_text"] = user_text
    s.update(resolve_tikitaka_branch(s))
    if s.get("final_branch") == "lucky":
        s.update(node_final_lucky(s))
    else:
        s.update(node_final_healing(s))
    return s  # type: ignore[return-value]


def tool_saju_compute(birth_iso: str, target_iso: str) -> str:
    """ReAct/도구 연동용: 만세력·규칙 JSON."""
    b = date.fromisoformat(birth_iso[:10])
    t = date.fromisoformat(target_iso[:10])
    return json.dumps(compute_saju_payload(b, t), ensure_ascii=False, indent=2)


try:
    from langchain_core.tools import tool

    @tool
    def compute_saju_analysis(birth_date_iso: str, target_date_iso: str) -> str:
        """양력 생년월일과 기준일(YYYY-MM-DD)로 삼주·오늘 일진·충합 규칙과 hard_verdict를 JSON으로 반환합니다."""
        return tool_saju_compute(birth_date_iso, target_date_iso)

except Exception:  # pragma: no cover
    compute_saju_analysis = None  # type: ignore[misc, assignment]
