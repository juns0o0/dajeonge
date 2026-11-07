"""지표 계산 테스트 (작업지시서 [2단계] 산출물: 계산식·테스트 예시).  실행: cd server && python -m pytest -q"""
from datetime import datetime, timedelta
from app import metrics as M

T0 = datetime(2026, 11, 10, 10, 0, 0)


def turn(speaker, text, sec, dur=2):
    return M.TurnIn(speaker, text, T0 + timedelta(seconds=sec), T0 + timedelta(seconds=sec + dur))


def test_similarity_catches_repeated_question():
    assert M.similarity("밥은 먹었어? 밥은?", "너 밥은 먹었니? 밥은 먹었어?") >= 0.7
    assert M.similarity("오늘 경로당 갔다 왔어", "서윤이는 잘 있니?") < 0.3


def test_uncertain_patterns():
    assert M.is_uncertain("글쎄… 잘 기억이 안 나네")
    assert M.is_uncertain("그게 뭐였더라")
    assert not M.is_uncertain("상추랑 고추 심었지")


def test_compute_metrics_basic():
    turns = [
        turn("bot", "엄마 뭐해? 밥은 챙겨 먹었어?", 0, 3),
        turn("parent", "응 먹었지. 된장국에 밥 말아 먹었어.", 5, 3),      # gap 2s
        turn("bot", "오늘 텃밭에 뭐 심었다고 했지?", 9, 3),
        turn("parent", "상추랑 고추랑 방울토마토 심었지.", 13, 3),        # gap 1s
        turn("bot", "서윤이가 토마토 따러 가고 싶대.", 17, 3),
        turn("parent", "글쎄 그게 언제였더라. 응 먹었지. 된장국에 밥 말아 먹었어.", 24, 4),  # gap 4s, repeat+uncertain
    ]
    m = M.compute_metrics(turns)
    assert m.parent_turns == 3 and m.valid
    assert m.tags[0] == [] and m.tags[1] == []
    assert "repeat" in m.tags[2] and "uncertain" in m.tags[2]
    assert abs(m.repeat_rate - 1 / 3) < 1e-3 and abs(m.uncertain_rate - 1 / 3) < 1e-3
    assert abs(m.avg_response_gap - (2 + 1 + 4) / 3) < 1e-2
    assert 0 < m.participation < 1
    assert m.duration_sec == 28.0


def test_invalid_when_few_parent_turns():
    m = M.compute_metrics([turn("bot", "엄마 뭐해?", 0), turn("parent", "응", 3)])
    assert m.parent_turns == 1 and not m.valid


def test_response_gap_ignores_long_absence():
    turns = [turn("bot", "엄마?", 0, 2), turn("parent", "응", 300)]   # 5분 뒤 → 자리 비움, 제외
    assert M.response_gaps(turns) == [None]


def test_baseline_rules():
    first = datetime(2026, 11, 1)
    assert not M.baseline_ready(first, 4, first + timedelta(days=20))     # 5회 미만
    assert not M.baseline_ready(first, 8, first + timedelta(days=10))     # 14일 미만
    assert M.baseline_ready(first, 5, first + timedelta(days=14))
    rows = [{"avg_utterance_len": 20, "repeat_rate": 0.1, "uncertain_rate": 0.0, "avg_response_gap": 1.8, "participation": 0.5},
            {"avg_utterance_len": 24, "repeat_rate": 0.0, "uncertain_rate": 0.2, "avg_response_gap": 2.2, "participation": 0.55}]
    b = M.build_baseline(rows)
    assert b["avg_utterance_len"]["mean"] == 22 and b["avg_response_gap"]["n"] == 2


def test_compare_levels():
    base = {"avg_response_gap": {"mean": 2.0, "sd": 0.4, "n": 5}, "avg_utterance_len": {"mean": 20, "sd": 3, "n": 5}}
    c = M.compare_to_baseline({"avg_response_gap": 2.1, "avg_utterance_len": 14}, base)
    assert c["avg_response_gap"]["level"] == "same"
    assert c["avg_utterance_len"]["level"] == "notable"     # 2 sd 낮음
    c2 = M.compare_to_baseline({"avg_response_gap": 2.5}, base)
    assert c2["avg_response_gap"]["level"] == "watch"
