"""외부 AI API 연동 (OpenAI). 키가 없으면 MOCK 모드로 동작해 전체 흐름을 시연할 수 있다.

- 응답 생성: chat.completions (OPENAI_CHAT_MODEL, 기본 gpt-4o-mini)
- 음성 → 글자: audio.transcriptions (OPENAI_STT_MODEL, 기본 gpt-4o-mini-transcribe). 브라우저 음성 인식이
  안 되는 환경에서 녹음 파일을 올릴 때만 쓴다.
- 요약: chat.completions. 의료 판정 표현은 프롬프트로 금지하고, 결과에서도 한 번 더 걸러낸다.
모든 호출은 ApiUsage 에 기록한다 (계약 §13).
"""
from __future__ import annotations
import os, re, json, logging
from typing import Any

log = logging.getLogger("dajeong.ai")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
STT_MODEL = os.getenv("OPENAI_STT_MODEL", "gpt-4o-mini-transcribe")
MOCK = not OPENAI_API_KEY or os.getenv("AI_MOCK") == "1"

FORBIDDEN = ["치매", "진단", "인지장애", "알츠하이머", "위험 점수", "질환"]

_client = None
def client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def scrub(text: str) -> str:
    """리포트에 의료 판정처럼 읽히는 단어가 섞이면 중립 표현으로 바꾼다."""
    out = text
    for w in FORBIDDEN:
        out = out.replace(w, "대화 변화")
    return out


def _log_usage(db, family_id, purpose, model, resp=None, ok=True, error=None, provider="openai"):
    from .models import ApiUsage
    try:
        u = getattr(resp, "usage", None)
        db.add(ApiUsage(family_id=family_id, provider=provider, purpose=purpose, model=model,
                        input_tokens=getattr(u, "prompt_tokens", 0) or getattr(u, "input_tokens", 0) or 0,
                        output_tokens=getattr(u, "completion_tokens", 0) or getattr(u, "output_tokens", 0) or 0,
                        ok=ok, error=error))
        db.commit()
    except Exception:   # 기록 실패가 본 기능을 막으면 안 된다
        log.exception("usage log failed")


# ---------- 가족 기록 검색 (가족별로만) ----------
def pick_memories(memories: list, text: str, history: list[dict], limit: int = 3) -> list:
    """부모 발화·최근 대화와 키워드가 겹치는 추억만 고른다. 겹치는 게 없으면 최근 등록 2개."""
    corpus = text + " " + " ".join(h["text"] for h in history[-4:])
    scored = []
    for m in memories:
        kws = list(m.keywords or []) + [m.title]
        score = sum(1 for k in kws if k and k in corpus)
        if score:
            scored.append((score, m))
    scored.sort(key=lambda x: -x[0])
    picked = [m for _, m in scored[:limit]]
    if not picked:
        picked = sorted(memories, key=lambda m: m.id, reverse=True)[:2]
    return picked


def persona_prompt(persona, memories: list) -> str:
    p = persona
    mem = "\n".join(f"- {m.title}{f' ({m.year})' if m.year else ''}: {m.detail}" for m in memories) or "- (등록된 기록 없음)"
    return f"""너는 돌봄 대화 서비스 '다정이'에서 자녀 '{p.display_name}'의 말투로 어머니/아버지와 전화하듯 대화한다.
- 부모님을 "{p.calls_parent}"라고 부른다. {p.formality}.
- 어미: {', '.join(p.endings) or '자연스럽게'} / 자주 쓰는 표현: {', '.join(p.expressions) or '없음'}
- 성격: {', '.join(p.personality) or '다정함'} / 습관: {' / '.join(p.habits) or '없음'}
- 가족 메모: {p.family_notes or '없음'}
규칙
- 한 번에 1~2문장, 50자 안팎. 소리로 읽히니 이모지·괄호·목록을 쓰지 않는다.
- 아래 [가족 기록]에 있는 사실만 말한다. 없는 일은 지어내지 말고 "그랬나? 엄마가 얘기해 줘"처럼 되묻는다.
- 피할 주제: {', '.join(p.avoid_topics) or '없음'}.
- 아프다, 넘어졌다, 숨이 차다 같은 위급한 말이 나오면 "지금 바로 119 부를까? 나도 바로 전화할게"라고 답한다.
- AI임을 숨기지 않는다. 진짜 자녀냐고 물으면 "{p.display_name}가 만든 다정이야"라고 답한다.
- 병명·진단·검사 결과를 말하지 않는다.
[가족 기록]
{mem}
답변 텍스트만 출력한다."""


