"""다정이 MVP API 서버 (FastAPI). 실행: uvicorn app.main:app --reload  (server/ 에서)

- /api/...       : JSON API (Swagger: /docs)
- /api/admin/... : 백오피스·연동용 API (X-Admin-Token)
- /              : web/ 정적 파일 (랜딩·태블릿·보호자 앱·백오피스 admin.html)
"""
from __future__ import annotations
import os, logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DbSession

from .db import Base, engine, get_db
from .models import Family, Persona, Memory, Conversation, Turn, ConversationMetric, Baseline, Summary, Job, Application, ApiUsage, Session
from . import auth as A, ai, jobs, metrics as M

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("dajeong")

app = FastAPI(title="다정이 MVP API", version="0.1.0", docs_url=None, redoc_url=None,
              description="AI Care Bot ‘다정이’ MVP · 음성 대화 저장, 지표 분석, 보호자 대시보드, AI 요약")

def _openapi():   # 번들된 Swagger UI(4.x)가 읽을 수 있게 OpenAPI 3.0 버전 표기로 제공
    if not app.openapi_schema:
        from fastapi.openapi.utils import get_openapi
        sch = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
        sch["openapi"] = "3.0.3"; app.openapi_schema = sch
    return app.openapi_schema
app.openapi = _openapi

# Swagger UI 를 로컬 파일로 제공 (CDN 없이, 폐쇄망·태블릿 환경에서도 /docs 동작)
try:
    import swagger_ui_bundle
    from fastapi.openapi.docs import get_swagger_ui_html
    app.mount("/_swagger", StaticFiles(directory=str(swagger_ui_bundle.swagger_ui_path)), name="swagger")

    @app.get("/docs", include_in_schema=False)
    def swagger_docs():
        return get_swagger_ui_html(openapi_url="/openapi.json", title="다정이 MVP API 문서",
                                   swagger_js_url="/_swagger/swagger-ui-bundle.js", swagger_css_url="/_swagger/swagger-ui.css")
except ImportError:   # 패키지가 없으면 FastAPI 기본(CDN) 문서
    from fastapi.openapi.docs import get_swagger_ui_html

    @app.get("/docs", include_in_schema=False)
    def swagger_docs():
        return get_swagger_ui_html(openapi_url="/openapi.json", title="다정이 MVP API 문서")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","), allow_methods=["*"], allow_headers=["*"])

AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "./data/audio")); AUDIO_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR = Path(__file__).resolve().parents[2] / "web"


def _migrate():
    """create_all 은 기존 테이블에 컬럼을 추가하지 않으므로, 뒤에 추가된 컬럼만 ALTER 로 보강한다."""
    from sqlalchemy import inspect, text
    insp = inspect(engine)
    if "applications" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("applications")}
        with engine.begin() as con:
            if "status" not in cols: con.execute(text("ALTER TABLE applications ADD COLUMN status VARCHAR(12) DEFAULT 'new'"))
            if "note" not in cols: con.execute(text("ALTER TABLE applications ADD COLUMN note TEXT"))


@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine); _migrate()
    if os.getenv("RUN_JOBS", "1") == "1":
        jobs.start_worker()
    log.info("AI mode: %s", "MOCK" if ai.MOCK else ai.CHAT_MODEL)


@app.on_event("shutdown")
def shutdown():
    jobs.stop_worker()


@app.get("/api/health", tags=["system"])
def health():
    return {"ok": True, "ai": "mock" if ai.MOCK else ai.CHAT_MODEL, "time": datetime.utcnow().isoformat()}


# ---------------- 인증 ----------------
class LoginIn(BaseModel):
    code: str = Field(..., description="가족 코드 (예: DEMO1)")
    password: str
    role: Literal["guardian", "tablet"] = "guardian"


@app.post("/api/auth/login", tags=["auth"])
def api_login(body: LoginIn, db: DbSession = Depends(get_db)):
    token, fam = A.login(db, body.code, body.password, body.role)
    return {"token": token, "role": body.role, "family": family_out(fam)}


@app.post("/api/auth/logout", tags=["auth"])
def api_logout(auth: A.Auth = Depends(A.current), db: DbSession = Depends(get_db)):
    db.delete(auth.session); db.commit(); return {"ok": True}


