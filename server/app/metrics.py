"""대화 분류와 지표 계산 (작업지시서 [2단계]).

외부 API 없이 순수 함수로만 계산한다. 테스트: server/tests/test_metrics.py
지표
- avg_utterance_len : 부모 발화 길이(공백 제외 글자 수) 평균
- repeat_rate       : 동일 표현 반복률 = 앞선 발화와 유사(0.7 이상)한 부모 발화 수 / 부모 발화 수
- uncertain_rate    : 불확실 표현('글쎄', '기억이 안', '모르겠' …)이 들어간 부모 발화 비율
- avg_response_gap  : 다정이 발화 종료 → 부모 발화 시작까지 간격(초) 평균
- participation     : 대화 참여 지표 = 부모 발화 글자 수 / 전체 발화 글자 수
- valid             : 부모 발화 3회 이상이면 유효 대화 (기준선 계산에 포함)
"""
from __future__ import annotations
import re
import statistics
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

UNCERTAIN_PATTERNS = [
    r"글쎄", r"기억이\s*안", r"기억\s*안\s*나", r"모르겠", r"뭐였더라", r"뭐더라", r"가물가물",
    r"잘\s*모르", r"생각이\s*안", r"뭐였지", r"그게\s*뭐", r"누구였더라", r"언제였더라",
]
_UNCERTAIN = re.compile("|".join(UNCERTAIN_PATTERNS))

REPEAT_THRESHOLD = 0.7   # 글자 2-gram 유사도
MIN_VALID_PARENT_TURNS = 3
BASELINE_MIN_DAYS = 14
BASELINE_MIN_CONVERSATIONS = 5


def normalize(text: str) -> str:
    return re.sub(r"[^0-9a-zA-Z가-힣]", "", text or "")


def bigrams(text: str) -> set[str]:
    t = normalize(text)
    return {t[i:i + 2] for i in range(len(t) - 1)}


def similarity(a: str, b: str) -> float:
    """글자 2-gram 겹침 비율 (짧은 쪽 기준). 같은 질문을 다시 하면 0.7 이상으로 잡힌다."""
    A, B = bigrams(a), bigrams(b)
    if not A or not B:
        return 0.0
    return len(A & B) / min(len(A), len(B))


def is_uncertain(text: str) -> bool:
    return bool(_UNCERTAIN.search(text or ""))


def tag_parent_turns(parent_texts: list[str]) -> list[list[str]]:
    """부모 발화 목록 → 발화별 태그 목록. 같은 대화 안에서 앞선 발화와 비슷하면 repeat."""
    tags: list[list[str]] = []
    for i, text in enumerate(parent_texts):
        t: list[str] = []
        if any(similarity(text, prev) >= REPEAT_THRESHOLD for prev in parent_texts[:i]):
            t.append("repeat")
        if is_uncertain(text):
            t.append("uncertain")
        tags.append(t)
    return tags


@dataclass
class TurnIn:
    speaker: str                 # bot | parent
    text: str
    started_at: datetime
    ended_at: datetime | None = None


@dataclass
class Metrics:
    parent_turns: int
    avg_utterance_len: float
    repeat_rate: float
    uncertain_rate: float
    avg_response_gap: float | None
    participation: float
    duration_sec: float
    valid: bool
    tags: list[list[str]]        # 부모 발화 순서대로

    def as_row(self) -> dict:
        d = asdict(self); d.pop("tags"); return d


def response_gaps(turns: list[TurnIn]) -> list[float | None]:
    """부모 발화마다 직전 bot 발화 종료(없으면 시작) → 부모 발화 시작 간격(초)."""
    gaps: list[float | None] = []
    last_bot_end: datetime | None = None
    for t in turns:
        if t.speaker == "bot":
            last_bot_end = t.ended_at or t.started_at
        else:
            if last_bot_end is None:
                gaps.append(None)
            else:
                g = (t.started_at - last_bot_end).total_seconds()
                gaps.append(g if 0 <= g <= 120 else None)   # 2분 넘는 공백은 자리 비움으로 보고 제외
    return gaps


def compute_metrics(turns: list[TurnIn]) -> Metrics:
    parents = [t for t in turns if t.speaker == "parent"]
    parent_texts = [t.text for t in parents]
    tags = tag_parent_turns(parent_texts)
    n = len(parents)
    lens = [len(normalize(t)) for t in parent_texts]
    total_len = sum(len(normalize(t.text)) for t in turns) or 1
    gaps = [g for g in response_gaps(turns) if g is not None]
    if turns:
        start = min(t.started_at for t in turns)
        end = max((t.ended_at or t.started_at) for t in turns)
        duration = max(0.0, (end - start).total_seconds())
    else:
        duration = 0.0
    return Metrics(
        parent_turns=n,
        avg_utterance_len=round(statistics.mean(lens), 1) if lens else 0.0,
        repeat_rate=round(sum("repeat" in t for t in tags) / n, 3) if n else 0.0,
        uncertain_rate=round(sum("uncertain" in t for t in tags) / n, 3) if n else 0.0,
        avg_response_gap=round(statistics.mean(gaps), 2) if gaps else None,
        participation=round(sum(lens) / total_len, 3),
        duration_sec=round(duration, 1),
        valid=n >= MIN_VALID_PARENT_TURNS,
        tags=tags,
    )


# ---- 기준선 ----
BASELINE_KEYS = ["avg_utterance_len", "repeat_rate", "uncertain_rate", "avg_response_gap", "participation"]
HIGHER_IS_BETTER = {"avg_utterance_len": True, "repeat_rate": False, "uncertain_rate": False,
                    "avg_response_gap": False, "participation": True}


def baseline_ready(first_valid_at: datetime | None, n_valid: int, now: datetime) -> bool:
    if first_valid_at is None:
        return False
    return n_valid >= BASELINE_MIN_CONVERSATIONS and now - first_valid_at >= timedelta(days=BASELINE_MIN_DAYS)


def build_baseline(rows: list[dict]) -> dict:
    """유효 대화 지표 행들 → {metric: {mean, sd, n}}"""
    out = {}
    for k in BASELINE_KEYS:
        vals = [r[k] for r in rows if r.get(k) is not None]
        if len(vals) >= 2:
            out[k] = {"mean": round(statistics.mean(vals), 3), "sd": round(statistics.pstdev(vals), 3), "n": len(vals)}
        elif vals:
            out[k] = {"mean": round(vals[0], 3), "sd": 0.0, "n": 1}
    return out


def compare_to_baseline(recent: dict, baseline: dict) -> dict:
    """최근 값과 기준선 비교 → {metric: {recent, mean, delta, level}}
    level: same(평소) | watch(관찰) | notable(확인). 의료 판정이 아니다.
    """
    out = {}
    for k in BASELINE_KEYS:
        if recent.get(k) is None or k not in baseline:
            continue
        b = baseline[k]; r = recent[k]
        sd = b["sd"] if b["sd"] > 0 else max(abs(b["mean"]) * 0.15, 1e-6)
        z = (r - b["mean"]) / sd
        worse = -z if HIGHER_IS_BETTER[k] else z
        level = "notable" if worse >= 1.5 else "watch" if worse >= 1.0 else "same"
        out[k] = {"recent": r, "mean": b["mean"], "delta": round(r - b["mean"], 3), "z": round(z, 2), "level": level}
    return out
