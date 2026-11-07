"""시연·검수용 시드 데이터.  실행: cd server && python seed.py  (기존 DEMO1 가족이 있으면 지우고 다시 만든다)

가족 DEMO1 (보호자 비번 1234 / 태블릿 비번 0000) + 페르소나 + 추억 8개 + 최근 24일 대화 20건.
대화는 처음 2주가 '평소', 이후 조금 달라지는 흐름이라 기준선 고정과 비교 화면을 바로 볼 수 있다.
실존 인물이 아닌 가상 데이터다.
"""
import os, random, sys
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("RUN_JOBS", "0")
from app.db import Base, engine, SessionLocal
from app.models import Family, Persona, Memory, Conversation, Turn, Job, Baseline, Summary, ConversationMetric
from app.auth import hash_pw
from app import jobs

random.seed(7)
Base.metadata.create_all(engine)
db = SessionLocal()

old = db.query(Family).filter(Family.code == "DEMO1").first()
if old:
    for t in ["conversation_metrics", "baselines", "summaries", "jobs"]:
        pass
    db.query(Job).filter(Job.family_id == old.id).delete()
    db.query(Summary).filter(Summary.family_id == old.id).delete()
    db.query(Baseline).filter(Baseline.family_id == old.id).delete()
    db.delete(old); db.commit()

fam = Family(code="DEMO1", parent_name="김순자", parent_age=78, region="세종시 조치원읍", guardian_name="이민호", guardian_relation="아들",
             guardian_password=hash_pw("1234"), tablet_password=hash_pw("0000"))
db.add(fam); db.commit(); db.refresh(fam)
db.add(Persona(family_id=fam.id, display_name="민호", calls_parent="엄마", formality="반말 (가끔 존댓말 섞음)",
               endings=["~했어?", "~잖아", "~거든", "~해 봐"], expressions=["아이고 우리 엄마", "밥은 챙겨 먹었고?", "그니까~", "알았어 알았어"],
               personality=["장난스럽고 다정함", "걱정 많지만 티 안 내려 함"], habits=["통화 시작은 '엄마 뭐해~?'", "끝날 때 '또 전화할게'"],
               avoid_topics=["아버지 투병 과정", "돈 문제"],
               family_notes="남편 이정호(2019년 작고, 목수). 장남 민호(서울, 건설회사 과장), 며느리 박지현(초등교사), 손녀 서윤(10살, 피아노). 딸 수정(대전, 간호사)."))
MEMS = [
    ("대천 해수욕장 가족여행", "민호 10살 때. 아빠가 튜브 바람 넣다 쓰러질 뻔함", ["대천", "바다", "해수욕장", "여행"], 1988),
    ("엄마표 김치찌개", "돼지 앞다리살과 묵은지. 민호가 제일 좋아하는 음식", ["김치찌개", "찌개", "음식"], None),
    ("민호 대학 합격", "충남대 건축과. 엄마가 동네에 떡을 돌림", ["대학", "합격", "떡"], 1997),
    ("서윤이 태어난 날", "3월 14일, 눈 오던 날", ["서윤", "손녀", "눈"], 2016),
    ("올해 텃밭", "상추·고추·방울토마토 심음", ["텃밭", "상추", "고추", "토마토"], 2026),
    ("아빠가 만든 흔들의자", "거실에 있는 흔들의자는 아빠가 만든 것", ["의자", "흔들의자", "거실"], None),
    ("경로당 친구 영숙 할머니", "화·목 경로당에서 화투를 침", ["경로당", "영숙", "화투"], 2026),
    ("추석 계획", "올 추석에 민호네가 세종으로 내려옴", ["추석", "명절"], 2026),
]
for t, d, k, y in MEMS:
    db.add(Memory(family_id=fam.id, title=t, detail=d, keywords=k, year=y))
db.commit()

BOT = ["엄마 뭐해~? 밥은 챙겨 먹었어?", "오늘 텃밭에 뭐 심었다고 했지?", "경로당은 다녀왔어? 영숙 할머니도 오셨어?",
       "서윤이가 엄마 김치찌개 먹고 싶대.", "무릎은 요즘 좀 어때?", "엄마 사랑해, 또 전화할게."]
PARENT_OK = ["응 먹었지. 된장국에 밥 말아 먹었어. 너는?", "상추랑 고추랑, 서윤이 좋아하는 방울토마토도 심었지.",
             "갔다 왔지. 영숙이랑 화투 쳤어. 내가 이겼어.", "그려, 추석에 오면 끓여 줘야지. 앞다리살 사다 놓을게.",
             "조금 쑤시긴 한데 괜찮아. 파스 붙였어.", "그래 그래, 운전 조심하고."]
PARENT_WEAK = ["먹었나… 먹은 것 같은데.", "글쎄 뭐 심었더라. 상추였나.", "갔다 왔지. 영숙이랑 화투 쳤어. 갔다 왔지.",
               "그게 뭐더라. 응 끓여 줘야지.", "너 밥은 먹었니? 밥은 먹었어?", "그래, 또 전화해."]

now = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)
day_idx = 0
for d in range(24, -1, -1):
    if d in (22, 15, 9, 3):      # 빠진 날
        continue
    weak = d <= 6               # 최근 1주일은 조금 달라진 흐름
    start = now - timedelta(days=d, minutes=random.randint(0, 90))
    conv = Conversation(family_id=fam.id, started_at=start, source="seed", status="finished")
    db.add(conv); db.commit(); db.refresh(conv)
    t = start
    for i in range(6):
        bt = Turn(conversation_id=conv.id, speaker="bot", text=BOT[i], started_at=t, ended_at=t + timedelta(seconds=3)); db.add(bt)
        gap = random.uniform(2.8, 4.5) if weak else random.uniform(1.2, 2.4)
        ps = t + timedelta(seconds=3 + gap)
        text = (PARENT_WEAK if weak and i in (0, 1, 2, 4) else PARENT_OK)[i]
        db.add(Turn(conversation_id=conv.id, speaker="parent", text=text, started_at=ps, ended_at=ps + timedelta(seconds=len(text) * 0.18)))
        t = ps + timedelta(seconds=len(text) * 0.18 + random.uniform(0.5, 1.5))
    conv.ended_at = t; db.commit()
    jobs.analyze_conversation(db, conv.id)
    day_idx += 1

print("seeded family DEMO1 · conversations:", db.query(Conversation).filter(Conversation.family_id == fam.id).count(),
      "· baseline:", "fixed" if db.query(Baseline).filter(Baseline.family_id == fam.id).first() else "collecting")
db.close()