# ---------------- 가족 / 페르소나 / 추억 ----------------
def family_out(f: Family) -> dict:
    return {"id": f.id, "code": f.code, "parent_name": f.parent_name, "parent_age": f.parent_age, "region": f.region,
            "guardian_name": f.guardian_name, "guardian_relation": f.guardian_relation, "keep_audio_days": f.keep_audio_days,
            "persona": persona_out(f.persona) if f.persona else None}


def persona_out(p: Persona) -> dict:
    return {"display_name": p.display_name, "calls_parent": p.calls_parent, "formality": p.formality, "endings": p.endings,
            "expressions": p.expressions, "personality": p.personality, "habits": p.habits, "avoid_topics": p.avoid_topics,
            "family_notes": p.family_notes}


class FamilyIn(BaseModel):
    parent_name: str | None = None
    parent_age: int | None = None
    region: str | None = None
    guardian_name: str | None = None
    guardian_relation: str | None = None
    keep_audio_days: int | None = None


class PersonaIn(BaseModel):
    display_name: str
    calls_parent: str = "엄마"
    formality: str = "반말 (가끔 존댓말 섞음)"
    endings: list[str] = []
    expressions: list[str] = []
    personality: list[str] = []
    habits: list[str] = []
    avoid_topics: list[str] = []
    family_notes: str = ""


class MemoryIn(BaseModel):
    title: str
    detail: str = ""
    keywords: list[str] = []
    year: int | None = None


@app.get("/api/family", tags=["family"])
def get_family(auth: A.Auth = Depends(A.current)):
    return family_out(auth.family)


@app.put("/api/family", tags=["family"])
def update_family(body: FamilyIn, auth: A.Auth = Depends(A.guardian_only), db: DbSession = Depends(get_db)):
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(auth.family, k, v)
    db.commit(); return family_out(auth.family)


@app.put("/api/family/persona", tags=["family"])
def update_persona(body: PersonaIn, auth: A.Auth = Depends(A.guardian_only), db: DbSession = Depends(get_db)):
    p = auth.family.persona or Persona(family_id=auth.family.id, display_name=body.display_name)
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    db.add(p); db.commit(); db.refresh(p); return persona_out(p)


@app.get("/api/family/memories", tags=["family"])
def list_memories(auth: A.Auth = Depends(A.current)):
    return [memory_out(m) for m in sorted(auth.family.memories, key=lambda m: -m.id)]


def memory_out(m: Memory) -> dict:
    return {"id": m.id, "title": m.title, "detail": m.detail, "keywords": m.keywords, "year": m.year, "created_at": m.created_at.isoformat()}


@app.post("/api/family/memories", tags=["family"], status_code=201)
def add_memory(body: MemoryIn, auth: A.Auth = Depends(A.guardian_only), db: DbSession = Depends(get_db)):
    m = Memory(family_id=auth.family.id, **body.model_dump()); db.add(m); db.commit(); db.refresh(m); return memory_out(m)


@app.put("/api/family/memories/{memory_id}", tags=["family"])
def edit_memory(memory_id: int, body: MemoryIn, auth: A.Auth = Depends(A.guardian_only), db: DbSession = Depends(get_db)):
    m = db.get(Memory, memory_id)
    if not m or m.family_id != auth.family.id:
        raise HTTPException(404, "기록이 없습니다.")
    for k, v in body.model_dump().items(): setattr(m, k, v)
    db.commit(); return memory_out(m)


@app.delete("/api/family/memories/{memory_id}", tags=["family"])
def delete_memory(memory_id: int, auth: A.Auth = Depends(A.guardian_only), db: DbSession = Depends(get_db)):
    m = db.get(Memory, memory_id)
    if not m or m.family_id != auth.family.id:
        raise HTTPException(404, "기록이 없습니다.")
    db.delete(m); db.commit(); return {"ok": True}


# ---------------- 대화 ----------------
class TurnIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    started_at: datetime | None = None   # 부모 발화 시작 시각(브라우저 기준, 없으면 서버 시각)
    ended_at: datetime | None = None
    input_mode: Literal["voice", "text"] = "voice"
    bot_spoke_until: datetime | None = None   # 직전 다정이 발화 재생이 끝난 시각 (응답 간격 계산용)