def generate_reply(db, family_id: int, persona, memories: list, history: list[dict], parent_text: str) -> str:
    picked = pick_memories(memories, parent_text, history)
    if MOCK:
        _log_usage(db, family_id, "reply", "mock", provider="mock")
        return _mock_reply(persona, picked, parent_text, history)
    msgs = [{"role": "system", "content": persona_prompt(persona, picked)}]
    for h in history[-12:]:
        msgs.append({"role": "assistant" if h["speaker"] == "bot" else "user", "content": h["text"]})
    msgs.append({"role": "user", "content": parent_text})
    try:
        resp = client().chat.completions.create(model=CHAT_MODEL, messages=msgs, max_tokens=120, temperature=0.7)
        _log_usage(db, family_id, "reply", CHAT_MODEL, resp)
        return scrub(resp.choices[0].message.content.strip())
    except Exception as e:
        _log_usage(db, family_id, "reply", CHAT_MODEL, ok=False, error=str(e)[:300])
        raise


def transcribe(db, family_id: int, audio_bytes: bytes, filename: str) -> str:
    if MOCK:
        raise RuntimeError("MOCK 모드에서는 음성 파일 변환을 지원하지 않습니다. OPENAI_API_KEY를 설정하세요.")
    import io
    f = io.BytesIO(audio_bytes); f.name = filename
    try:
        resp = client().audio.transcriptions.create(model=STT_MODEL, file=f, language="ko")
        _log_usage(db, family_id, "stt", STT_MODEL, resp)
        return resp.text.strip()
    except Exception as e:
        _log_usage(db, family_id, "stt", STT_MODEL, ok=False, error=str(e)[:300])
        raise


SUMMARY_RULES = """규칙: 보호자(자녀)가 읽는 글이다. 3~5문장, 존댓말, 따뜻하고 담백하게.
수치는 아래 데이터에 있는 것만 쓰고, 병명·진단·검사 권유·위험 점수는 절대 쓰지 않는다.
'평소와 같아요 / 관찰이 필요해요 / 확인이 필요해요' 수준으로만 말하고, 마지막 문장은 보호자가 오늘 할 수 있는 작은 행동 하나를 제안한다."""


def summarize_conversation(db, family_id: int, persona, turns: list[dict], metrics: dict) -> str:
    if MOCK:
        _log_usage(db, family_id, "summary_conversation", "mock", provider="mock")
        return _mock_summary_conv(persona, turns, metrics)
    transcript = "\n".join(f"{'다정이' if t['speaker']=='bot' else '부모님'}: {t['text']}" for t in turns)
    prompt = f"""{SUMMARY_RULES}
[대화 지표] {json.dumps(metrics, ensure_ascii=False)}
[대화]
{transcript}
위 대화를 보호자에게 요약해 주세요."""
    return _chat(db, family_id, "summary", prompt)


