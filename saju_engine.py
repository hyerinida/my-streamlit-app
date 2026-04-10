"""
만세력·삼주(연월일)·기준일 일진 및 충·합 기반 규칙 엔진 (MVP, KST 달력일 기준).
일진은 줄리안일 + (JD+49)%60 공식으로 산출합니다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Tuple

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

# 지지 충(六冲)
CHONG_PAIRS = frozenset(
    {
        ("子", "午"),
        ("午", "子"),
        ("丑", "未"),
        ("未", "丑"),
        ("寅", "申"),
        ("申", "寅"),
        ("卯", "酉"),
        ("酉", "卯"),
        ("辰", "戌"),
        ("戌", "辰"),
        ("巳", "亥"),
        ("亥", "巳"),
    }
)

# 지지 육합
LIUHE_PAIRS = frozenset(
    {
        ("子", "丑"),
        ("丑", "子"),
        ("寅", "亥"),
        ("亥", "寅"),
        ("卯", "戌"),
        ("戌", "卯"),
        ("辰", "酉"),
        ("酉", "辰"),
        ("巳", "申"),
        ("申", "巳"),
        ("午", "未"),
        ("未", "午"),
    }
)

# 천간 오합
STEM_HE_PAIRS = frozenset(
    {
        ("甲", "己"),
        ("己", "甲"),
        ("乙", "庚"),
        ("庚", "乙"),
        ("丙", "辛"),
        ("辛", "丙"),
        ("丁", "壬"),
        ("壬", "丁"),
        ("戊", "癸"),
        ("癸", "戊"),
    }
)


def _jd_gregorian(y: int, m: int, d: int) -> int:
    a = (14 - m) // 12
    y_ = y + 4800 - a
    m_ = m + 12 * a - 3
    return d + (153 * m_ + 2) // 5 + 365 * y_ + y_ // 4 - y_ // 100 + y_ // 400 - 32045


def day_pillar_from_solar(y: int, m: int, d: int) -> Tuple[str, str]:
    """양력 연·월·일 → 일간·일지 (甲子=0 …)."""
    jd = _jd_gregorian(y, m, d)
    idx = (jd + 49) % 60
    return GAN[idx % 10], ZHI[idx % 12]


def _lichun_adjusted_year(b: date) -> int:
    """입춘(약 2/4) 이전이면 전년도로 간주 (년주 계산 MVP)."""
    if (b.month, b.day) < (2, 4):
        return b.year - 1
    return b.year


def year_pillar_from_date(b: date) -> Tuple[str, str]:
    y = _lichun_adjusted_year(b)
    idx = (y - 4) % 10
    z = (y - 4) % 12
    return GAN[idx], ZHI[z]


def _month_zhi_for_solar(b: date) -> str:
    """절기 경계 단순화(교육용): 대략적 월지."""
    m, d = b.month, b.day
    # (시작월, 시작일) 이상이면 해당 월지
    bounds = [
        ((1, 1), (2, 3), "丑"),
        ((2, 4), (3, 4), "寅"),
        ((3, 5), (4, 4), "卯"),
        ((4, 5), (5, 4), "辰"),
        ((5, 5), (6, 5), "巳"),
        ((6, 6), (7, 6), "午"),
        ((7, 7), (8, 6), "未"),
        ((8, 7), (9, 7), "申"),
        ((9, 8), (10, 7), "酉"),
        ((10, 8), (11, 6), "戌"),
        ((11, 7), (12, 6), "亥"),
        ((12, 7), (12, 31), "子"),
    ]
    for (sm, sd), (em, ed), zhi in bounds:
        start = (sm, sd)
        end = (em, ed)
        cur = (m, d)
        if start <= cur <= end:
            return zhi
    return "丑"


def _first_month_stem_for_year_stem(year_stem: str) -> int:
    """五虎遁: 인월 천간 인덱스."""
    table = {"甲": 2, "己": 2, "乙": 4, "庚": 4, "丙": 6, "辛": 6, "丁": 8, "壬": 8, "戊": 0, "癸": 0}
    return table[year_stem]


def _zhi_index(z: str) -> int:
    return ZHI.index(z)


def month_pillar_from_date(b: date) -> Tuple[str, str]:
    y_stem, _ = year_pillar_from_date(b)
    mz = _month_zhi_for_solar(b)
    # 인월(寅) 간지 인덱스를 0으로 한 월수 차이
    yin_idx = _zhi_index("寅")
    cur_idx = _zhi_index(mz)
    offset = (cur_idx - yin_idx) % 12
    stem0 = _first_month_stem_for_year_stem(y_stem)
    stem = GAN[(stem0 + offset) % 10]
    return stem, mz


def samju_from_birth(birth: date) -> Dict[str, Any]:
    yg, yz = year_pillar_from_date(birth)
    mg, mz = month_pillar_from_date(birth)
    dg, dz = day_pillar_from_solar(birth.year, birth.month, birth.day)
    return {
        "year": {"gan": yg, "zhi": yz, "pillar": f"{yg}{yz}"},
        "month": {"gan": mg, "zhi": mz, "pillar": f"{mg}{mz}"},
        "day": {"gan": dg, "zhi": dz, "pillar": f"{dg}{dz}"},
    }


def today_pillar(target: date) -> Dict[str, str]:
    g, z = day_pillar_from_solar(target.year, target.month, target.day)
    return {"gan": g, "zhi": z, "pillar": f"{g}{z}"}


@dataclass
class RuleResult:
    tags: List[str] = field(default_factory=list)
    score: int = 0
    positive_score: int = 0
    negative_score: int = 0
    has_chong: bool = False
    has_he: bool = False
    day_branch_chong_birth_day: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tags": self.tags,
            "score": self.score,
            "positive_score": self.positive_score,
            "negative_score": self.negative_score,
            "has_chong": self.has_chong,
            "has_he": self.has_he,
            "day_branch_chong_birth_day": self.day_branch_chong_birth_day,
        }


def analyze_chong_he(samju: Dict[str, Any], today: Dict[str, str]) -> RuleResult:
    """삼주 지지·천간 vs 오늘 일진 간 충·합(육합·천간합) 위주."""
    r = RuleResult()
    tg, tz = today["gan"], today["zhi"]
    pillars = [
        ("연", samju["year"]["gan"], samju["year"]["zhi"]),
        ("월", samju["month"]["gan"], samju["month"]["zhi"]),
        ("일", samju["day"]["gan"], samju["day"]["zhi"]),
    ]

    birth_day_zhi = samju["day"]["zhi"]

    for label, bg, bz in pillars:
        pair_z = (bz, tz)
        if pair_z in CHONG_PAIRS:
            r.has_chong = True
            r.negative_score += 2
            r.tags.append(f"冲:{label}지({bz})×오늘일지({tz})")
            if label == "일":
                r.day_branch_chong_birth_day = True
        if pair_z in LIUHE_PAIRS:
            r.has_he = True
            r.positive_score += 2
            r.tags.append(f"合:{label}지({bz})×오늘일지({tz})")
        pair_g = (bg, tg)
        if pair_g in STEM_HE_PAIRS:
            r.has_he = True
            r.positive_score += 1
            r.tags.append(f"干合:{label}간({bg})×오늘일간({tg})")

    r.score = r.positive_score - r.negative_score
    return r


def hard_verdict_from_rules(rule: RuleResult) -> str:
    """
    strong_lucky / strong_unlucky / balanced / ambiguous
    - 무별(유의미한 충합 태그 없음) → balanced (무난·균형, 긍정 풀이 경로로 연결)
    - 강흉: 점수가 매우 낮거나 일지 충이 생일 일지와 직접 충
    - 강길: 긍정 우세且 부정 약함
    - 충·합 동시: 순점수로 방향을 잡고, 완전 상쇄(score==0)만 ambiguous
    - 약한 신호(|score|<=2): 순점수 부호로 lucky/unlucky, 0만 ambiguous
    """
    if not rule.tags:
        return "balanced"

    if rule.day_branch_chong_birth_day or rule.negative_score >= 3 or rule.score <= -3:
        return "strong_unlucky"

    if rule.positive_score >= 3 and rule.negative_score == 0:
        return "strong_lucky"

    if rule.score >= 3:
        return "strong_lucky"

    if rule.has_chong and rule.has_he:
        if rule.score > 0:
            return "strong_lucky"
        if rule.score < 0:
            return "strong_unlucky"
        return "ambiguous"

    if -2 <= rule.score <= 2:
        if rule.score > 0:
            return "strong_lucky"
        if rule.score < 0:
            return "strong_unlucky"
        return "ambiguous"

    if rule.score <= -3:
        return "strong_unlucky"

    return "ambiguous"


def compute_saju_payload(birth: date, target: date) -> Dict[str, Any]:
    samju = samju_from_birth(birth)
    day_t = today_pillar(target)
    rule = analyze_chong_he(samju, day_t)
    verdict = hard_verdict_from_rules(rule)
    return {
        "birth_iso": birth.isoformat(),
        "target_iso": target.isoformat(),
        "timezone": "Asia/Seoul",
        "calendar_source": "local",
        "pillars_samju": samju,
        "day_pillar_today": day_t,
        "rule_engine": rule.to_dict(),
        "hard_verdict": verdict,
    }


def compute_saju_payload_custom(
    birth_iso: str,
    target_iso: str,
    pillars_samju: Dict[str, Any],
    day_pillar_today: Dict[str, Any],
    *,
    calendar_source: str = "custom",
) -> Dict[str, Any]:
    """외부 만세력(MCP 등)에서 받은 삼주·일진으로 규칙 엔진만 적용."""
    rule = analyze_chong_he(pillars_samju, day_pillar_today)
    verdict = hard_verdict_from_rules(rule)
    return {
        "birth_iso": birth_iso,
        "target_iso": target_iso,
        "timezone": "Asia/Seoul",
        "calendar_source": calendar_source,
        "pillars_samju": pillars_samju,
        "day_pillar_today": day_pillar_today,
        "rule_engine": rule.to_dict(),
        "hard_verdict": verdict,
    }


def saju_tool_json(birth_iso: str, target_iso: str) -> str:
    """LangChain tool용: ISO 문자열(YYYY-MM-DD) 입력."""
    import json

    b = date.fromisoformat(birth_iso.strip()[:10])
    t = date.fromisoformat(target_iso.strip()[:10])
    return json.dumps(compute_saju_payload(b, t), ensure_ascii=False, indent=2)