def conv_out(c: Conversation, with_turns=False) -> dict:
    d = {"id": c.id, "started_at": c.started_at.isoformat(), "ended_at": c.ended_at.isoformat() if c.ended_at else None,
         "status": c.status, "source": c.source, "error": c.error, "turn_count": len(c.turns),
         "parent_turns": sum(1 for t in c.turns if t.speaker == "parent"),
         "metric": metric_out(c.metric) if c.metric else None}
    if with_turns:
        d["turns"] = [{"id": t.id, "speaker": t.speaker, "text": t.text, "started_at": t.started_at.isoformat(),
                       "ended_at": t.ended_at.isoformat() if t.ended_at else None, "input_mode": t.input_mode,
                       "tags": t.tags, "response_gap_sec": t.response_gap_sec} for t in c.turns]
    return d


def metric_out(m: ConversationMetric) -> dict:
    return {k: getattr(m, k) for k in ["parent_turns", "avg_utterance_len", "repeat_rate", "uncertain_rate",
                                       "avg_response_gap", "participation", "duration_sec", "valid"]} | {"computed_at": m.computed_at.isoformat()}


def own_conversation(db, auth: A.Auth, conversation_id: int) -> Conversation:
    c = db.get(Conversation, conversation_id)
    if not c or c.family_id != auth.family.id:      # 다른 가족 기록 접근 차단
        raise HTTPException(404, "대화가 없습니다.")
    return c


@app.post("/api/conversations", tags=["conversation"], status_code=201)
def start_conversation(auth: A.Auth = Depends(A.current), db: DbSession = Depends(get_db)):
    """대화 시작. 다정이의 첫마디를 함께 돌려준다."""
    if not auth.family.persona:
        raise HTTPException(400, "페르소나가 아직 없어요. 보호자 앱에서 먼저 등록해 주세요.")
    c = Conversation(family_id=auth.family.id, source="tablet"); db.add(c); db.commit(); db.refresh(c)
    p = auth.family.persona
    greet = f"{p.calls_parent} 뭐해~? 밥은 챙겨 먹었어?"
    t = Turn(conversation_id=c.id, speaker="bot", text=greet, started_at=datetime.utcnow()); db.add(t); db.commit()
    return {"conversation": conv_out(c), "reply": {"turn_id": t.id, "text": greet}}


@app.post("/api/conversations/{conversation_id}/turns", tags=["conversation"])
def add_turn(conversation_id: int, body: TurnIn, auth: A.Auth = Depends(A.current), db: DbSession = Depends(get_db)):
    """부모님 발화 1개 저장 → 가족 기록 기반 다정이 응답 생성·저장 → 응답 텍스트 반환 (TTS는 브라우저)."""
    c = own_conversation(db, auth, conversation_id)
    if c.status != "open":
        raise HTTPException(400, "이미 끝난 대화예요.")
    now = datetime.utcnow()
    # 직전 bot 발화의 재생 종료 시각을 기록해 두면 응답 간격이 정확해진다
    last_bot = next((t for t in reversed(c.turns) if t.speaker == "bot"), None)
    if last_bot and body.bot_spoke_until and not last_bot.ended_at:
        last_bot.ended_at = body.bot_spoke_until.replace(tzinfo=None)
    started = (body.started_at or now).replace(tzinfo=None)
    pt = Turn(conversation_id=c.id, speaker="parent", text=body.text.strip(), started_at=started,
              ended_at=(body.ended_at or now).replace(tzinfo=None), input_mode=body.input_mode,
              char_len=len(M.normalize(body.text)))
    db.add(pt); db.commit()
    history = [{"speaker": t.speaker, "text": t.text} for t in c.turns]
    try:
        reply = ai.generate_reply(db, c.family_id, auth.family.persona, auth.family.memories, history[:-1], pt.text)
    except Exception as e:
        log.exception("reply failed")
        reply = f"{auth.family.persona.calls_parent}, 잠깐만. 내가 다시 말할게."   # API 실패 시에도 대화는 이어진다
        c.error = f"reply failed: {str(e)[:200]}"
    bt = Turn(conversation_id=c.id, speaker="bot", text=reply, started_at=datetime.utcnow()); db.add(bt); db.commit()
    return {"parent_turn_id": pt.id, "reply": {"turn_id": bt.id, "text": reply}}


