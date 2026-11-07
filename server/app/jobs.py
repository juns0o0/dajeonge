"""뒤에서 도는 작업: 대화 분석(analyze), AI 요약(summarize).

Job 테이블을 2초마다 확인하는 스레드 1개. 실패하면 status=failed + error 를 남기고,
/api/jobs/{id}/retry 로 다시 큐에 넣는다. (서버 1대 기준. 규모가 커지면 Celery 등으로 교체)
"""
from __future__ import annotations
import logging, threading, time, traceback
from datetime import datetime, timedelta
from .db import SessionLocal
from .models import Job, Conversation, ConversationMetric, Baseline, Summary, Family
from . import metrics as M
from . import ai

log = logging.getLogger("dajeong.jobs")
MAX_ATTEMPTS = 3
_stop = threading.Event()


def enqueue(db, kind: str, ref_id: int, family_id: int) -> Job:
    j = Job(kind=kind, ref_id=ref_id, family_id=family_id); db.add(j); db.commit(); db.refresh(j)
    return j


def run_job(db, job: Job):
    job.status = "running"; job.attempts += 1; db.commit()
    try:
        if job.kind == "analyze":
            analyze_conversation(db, job.ref_id)
        elif job.kind == "summarize":
            make_summary(db, job.ref_id)
        else:
            raise ValueError(f"unknown job kind {job.kind}")
        job.status = "done"; job.error = None
    except Exception as e:
        log.error("job %s failed: %s", job.id, e)
        job.status = "failed" if job.attempts >= MAX_ATTEMPTS else "queued"
        job.error = (str(e) or e.__class__.__name__)[:500] + "\n" + traceback.format_exc()[-800:]
    db.commit()


def process_once() -> int:
    db = SessionLocal()
    try:
        jobs = db.query(Job).filter(Job.status == "queued").order_by(Job.id).limit(5).all()
        for j in jobs:
            run_job(db, j)
        return len(jobs)
    finally:
        db.close()


def worker():
    while not _stop.is_set():
        try:
            n = process_once()
        except Exception:
            log.exception("worker loop error"); n = 0
        time.sleep(0.5 if n else 2)


def start_worker():
    t = threading.Thread(target=worker, name="dajeong-jobs", daemon=True); t.start(); return t


def stop_worker():
    _stop.set()


# ---------- analyze ----------
def analyze_conversation(db, conversation_id: int):
    conv = db.get(Conversation, conversation_id)
    if not conv:
        raise ValueError("대화가 없습니다")
    turns = [M.TurnIn(t.speaker, t.text, t.started_at, t.ended_at) for t in conv.turns]
    m = M.compute_metrics(turns)
    # 부모 발화에 태그·간격 기록
    gaps = M.response_gaps(turns)
    pi = 0
    for t in conv.turns:
        if t.speaker == "parent":
            t.tags = m.tags[pi]; t.response_gap_sec = gaps[pi]; t.char_len = len(M.normalize(t.text)); pi += 1
    row = m.as_row()
    if conv.metric:
        for k, v in row.items(): setattr(conv.metric, k, v)
        conv.metric.computed_at = datetime.utcnow()
    else:
        db.add(ConversationMetric(conversation_id=conv.id, family_id=conv.family_id, **row))
    conv.status = "analyzed"; conv.error = None
    db.commit()
    refresh_baseline(db, conv.family_id)


def refresh_baseline(db, family_id: int):
    """기준선이 아직 없고 조건(14일·유효 5회)을 채우면 고정한다. 한 번 고정되면 바꾸지 않는다."""
    if db.query(Baseline).filter(Baseline.family_id == family_id).first():
        return
    rows = (db.query(ConversationMetric, Conversation.started_at)
              .join(Conversation, Conversation.id == ConversationMetric.conversation_id)
              .filter(ConversationMetric.family_id == family_id, ConversationMetric.valid == True)
              .order_by(Conversation.started_at).all())
    if not rows:
        return
    first = rows[0][1]
    if M.baseline_ready(first, len(rows), datetime.utcnow()):
        window = [r[0] for r in rows if r[1] <= first + timedelta(days=M.BASELINE_MIN_DAYS)] or [r[0] for r in rows[:M.BASELINE_MIN_CONVERSATIONS]]
        values = M.build_baseline([{k: getattr(x, k) for k in M.BASELINE_KEYS} for x in window])
        db.add(Baseline(family_id=family_id, n_conversations=len(window), values=values)); db.commit()


# ---------- summarize ----------
def week_stats(db, family_id: int, end: datetime | None = None) -> tuple[dict, datetime, datetime]:
    end = end or datetime.utcnow(); start = end - timedelta(days=7)
    rows = (db.query(ConversationMetric).join(Conversation, Conversation.id == ConversationMetric.conversation_id)
              .filter(ConversationMetric.family_id == family_id, Conversation.started_at >= start, Conversation.started_at <= end)
              .all())
    valid = [r for r in rows if r.valid]
    def mean(k):
        vals = [getattr(r, k) for r in valid if getattr(r, k) is not None]
        return round(sum(vals) / len(vals), 3) if vals else None
    week = {"conversations": len(rows), "valid_conversations": len(valid),
            "total_minutes": round(sum(r.duration_sec for r in rows) / 60, 1),
            **{k: mean(k) for k in M.BASELINE_KEYS}}
    return week, start, end


def baseline_info(db, family_id: int) -> dict:
    b = db.query(Baseline).filter(Baseline.family_id == family_id).first()
    rows = (db.query(Conversation.started_at).join(ConversationMetric, Conversation.id == ConversationMetric.conversation_id)
              .filter(ConversationMetric.family_id == family_id, ConversationMetric.valid == True)
              .order_by(Conversation.started_at).all())
    n = len(rows); first = rows[0][0] if rows else None
    days = (datetime.utcnow() - first).days if first else 0
    if b:
        return {"status": "ready", "fixed_at": b.fixed_at.isoformat(), "n_conversations": b.n_conversations, "values": b.values,
                "valid_conversations": n, "days": days}
    return {"status": "collecting", "valid_conversations": n, "need_conversations": M.BASELINE_MIN_CONVERSATIONS,
            "days": days, "need_days": M.BASELINE_MIN_DAYS, "values": None}


def make_summary(db, summary_id: int):
    s = db.get(Summary, summary_id)
    fam = db.get(Family, s.family_id); persona = fam.persona
    try:
        if s.kind == "conversation":
            conv = db.get(Conversation, s.conversation_id)
            if not conv or not conv.metric:
                raise ValueError("분석이 끝난 대화만 요약할 수 있어요.")
            turns = [{"speaker": t.speaker, "text": t.text} for t in conv.turns]
            metrics = {k: getattr(conv.metric, k) for k in ["parent_turns", "avg_utterance_len", "repeat_rate", "uncertain_rate", "avg_response_gap", "participation", "duration_sec"]}
            s.text = ai.summarize_conversation(db, fam.id, persona, turns, metrics)
        else:
            week, start, end = week_stats(db, fam.id, s.period_end)
            b = baseline_info(db, fam.id)
            compare = M.compare_to_baseline(week, b["values"]) if b["status"] == "ready" else None
            s.period_start, s.period_end = start, end
            s.text = ai.summarize_week(db, fam.id, persona, week, compare, b["status"])
        s.status = "done"; s.error = None; s.model = "mock" if ai.MOCK else ai.CHAT_MODEL
    except Exception as e:
        s.status = "failed"; s.error = str(e)[:500]; db.commit(); raise
    db.commit()