def summarize_week(db, family_id: int, persona, week: dict, compare: dict | None, baseline_status: str) -> str:
    if MOCK:
        _log_usage(db, family_id, "summary_weekly", "mock", provider="mock")
        return _mock_summary_week(persona, week, compare, baseline_status)
    prompt = f"""{SUMMARY_RULES}
[최근 7일 지표] {json.dumps(week, ensure_ascii=False)}
[기준선 상태] {baseline_status}
[평소 대비 비교] {json.dumps(compare or {}, ensure_ascii=False)}
위 데이터를 바탕으로 지난 한 주를 보호자에게 요약해 주세요. 기준선이 '수집 중'이면 비교 표현은 쓰지 말고 이번 주 모습만 전해 주세요."""
    return _chat(db, family_id, "summary", prompt)


def _chat(db, family_id, purpose, prompt) -> str:
    try:
        resp = client().chat.completions.create(model=CHAT_MODEL, messages=[{"role": "user", "content": prompt}],
                                                max_tokens=400, temperature=0.5)
        _log_usage(db, family_id, purpose, CHAT_MODEL, resp)
        return scrub(resp.choices[0].message.content.strip())
    except Exception as e:
        _log_usage(db, family_id, purpose, CHAT_MODEL, ok=False, error=str(e)[:300])
        raise


# ---------- MOCK ----------
def _mock_reply(persona, picked, parent_text, history) -> str:
    name = persona.calls_parent
    t = parent_text
    if re.search(r"아프|넘어|숨이|어지러", t):
        return f"{name} 지금 바로 119 부를까? 나도 바로 전화할게."
    if re.search(r"진짜|로봇|AI|기계", t):
        return f"{persona.display_name}가 만든 다정이야, {persona.display_name} 목소리로 얘기하는 거야."
    if re.search(r"밥|먹었|식사", t):
        return f"잘했어 {name}~ 나도 방금 먹었지. 오늘은 뭐 했어?"
    if picked and len(history) % 3 == 2:
        m = picked[0]
        return f"{name}, {m.title} 기억나? {m.detail[:30]} 그때 생각나네."
    if re.search(r"글쎄|모르겠|기억", t):
        return f"괜찮아 {name}, 천천히 생각해도 돼. 오늘 날씨는 어때?"
    tails = ["그래서 오늘 기분은 어때?", "무릎은 요즘 좀 어때?", "경로당은 다녀왔어?", "오늘 뭐 먹고 싶어?"]
    return f"그렇구나 {name}. {tails[len(history) % len(tails)]}"


def _mock_summary_conv(persona, turns, m) -> str:
    n = m.get("parent_turns", 0)
    gap = m.get("avg_response_gap")
    s = [f"오늘 {persona.calls_parent}께서 다정이와 {n}번 말을 주고받으셨어요."]
    if gap is not None:
        s.append(f"대답은 평균 {gap:.1f}초 만에 이어졌고, 한 번에 평균 {m.get('avg_utterance_len', 0):.0f}글자 정도 말씀하셨어요.")
    if m.get("repeat_rate", 0) >= 0.3:
        s.append("같은 말씀을 몇 번 되풀이하신 대목이 있어요.")
    else:
        s.append("대화가 자연스럽게 이어졌어요.")
    if m.get("uncertain_rate", 0) >= 0.3:
        s.append("'글쎄' 같은 말씀이 평소보다 잦았어요.")
    s.append("오늘 저녁에 짧게 전화 한 통 드려 보시는 건 어떨까요?")
    return " ".join(s)


def _mock_summary_week(persona, week, compare, status) -> str:
    n = week.get("conversations", 0)
    s = [f"지난 7일 동안 {persona.calls_parent}께서 다정이와 {n}번 대화하셨어요."]
    if status != "ready":
        s.append("아직 평소 기준이 모이는 중이라 비교보다는 이번 주 모습만 전해드려요.")
    else:
        notable = [k for k, v in (compare or {}).items() if v["level"] != "same"]
        s.append("평소와 비슷한 한 주였어요." if not notable else "평소와 조금 다른 부분이 있어 지켜보면 좋겠어요.")
    s.append("이번 주말에는 좋아하시는 이야기로 길게 통화해 보세요.")
    return " ".join(s)