@app.post("/api/conversations/{conversation_id}/audio", tags=["conversation"])
async def upload_audio(conversation_id: int, file: UploadFile = File(...), auth: A.Auth = Depends(A.current), db: DbSession = Depends(get_db)):
    """브라우저 음성 인식이 안 되는 환경용: 녹음 파일을 올리면 서버에서 글자로 바꿔 돌려준다 (저장만, 발화 등록은 /turns)."""
    c = own_conversation(db, auth, conversation_id)
    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(413, "25MB 이하 파일만 올릴 수 있어요.")
    path = AUDIO_DIR / f"fam{c.family_id}_conv{c.id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
    path.write_bytes(data); c.audio_path = str(path); db.commit()
    try:
        text = ai.transcribe(db, c.family_id, data, file.filename or "audio.webm")
    except Exception as e:
        raise HTTPException(502, f"음성 변환에 실패했어요: {str(e)[:200]}")
    return {"text": text, "audio_path": path.name}


@app.post("/api/conversations/{conversation_id}/finish", tags=["conversation"])
def finish_conversation(conversation_id: int, auth: A.Auth = Depends(A.current), db: DbSession = Depends(get_db)):
    """대화 종료 → 분석 작업(analyze)을 큐에 넣는다."""
    c = own_conversation(db, auth, conversation_id)
    if c.status == "open":
        c.status = "finished"; c.ended_at = datetime.utcnow(); db.commit()
    j = jobs.enqueue(db, "analyze", c.id, c.family_id)
    return {"conversation": conv_out(c), "job_id": j.id}


@app.get("/api/conversations", tags=["conversation"])
def list_conversations(limit: int = Query(30, le=200), auth: A.Auth = Depends(A.current), db: DbSession = Depends(get_db)):
    rows = db.query(Conversation).filter(Conversation.family_id == auth.family.id).order_by(Conversation.started_at.desc()).limit(limit).all()
    return [conv_out(c) for c in rows]


@app.get("/api/conversations/{conversation_id}", tags=["conversation"])
def get_conversation(conversation_id: int, auth: A.Auth = Depends(A.current), db: DbSession = Depends(get_db)):
    return conv_out(own_conversation(db, auth, conversation_id), with_turns=True)


@app.delete("/api/conversations/{conversation_id}", tags=["conversation"])
def delete_conversation(conversation_id: int, auth: A.Auth = Depends(A.guardian_only), db: DbSession = Depends(get_db)):
    """운영자(보호자) 삭제 절차: 대화·발화·지표·음성 파일을 함께 지운다 (계약 §13)."""
    c = own_conversation(db, auth, conversation_id)
    if c.audio_path and Path(c.audio_path).exists():
        Path(c.audio_path).unlink()
    db.delete(c); db.commit(); return {"ok": True}


# ---------------- 대시보드 ----------------
@app.get("/api/dashboard/overview", tags=["dashboard"])
def dashboard_overview(auth: A.Auth = Depends(A.current), db: DbSession = Depends(get_db)):
    """최근 7일 지표 + 개인 기준선 + 비교 + 14일 일별 추이."""
    fid = auth.family.id
    week, start, end = jobs.week_stats(db, fid)
    b = jobs.baseline_info(db, fid)
    compare = M.compare_to_baseline(week, b["values"]) if b["status"] == "ready" else None
    # 일별 추이 (최근 14일)
    since = end - timedelta(days=14)
    rows = (db.query(Conversation, ConversationMetric).join(ConversationMetric, ConversationMetric.conversation_id == Conversation.id)
              .filter(Conversation.family_id == fid, Conversation.started_at >= since).order_by(Conversation.started_at).all())
    daily: dict[str, dict] = {}
    for c, m in rows:
        d = daily.setdefault(c.started_at.date().isoformat(), {"conversations": 0, "minutes": 0.0, "avg_utterance_len": [], "repeat_rate": [], "avg_response_gap": [], "participation": []})
        d["conversations"] += 1; d["minutes"] += m.duration_sec / 60
        for k in ["avg_utterance_len", "repeat_rate", "avg_response_gap", "participation"]:
            if getattr(m, k) is not None: d[k].append(getattr(m, k))
    series = []
    for i in range(14, -1, -1):
        day = (end - timedelta(days=i)).date().isoformat(); d = daily.get(day)
        series.append({"date": day, "conversations": d["conversations"] if d else 0, "minutes": round(d["minutes"], 1) if d else 0,
                       **{k: (round(sum(d[k]) / len(d[k]), 2) if d and d[k] else None) for k in ["avg_utterance_len", "repeat_rate", "avg_response_gap", "participation"]}})
    last = db.query(Conversation).filter(Conversation.family_id == fid).order_by(Conversation.started_at.desc()).first()
    return {"family": family_out(auth.family), "period": {"start": start.isoformat(), "end": end.isoformat()},
            "week": week, "baseline": b, "compare": compare, "series": series,
            "last_conversation": conv_out(last) if last else None,
            "metric_labels": METRIC_LABELS}


