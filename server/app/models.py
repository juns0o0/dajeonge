"""데이터 모델 (ERD는 docs/03_ERD.md 참고).

이번 과업 범위 밖이지만 향후 연결 위치만 잡아 둔 항목은 `reserved_*` 로 표시했다.
"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


def now():
    return datetime.utcnow()


class Family(Base):
    """가족 1단위 = 부모님 1명 + 보호자들. 모든 기록은 family_id로 격리한다."""
    __tablename__ = "families"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)       # 로그인용 가족 코드
    parent_name: Mapped[str] = mapped_column(String(50))
    parent_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    guardian_name: Mapped[str] = mapped_column(String(50))
    guardian_relation: Mapped[str] = mapped_column(String(30), default="자녀")
    guardian_password: Mapped[str] = mapped_column(String(128))                  # 보호자 앱 로그인 (해시)
    tablet_password: Mapped[str] = mapped_column(String(128))                    # 태블릿 로그인 (해시)
    keep_audio_days: Mapped[int] = mapped_column(Integer, default=30)            # 음성 보관 기간 (계약 §13)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    persona: Mapped["Persona"] = relationship(back_populates="family", uselist=False, cascade="all, delete-orphan")
    memories: Mapped[list["Memory"]] = relationship(back_populates="family", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="family", cascade="all, delete-orphan")


class Persona(Base):
    """자녀 페르소나: 호칭·관계·말투. 대화 생성 프롬프트에 그대로 들어간다."""
    __tablename__ = "personas"
    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), unique=True)
    display_name: Mapped[str] = mapped_column(String(30))            # 예: 민호
    calls_parent: Mapped[str] = mapped_column(String(20), default="엄마")
    formality: Mapped[str] = mapped_column(String(100), default="반말")
    endings: Mapped[list] = mapped_column(JSON, default=list)        # 자주 쓰는 어미
    expressions: Mapped[list] = mapped_column(JSON, default=list)    # 자주 쓰는 표현
    personality: Mapped[list] = mapped_column(JSON, default=list)
    habits: Mapped[list] = mapped_column(JSON, default=list)
    avoid_topics: Mapped[list] = mapped_column(JSON, default=list)
    family_notes: Mapped[str] = mapped_column(Text, default="")      # 가족 관계 메모 (자유 텍스트)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    family: Mapped[Family] = relationship(back_populates="persona")


class Memory(Base):
    """확인된 추억·생활 정보. 응답 생성 시 관련 항목만 골라 넣는다(가족별 검색)."""
    __tablename__ = "memories"
    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    title: Mapped[str] = mapped_column(String(100))
    detail: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[list] = mapped_column(JSON, default=list)       # 검색용 키워드
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # reserved: 기억 회상 확인 질문·정답 (이번 범위 밖, 연결 위치만 확보)
    reserved_recall_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)

    family: Mapped[Family] = relationship(back_populates="memories")


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="tablet")   # tablet | upload | seed
    status: Mapped[str] = mapped_column(String(20), default="open")     # open | finished | analyzed | failed
    audio_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    family: Mapped[Family] = relationship(back_populates="conversations")
    turns: Mapped[list["Turn"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", order_by="Turn.id")
    metric: Mapped["ConversationMetric"] = relationship(back_populates="conversation", uselist=False, cascade="all, delete-orphan")


class Turn(Base):
    """발화 1개. 부모님 발화에는 분류 태그가 붙는다."""
    __tablename__ = "turns"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    speaker: Mapped[str] = mapped_column(String(10))                 # bot | parent
    text: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    input_mode: Mapped[str] = mapped_column(String(10), default="voice")  # voice | text
    tags: Mapped[list] = mapped_column(JSON, default=list)            # repeat | uncertain
    char_len: Mapped[int] = mapped_column(Integer, default=0)
    response_gap_sec: Mapped[float | None] = mapped_column(Float, nullable=True)  # 직전 bot 발화 종료 → 이 발화 시작
    # reserved: 기억 회상 결과 (이번 범위 밖)
    reserved_recall_result: Mapped[str | None] = mapped_column(String(10), nullable=True)

    conversation: Mapped[Conversation] = relationship(back_populates="turns")


class ConversationMetric(Base):
    """대화 1건의 지표. metrics.py 의 compute_metrics 결과."""
    __tablename__ = "conversation_metrics"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), unique=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    parent_turns: Mapped[int] = mapped_column(Integer, default=0)
    avg_utterance_len: Mapped[float] = mapped_column(Float, default=0)   # 발화 길이 (글자 수 평균)
    repeat_rate: Mapped[float] = mapped_column(Float, default=0)          # 동일 표현 반복률 (0~1)
    uncertain_rate: Mapped[float] = mapped_column(Float, default=0)       # 불확실 표현 비율 (0~1)
    avg_response_gap: Mapped[float | None] = mapped_column(Float, nullable=True)  # 응답 간격 평균(초)
    participation: Mapped[float] = mapped_column(Float, default=0)        # 대화 참여 지표 (부모 발화 비중 0~1)
    duration_sec: Mapped[float] = mapped_column(Float, default=0)
    valid: Mapped[bool] = mapped_column(Boolean, default=True)            # 부모 발화 3회 이상이면 유효 대화
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    # reserved: 일관성 점수 (이번 범위 밖)
    reserved_consistency: Mapped[float | None] = mapped_column(Float, nullable=True)

    conversation: Mapped[Conversation] = relationship(back_populates="metric")


class Baseline(Base):
    """개인 기준선: 첫 유효 대화 후 14일 경과 + 유효 대화 5회 이상이면 고정."""
    __tablename__ = "baselines"
    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), unique=True)
    fixed_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    n_conversations: Mapped[int] = mapped_column(Integer)
    values: Mapped[dict] = mapped_column(JSON)      # {metric: {"mean":..,"sd":..}}


class Summary(Base):
    """보호자가 버튼으로 생성하는 AI 요약 (대화 1건 / 주간)."""
    __tablename__ = "summaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))                    # conversation | weekly
    conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id"), nullable=True)
    period_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")   # pending | done | failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Job(Base):
    """뒤에서 도는 작업(분석·요약). 실패하면 상태·오류를 남기고 재시도할 수 있다."""
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(30))                    # analyze | summarize
    ref_id: Mapped[int] = mapped_column(Integer)                     # conversation_id 또는 summary_id
    family_id: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")  # queued | running | done | failed
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class ApiUsage(Base):
    """외부 API 호출 기록 (계약 §13: 오류·API 사용량 기록)."""
    __tablename__ = "api_usage"
    id: Mapped[int] = mapped_column(primary_key=True)
    family_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider: Mapped[str] = mapped_column(String(20))     # openai
    purpose: Mapped[str] = mapped_column(String(30))      # reply | stt | tags | summary
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Application(Base):
    """랜딩페이지 신청 (가정용 / 기관용)."""
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(10))         # home | org
    name: Mapped[str] = mapped_column(String(50))
    org_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    agreed: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(12), default="new")   # new | contacted | done (백오피스에서 변경)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)     # 운영자 메모
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Session(Base):
    """로그인 토큰."""
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    family_id: Mapped[int] = mapped_column(Integer, index=True)
    role: Mapped[str] = mapped_column(String(10))        # guardian | tablet
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