METRIC_LABELS = {
    "avg_utterance_len": {"name": "발화 길이", "unit": "글자", "how": "부모님 발화 한 번의 글자 수(공백 제외) 평균", "higher_is_better": True},
    "repeat_rate": {"name": "동일 표현 반복률", "unit": "%", "how": "한 대화 안에서 앞서 한 말과 비슷한(글자 2-gram 유사도 0.7 이상) 발화 비율", "higher_is_better": False},
    "uncertain_rate": {"name": "불확실 표현 비율", "unit": "%", "how": "‘글쎄’, ‘기억이 안 나’ 같은 표현이 들어간 발화 비율", "higher_is_better": False},
    "avg_response_gap": {"name": "응답 간격", "unit": "초", "how": "다정이 말이 끝난 뒤 부모님이 말을 시작하기까지 걸린 시간 평균", "higher_is_better": False},
    "participation": {"name": "대화 참여", "unit": "%", "how": "전체 대화 글자 수 중 부모님 발화가 차지하는 비중", "higher_is_better": True},
}


# ---------------- AI 요약 ----------------
class SummaryReq(BaseModel):
    kind: Literal["conversation", "weekly"]
    conversation_id: int | None = None


def summary_out(s: Summary) -> dict:
    return {"id": s.id, "kind": s.kind, "conversation_id": s.conversation_id, "status": s.status, "text": s.text, "error": s.error,
            "model": s.model, "period_start": s.period_start.isoformat() if s.period_start else None,
            "period_end": s.period_end.isoformat() if s.period_end else None, "created_at": s.created_at.isoformat()}


@app.post("/api/summaries", tags=["summary"], status_code=201)
def request_summary(body: SummaryReq, auth: A.Auth = Depends(A.guardian_only), db: DbSession = Depends(get_db)):
    """보호자가 버튼을 눌러 요약을 요청한다 (자동 생성 없음). 결과는 GET /api/summaries/{id} 로 확인."""
    if body.kind == "conversation":
        if not body.conversation_id:
            raise HTTPException(400, "conversation_id가 필요해요.")
        own_conversation(db, auth, body.conversation_id)
    s = Summary(family_id=auth.family.id, kind=body.kind, conversation_id=body.conversation_id,
                period_end=datetime.utcnow() if body.kind == "weekly" else None)
    db.add(s); db.commit(); db.refresh(s)
    j = jobs.enqueue(db, "summarize", s.id, auth.family.id)
    return {"summary": summary_out(s), "job_id": j.id}


@app.get("/api/summaries", tags=["summary"])
def list_summaries(kind: str | None = None, conversation_id: int | None = None, auth: A.Auth = Depends(A.current), db: DbSession = Depends(get_db)):
    q = db.query(Summary).filter(Summary.family_id == auth.family.id)
    if kind: q = q.filter(Summary.kind == kind)
    if conversation_id: q = q.filter(Summary.conversation_id == conversation_id)
    return [summary_out(s) for s in q.order_by(Summary.id.desc()).limit(20).all()]


@app.get("/api/summaries/{summary_id}", tags=["summary"])
def get_summary(summary_id: int, auth: A.Auth = Depends(A.current), db: DbSession = Depends(get_db)):
    s = db.get(Summary, summary_id)
    if not s or s.family_id != auth.family.id:
        raise HTTPException(404, "요약이 없습니다.")
    return summary_out(s)


# ---------------- 작업(잡) ----------------
def job_out(j: Job) -> dict:
    return {"id": j.id, "kind": j.kind, "ref_id": j.ref_id, "status": j.status, "attempts": j.attempts, "error": j.error,
            "created_at": j.created_at.isoformat(), "updated_at": j.updated_at.isoformat()}


@app.get("/api/jobs", tags=["jobs"])
def list_jobs(status: str | None = None, auth: A.Auth = Depends(A.current), db: DbSession = Depends(get_db)):
    q = db.query(Job).filter(Job.family_id == auth.family.id)
    if status: q = q.filter(Job.status == status)
    return [job_out(j) for j in q.order_by(Job.id.desc()).limit(50).all()]


@app.get("/api/jobs/{job_id}", tags=["jobs"])
def get_job(job_id: int, auth: A.Auth = Depends(A.current), db: DbSession = Depends(get_db)):
    j = db.get(Job, job_id)
    if not j or j.family_id != auth.family.id:
        raise HTTPException(404, "작업이 없습니다.")
    return job_out(j)


@app.post("/api/jobs/{job_id}/retry", tags=["jobs"])
def retry_job(job_id: int, auth: A.Auth = Depends(A.guardian_only), db: DbSession = Depends(get_db)):
    j = db.get(Job, job_id)
    if not j or j.family_id != auth.family.id:
        raise HTTPException(404, "작업이 없습니다.")
    j.status = "queued"; j.attempts = 0; j.error = None
    if j.kind == "summarize":
        s = db.get(Summary, j.ref_id)
        if s: s.status = "pending"; s.error = None
    db.commit(); return job_out(j)


# ---------------- 랜딩페이지 신청 ----------------
class ApplicationIn(BaseModel):
    kind: Literal["home", "org"]
    name: str = Field(..., min_length=1, max_length=50)
    org_name: str | None = None
    phone: str = Field(..., min_length=8, max_length=30)
    email: str | None = None
    region: str | None = None
    message: str | None = None
    agreed: bool


@app.post("/api/applications", tags=["landing"], status_code=201)
def create_application(body: ApplicationIn, db: DbSession = Depends(get_db)):
    if not body.agreed:
        raise HTTPException(400, "개인정보 수집·이용에 동의해 주세요.")
    a = Application(**body.model_dump()); db.add(a); db.commit(); db.refresh(a)
    return {"id": a.id, "created_at": a.created_at.isoformat()}


# ---------------- 관리자 ----------------
class FamilyCreate(BaseModel):
    code: str
    parent_name: str
    parent_age: int | None = None
    region: str | None = None
    guardian_name: str
    guardian_relation: str = "자녀"
    guardian_password: str
    tablet_password: str
    persona: PersonaIn | None = None


@app.post("/api/admin/families", tags=["admin"], status_code=201, dependencies=[Depends(A.admin_only)])
def admin_create_family(body: FamilyCreate, db: DbSession = Depends(get_db)):
    if db.query(Family).filter(Family.code == body.code.upper()).first():
        raise HTTPException(409, "이미 있는 가족 코드예요.")
    f = Family(code=body.code.upper(), parent_name=body.parent_name, parent_age=body.parent_age, region=body.region,
               guardian_name=body.guardian_name, guardian_relation=body.guardian_relation,
               guardian_password=A.hash_pw(body.guardian_password), tablet_password=A.hash_pw(body.tablet_password))
    db.add(f); db.commit(); db.refresh(f)
    if body.persona:
        db.add(Persona(family_id=f.id, **body.persona.model_dump())); db.commit(); db.refresh(f)
    return family_out(f)


# ---------------- 백오피스 · 연동용 API (X-Admin-Token) ----------------
# 가족·대화·신청·작업·사용량을 가족 경계 없이 조회·관리한다. 외부 시스템(기관 관리 도구, 알림 발송 등)은 같은 API 로 연동한다.

def _family_summary(f: Family, db) -> dict:
    last = db.query(Conversation).filter(Conversation.family_id == f.id).order_by(Conversation.started_at.desc()).first()
    b = db.query(Baseline).filter(Baseline.family_id == f.id).first()
    return family_out(f) | {"conversations": len(f.conversations), "memories": len(f.memories),
                            "last_conversation_at": last.started_at.isoformat() if last else None,
                            "baseline_fixed_at": b.fixed_at.isoformat() if b else None,
                            "created_at": f.created_at.isoformat()}


@app.get("/api/admin/stats", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_stats(db: DbSession = Depends(get_db)):
    """백오피스 현황 카드: 가족·대화·신청·작업·외부 API 호출 수."""
    now = datetime.utcnow(); week = now - timedelta(days=7)
    usage = db.query(ApiUsage).filter(ApiUsage.created_at >= week).all()
    return {"families": db.query(Family).count(),
            "conversations": db.query(Conversation).count(),
            "conversations_7d": db.query(Conversation).filter(Conversation.started_at >= week).count(),
            "baselines_fixed": db.query(Baseline).count(),
            "applications_new": db.query(Application).filter(Application.status == "new").count(),
            "jobs_queued": db.query(Job).filter(Job.status.in_(["queued", "running"])).count(),
            "jobs_failed": db.query(Job).filter(Job.status == "failed").count(),
            "api_calls_7d": len(usage), "api_errors_7d": sum(1 for u in usage if not u.ok),
            "mock": ai.MOCK, "server_time": now.isoformat()}


@app.get("/api/admin/families", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_list_families(q: str | None = None, db: DbSession = Depends(get_db)):
    fams = db.query(Family).order_by(Family.id.desc()).all()
    if q:
        q = q.strip().lower()
        fams = [f for f in fams if q in f.code.lower() or q in f.parent_name.lower() or q in (f.guardian_name or "").lower()]
    return [_family_summary(f, db) for f in fams]


@app.get("/api/admin/families/{family_id}", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_get_family(family_id: int, db: DbSession = Depends(get_db)):
    f = db.get(Family, family_id)
    if not f: raise HTTPException(404, "가족이 없습니다.")
    convs = db.query(Conversation).filter(Conversation.family_id == f.id).order_by(Conversation.started_at.desc()).limit(30).all()
    jobs_ = db.query(Job).filter(Job.family_id == f.id).order_by(Job.id.desc()).limit(20).all()
    return _family_summary(f, db) | {"memories_list": [memory_out(m) for m in f.memories],
                                     "baseline": jobs.baseline_info(db, f.id),
                                     "conversations_list": [conv_out(c) for c in convs],
                                     "jobs": [job_out(j) for j in jobs_]}


class FamilyAdminUpdate(BaseModel):
    parent_name: str | None = None
    parent_age: int | None = None
    region: str | None = None
    guardian_name: str | None = None
    guardian_relation: str | None = None
    keep_audio_days: int | None = Field(default=None, ge=0, le=365)
    guardian_password: str | None = Field(default=None, min_length=4)   # 넣으면 재설정
    tablet_password: str | None = Field(default=None, min_length=4)


@app.put("/api/admin/families/{family_id}", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_update_family(family_id: int, body: FamilyAdminUpdate, db: DbSession = Depends(get_db)):
    f = db.get(Family, family_id)
    if not f: raise HTTPException(404, "가족이 없습니다.")
    for k, v in body.model_dump(exclude_none=True).items():
        if k.endswith("_password"): setattr(f, k, A.hash_pw(v))
        else: setattr(f, k, v)
    db.commit(); db.refresh(f); return _family_summary(f, db)


@app.delete("/api/admin/families/{family_id}", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_delete_family(family_id: int, db: DbSession = Depends(get_db)):
    """가족 삭제(운영자 삭제 절차). 대화·발화·지표·기준선·요약·작업·세션·음성 파일을 함께 지운다."""
    f = db.get(Family, family_id)
    if not f: raise HTTPException(404, "가족이 없습니다.")
    for c in f.conversations:
        if c.audio_path and Path(c.audio_path).exists():
            try: Path(c.audio_path).unlink()
            except OSError: pass
    for model in (Baseline, Summary, Job, Session):
        db.query(model).filter(model.family_id == f.id).delete()
    db.delete(f); db.commit()
    return {"deleted": family_id}


@app.get("/api/admin/families/{family_id}/export", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_export_family(family_id: int, db: DbSession = Depends(get_db)):
    """가족 1곳의 전체 기록을 JSON 한 벌로 내보낸다 (이관·외부 분석 연동용)."""
    f = db.get(Family, family_id)
    if not f: raise HTTPException(404, "가족이 없습니다.")
    convs = db.query(Conversation).filter(Conversation.family_id == f.id).order_by(Conversation.id).all()
    sums = db.query(Summary).filter(Summary.family_id == f.id).order_by(Summary.id).all()
    return {"exported_at": datetime.utcnow().isoformat(), "family": family_out(f),
            "memories": [memory_out(m) for m in f.memories], "baseline": jobs.baseline_info(db, f.id),
            "conversations": [conv_out(c, with_turns=True) for c in convs], "summaries": [summary_out(s) for s in sums]}


@app.get("/api/admin/conversations", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_list_conversations(family_id: int | None = None, status: str | None = None, limit: int = Query(50, le=500), db: DbSession = Depends(get_db)):
    q = db.query(Conversation)
    if family_id: q = q.filter(Conversation.family_id == family_id)
    if status: q = q.filter(Conversation.status == status)
    rows = q.order_by(Conversation.started_at.desc()).limit(limit).all()
    return [conv_out(c) | {"family_id": c.family_id, "family_code": c.family.code} for c in rows]


@app.get("/api/admin/conversations/{conversation_id}", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_get_conversation(conversation_id: int, db: DbSession = Depends(get_db)):
    c = db.get(Conversation, conversation_id)
    if not c: raise HTTPException(404, "대화가 없습니다.")
    return conv_out(c, with_turns=True) | {"family_id": c.family_id, "family_code": c.family.code}


@app.get("/api/admin/jobs", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_list_jobs(status: str | None = None, limit: int = Query(100, le=500), db: DbSession = Depends(get_db)):
    q = db.query(Job)
    if status: q = q.filter(Job.status == status)
    codes = {f.id: f.code for f in db.query(Family).all()}
    return [job_out(j) | {"family_id": j.family_id, "family_code": codes.get(j.family_id)} for j in q.order_by(Job.id.desc()).limit(limit).all()]


@app.post("/api/admin/jobs/{job_id}/retry", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_retry_job(job_id: int, db: DbSession = Depends(get_db)):
    j = db.get(Job, job_id)
    if not j: raise HTTPException(404, "작업이 없습니다.")
    j.status = "queued"; j.attempts = 0; j.error = None
    if j.kind == "summarize":
        s = db.get(Summary, j.ref_id)
        if s: s.status = "pending"; s.error = None
    db.commit(); return job_out(j)


def application_out(a: Application) -> dict:
    return {"id": a.id, "kind": a.kind, "name": a.name, "org_name": a.org_name, "phone": a.phone, "email": a.email,
            "region": a.region, "message": a.message, "agreed": a.agreed, "status": a.status or "new", "note": a.note,
            "created_at": a.created_at.isoformat()}


@app.get("/api/admin/applications", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_list_applications(status: str | None = None, db: DbSession = Depends(get_db)):
    q = db.query(Application)
    if status: q = q.filter(Application.status == status)
    return [application_out(a) for a in q.order_by(Application.id.desc()).all()]


class ApplicationUpdate(BaseModel):
    status: Literal["new", "contacted", "done"] | None = None
    note: str | None = Field(default=None, max_length=1000)


@app.put("/api/admin/applications/{application_id}", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_update_application(application_id: int, body: ApplicationUpdate, db: DbSession = Depends(get_db)):
    a = db.get(Application, application_id)
    if not a: raise HTTPException(404, "신청이 없습니다.")
    if body.status: a.status = body.status
    if body.note is not None: a.note = body.note
    db.commit(); return application_out(a)


@app.get("/api/admin/usage", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_usage(days: int = 30, db: DbSession = Depends(get_db)):
    """외부 API 사용량·오류 집계 (계약 §13)."""
    since = datetime.utcnow() - timedelta(days=days)
    rows = db.query(ApiUsage).filter(ApiUsage.created_at >= since).all()
    agg: dict[str, dict] = {}
    for r in rows:
        a = agg.setdefault(r.purpose, {"calls": 0, "errors": 0, "input_tokens": 0, "output_tokens": 0})
        a["calls"] += 1; a["errors"] += (0 if r.ok else 1); a["input_tokens"] += r.input_tokens; a["output_tokens"] += r.output_tokens
    failed_jobs = db.query(Job).filter(Job.status == "failed").count()
    return {"days": days, "by_purpose": agg, "failed_jobs": failed_jobs, "mock": ai.MOCK}


@app.get("/api/admin/usage/log", tags=["admin"], dependencies=[Depends(A.admin_only)])
def admin_usage_log(limit: int = Query(50, le=500), db: DbSession = Depends(get_db)):
    rows = db.query(ApiUsage).order_by(ApiUsage.id.desc()).limit(limit).all()
    return [{"id": r.id, "family_id": r.family_id, "provider": r.provider, "purpose": r.purpose, "model": r.model,
             "input_tokens": r.input_tokens, "output_tokens": r.output_tokens, "ok": r.ok, "error": r.error,
             "created_at": r.created_at.isoformat()} for r in rows]


# ---------------- 정적 파일 (web/) ----------------
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
