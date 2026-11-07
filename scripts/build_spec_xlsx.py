"""기능명세서 엑셀 생성.  실행: python3 scripts/build_spec_xlsx.py  →  docs/다정이_MVP_기능명세서.xlsx

시트: 1.기능명세 · 2.정보구조(IA) · 3.화면목록 · 4.API목록(docs/openapi.json 에서 자동) · 5.테이블정의(models.py 에서 자동)
"""
import json, os, sys
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "server"))
FONT = "맑은 고딕"
f = lambda **k: Font(name=FONT, size=k.pop("size", 10), **k)
thin = Side(style="thin", color="C4CBC0"); box = Border(left=thin, right=thin, top=thin, bottom=thin)
HEAD = PatternFill("solid", fgColor="17191B"); SUB = PatternFill("solid", fgColor="EAF7C0")
wrap = Alignment(wrap_text=True, vertical="top")

wb = Workbook(); wb.remove(wb.active)

def sheet(name, headers, rows, widths, note=None):
    ws = wb.create_sheet(name); ws.sheet_view.showGridLines = False
    ws["A1"] = f"다정이 MVP {name}"; ws["A1"].font = f(size=14, bold=True)
    ws["A2"] = note or "작업지시서 R4(2026.11.04) 기준 · 수행: 펄스픽시아"; ws["A2"].font = f(size=9, color="6B7280")
    for i, h in enumerate(headers, 1):
        c = ws.cell(4, i, h); c.font = Font(name=FONT, size=10, bold=True, color="CBEF5C"); c.fill = HEAD; c.border = box; c.alignment = Alignment(vertical="center", wrap_text=True)
    for r, row in enumerate(rows, 5):
        for i, v in enumerate(row, 1):
            c = ws.cell(r, i, v); c.font = f(); c.border = box; c.alignment = wrap
            if isinstance(v, str) and v.startswith("§"):
                c.fill = SUB; c.font = f(bold=True)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A5"; ws.row_dimensions[4].height = 28
    return ws

# ---------- 1. 기능명세 ----------
F = [
 ("§ F1 음성 대화와 저장 (태블릿)", "", "", "", "", "", "", "", "", ""),
 ("F1-1", "태블릿", "태블릿 연결", "가족 코드 + 태블릿 비밀번호로 로그인, 토큰을 기기에 저장", "가족 코드, 비밀번호", "POST /api/auth/login (role=tablet)", "대화 화면 진입", "코드 없음/비밀번호 오류 → 메시지", "1", "완료"),
 ("F1-2", "태블릿", "대화 시작", "큰 버튼 1개. 대화 생성 후 다정이 첫마디를 음성으로 재생", "버튼 클릭", "POST /api/conversations", "conversation id, 첫마디 텍스트", "페르소나 미등록 → 보호자 앱 안내", "1", "완료"),
 ("F1-3", "태블릿", "음성 입력", "브라우저 음성 인식(ko-KR)으로 부모님 발화를 글자로 변환, 다정이 발화 종료 후 자동 듣기", "마이크", "(브라우저)", "인식 텍스트, 시작·종료 시각", "미지원·권한 거부 → 글 입력 전환", "1", "완료 (실기기 확인 필요)"),
 ("F1-4", "태블릿", "응답 생성", "부모 발화 저장 → 페르소나 + 관련 가족 기록으로 LLM 응답 생성 → 저장 → TTS 재생", "발화 텍스트, 시각", "POST /api/conversations/{id}/turns", "응답 텍스트", "LLM 실패 → 고정 문구, conversations.error 기록", "1", "완료"),
 ("F1-5", "태블릿", "시간 기록", "다정이 재생 종료 시각, 부모 발화 시작·종료 시각 저장", "bot_spoke_until, started_at, ended_at", "같은 API", "turns 행", "시각 누락 → 서버 시각", "1", "완료"),
 ("F1-6", "태블릿", "대화 종료", "‘대화 마치기’ 또는 3분 무응답 → 종료 → 분석 작업 큐", "버튼/타이머", "POST /api/conversations/{id}/finish", "job id", "저장 실패 → 오류 표시", "1", "완료"),
 ("F1-7", "태블릿", "녹음 파일 변환(보조)", "녹음 파일 업로드 → 서버 STT", "오디오 파일 ≤25MB", "POST /api/conversations/{id}/audio", "텍스트", "MOCK/용량 초과 → 오류", "3", "완료 (키 필요)"),
 ("§ F2 대화 분류와 지표 (서버 작업)", "", "", "", "", "", "", "", "", ""),
 ("F2-1", "서버", "발화 정리", "부모 발화별 글자 수(공백 제외), 응답 간격(직전 bot 종료→발화 시작)", "turns", "jobs.analyze_conversation", "turns.char_len, response_gap_sec", "2분 초과 간격은 제외", "1", "완료"),
 ("F2-2", "서버", "태그 분류", "repeat: 앞선 발화와 2-gram 유사도 ≥0.7 / uncertain: ‘글쎄’, ‘기억이 안’ 등 패턴", "부모 발화 목록", "metrics.tag_parent_turns", "turns.tags", "-", "1", "완료 (테스트)"),
 ("F2-3", "서버", "대화 지표", "발화 길이 평균, 반복률, 불확실 비율, 응답 간격 평균, 참여(부모 글자 비중), 대화 시간", "turns", "metrics.compute_metrics", "conversation_metrics", "-", "1", "완료 (테스트)"),
 ("F2-4", "서버", "유효 대화", "부모 발화 3회 이상이면 valid=true, 기준선에 포함", "-", "metrics", "valid", "-", "1", "완료"),
 ("F2-5", "서버", "개인 기준선", "첫 유효 대화 +14일 · 유효 5회 → 초기 14일 평균·편차로 고정(1회)", "conversation_metrics", "jobs.refresh_baseline", "baselines", "조건 미달 → 수집 중", "1", "완료 (테스트)"),
 ("F2-6", "서버", "비교", "최근 7일 평균 vs 기준선 → 평소(<1σ) / 관찰(≥1σ) / 확인(≥1.5σ)", "week, baseline", "metrics.compare_to_baseline", "compare{level}", "기준선 없음 → 비교 없음", "1", "완료 (테스트)"),
 ("F2-7", "서버", "작업 큐", "analyze/summarize 를 jobs 에 쌓아 워커가 처리. 실패 시 상태·오류, 3회 재시도, 수동 재시도", "-", "jobs.start_worker, POST /api/jobs/{id}/retry", "jobs.status", "-", "1", "완료"),
 ("§ F3 보호자 대시보드와 AI 리포트", "", "", "", "", "", "", "", "", ""),
 ("F3-1", "보호자", "홈", "이번 주 한 줄 상태, 지표 카드 5(배지), 14일 그래프, 마지막 대화", "-", "GET /api/dashboard/overview", "화면", "-", "1", "완료"),
 ("F3-2", "보호자", "기준선 상태", "미고정 시 ‘수집 중 n/5회 · n/14일’ 표시", "-", "같은 API", "안내 문구", "-", "1", "완료"),
 ("F3-3", "보호자", "지표 상세", "측정 방법, 평소 값, 최근 14일 일별 표", "지표 키", "같은 API", "화면", "-", "2", "완료"),
 ("F3-4", "보호자", "대화 기록·상세", "월별 목록 → 지표 표, 발화별 태그·응답 초·입력 방식, 원문", "-", "GET /api/conversations, /{id}", "화면", "다른 가족 ID → 404", "1", "완료"),
 ("F3-5", "보호자", "대화 삭제", "대화·발화·지표·음성 파일 삭제", "id", "DELETE /api/conversations/{id}", "ok", "-", "2", "완료"),
 ("F3-6", "보호자", "AI 요약(대화)", "버튼 클릭 시 생성, 자동 없음. 생성 중/실패 표시, 다시 만들기", "conversation_id", "POST /api/summaries, GET /api/summaries/{id}", "summaries.text", "분석 전 → 400, 실패 → failed", "1", "완료"),
 ("F3-7", "보호자", "AI 요약(주간)", "최근 7일 지표·비교 기반 생성, 이전 요약 3개 표시", "-", "POST /api/summaries (weekly)", "summaries.text", "기준선 없음 → 비교 표현 없음", "1", "완료"),
 ("F3-8", "보호자", "가족 정보", "부모님·보호자 정보, 페르소나(호칭·말투·어미·표현·성격·습관·피할 주제·메모) 수정", "폼", "PUT /api/family, /api/family/persona", "저장", "태블릿 역할 → 403", "1", "완료"),
 ("F3-9", "보호자", "가족 이야기", "추억·생활 정보 등록·수정·삭제(제목·내용·키워드·연도)", "폼", "/api/family/memories", "저장", "-", "1", "완료"),
 ("F3-10", "보호자", "설정", "태블릿 연결 안내, 처리 작업 목록·재시도, 개인정보 안내, 로그아웃", "-", "GET /api/jobs, POST /api/jobs/{id}/retry", "화면", "-", "2", "완료"),
 ("§ F4 랜딩페이지", "", "", "", "", "", "", "", "", ""),
 ("F4-1", "랜딩", "구성", "히어로 → 부모님 태블릿 → 일상의 빈틈(한 주 토글) → 작동 방식(3단계) → 자녀 앱 → 이용 전후 → 참여 가정 모집 → 진행 과정 → 신청 → FAQ → 만든 사람들 → 푸터 (디자인 확정본 index.html 그대로)", "-", "-", "페이지", "-", "1", "완료"),
 ("F4-2", "랜딩", "신청 폼", "가정용(연령대·태블릿 보유)/기관용(기관명·이용 규모) 전환, 이름·연락 수단·동의 필수", "폼", "POST /api/applications", "접수 완료 화면", "이름 없음 → 입력칸 오류, 동의 없음 → 안내", "1", "완료"),
 ("F4-3", "백오피스", "신청 접수 관리", "접수 목록, 연락 상태(신규·연락함·완료)·메모", "상태·메모", "GET/PUT /api/admin/applications", "목록", "토큰 없음 → 403", "2", "완료"),
 ("F4-4", "랜딩", "추적 코드", "head 주석 위치에 GA4·픽셀 삽입", "-", "-", "-", "마케팅 업체 전달", "3", "자리만"),
 ("§ F5 운영·보안 (계약 §13)", "", "", "", "", "", "", "", "", ""),
 ("F5-1", "서버", "인증·격리", "토큰 인증, 역할 구분, 가족별 접근 제한, 운영자 토큰", "-", "auth.py", "-", "401/403/404", "1", "완료"),
 ("F5-2", "서버", "API 사용량 기록", "외부 호출마다 목적·토큰·성공 여부 저장, 집계 API", "-", "GET /api/admin/usage", "집계", "-", "2", "완료"),
 ("F5-3", "서버", "음성 보관·삭제", "가족별 keep_audio_days, 정리 스크립트, 대화 삭제 시 파일 삭제", "-", "scripts_cleanup.py", "-", "-", "2", "완료"),
 ("F5-4", "배포", "HTTPS·배포", "Docker 구성, Caddy 리버스 프록시 예시, 환경변수", "-", "docker-compose.yml", "-", "-", "1", "구성 완료 (도메인 대기)"),
 ("§ F6 백오피스와 연동 API (운영자 · X-Admin-Token)", "", "", "", "", "", "", "", "", ""),
 ("F6-1", "백오피스", "토큰 로그인", "운영자 토큰 입력, 탭 세션에만 보관", "토큰", "GET /api/admin/stats (검증)", "현황 화면", "틀림 → 오류 문구", "1", "완료"),
 ("F6-2", "백오피스", "현황", "가족·대화·신규 신청·실패 작업 수, 최근 작업, 연락 전 신청, 외부 API 호출", "-", "GET /api/admin/stats", "카드·표", "-", "1", "완료"),
 ("F6-3", "백오피스", "가족 목록·등록", "코드·이름 검색, 가족 등록(코드·부모님·보호자·비밀번호 2종)", "검색어·폼", "GET/POST /api/admin/families", "목록", "중복 코드 → 409", "1", "완료"),
 ("F6-4", "백오피스", "가족 상세·수정", "가족 정보·페르소나·가족 이야기·기준선(평균·편차)·최근 대화·작업, 정보 수정·비밀번호 재설정", "폼", "GET/PUT /api/admin/families/{id}", "상세", "없는 id → 404", "1", "완료"),
 ("F6-5", "백오피스", "가족 삭제", "코드 재입력 확인 후 대화·지표·기준선·요약·작업·세션·음성 파일 일괄 삭제", "코드 확인", "DELETE /api/admin/families/{id}", "삭제 결과", "-", "2", "완료"),
 ("F6-6", "연동 API", "기록 내보내기", "가족 1곳 전체 기록(가족·이야기·기준선·대화+발화+지표·요약) JSON", "family_id", "GET /api/admin/families/{id}/export", "JSON 파일", "-", "1", "완료"),
 ("F6-7", "백오피스", "대화 기록", "모든 가족의 대화를 가족·상태로 필터, 지표와 함께 표시 → 상세(원문·태그·응답 간격)", "필터", "GET /api/admin/conversations[/{id}]", "표·상세", "-", "1", "완료"),
 ("F6-8", "백오피스", "처리 작업", "분석·요약 작업 목록(상태·시도·오류), 실패 작업 다시 시도", "상태 필터", "GET /api/admin/jobs, POST …/retry", "표", "-", "2", "완료"),
 ("F6-9", "백오피스", "API 사용량", "최근 30일 목적별 호출·오류·토큰, 최근 호출 50건", "기간", "GET /api/admin/usage[/log]", "표", "-", "2", "완료"),
 ("F6-10", "백오피스", "연동 안내", "인증 방법, 엔드포인트 표, 기관 도구 연동 순서·요청 예시", "-", "화면", "-", "-", "3", "완료"),
]
sheet("기능명세", ["ID", "화면/영역", "기능", "설명", "입력", "처리 / API", "출력", "예외 처리", "우선순위", "상태(11.04)"], F, [8, 10, 18, 52, 20, 34, 20, 30, 8, 16])

# ---------- 2. 정보구조 ----------
IA = [
 ("랜딩", "/", "랜딩페이지", "1", "누구나", "히어로 · 태블릿 · 일상의 빈틈 · 작동 방식 · 자녀 앱 · 이용 전후 · 모집 · 진행 과정 · 신청 · FAQ · 만든 사람들"),
 ("랜딩", "/#apply", "신청 폼", "2", "누구나", "가정용 / 기관용 · 동의"),
 ("랜딩", "/privacy.html", "개인정보 처리방침", "2", "누구나", "발주사 검토본으로 교체"),
 ("태블릿", "/tablet.html", "연결", "1", "부모님(설치 시 자녀)", "가족 코드 · 태블릿 비밀번호"),
 ("태블릿", "/tablet.html", "대기 화면", "2", "부모님", "시계 · 아바타 · 버튼 1개"),
 ("태블릿", "/tablet.html", "대화 화면", "3", "부모님", "다정이 자막 · 부모님 자막 · 상태 · 글로 말하기"),
 ("태블릿", "/tablet.html", "종료", "3", "부모님", "대화 마치기 · 자동 종료"),
 ("보호자", "/app.html", "로그인", "1", "보호자", "가족 코드 · 비밀번호"),
 ("보호자", "/app.html#home", "홈", "2", "보호자", "이번 주 상태 · 지표 5 · 14일 그래프 · 마지막 대화"),
 ("보호자", "/app.html#metric/{key}", "지표 상세", "3", "보호자", "측정 방법 · 평소 · 일별"),
 ("보호자", "/app.html#report", "주간 AI 요약", "3", "보호자", "평소/이번 주/비교 표 · 요약 생성"),
 ("보호자", "/app.html#talks", "대화 기록", "2", "보호자", "월별 목록"),
 ("보호자", "/app.html#talk/{id}", "대화 상세", "3", "보호자", "지표 · 원문 · 태그 · AI 요약 · 삭제"),
 ("보호자", "/app.html#family", "가족 정보", "2", "보호자", "부모님·보호자 · 페르소나 · 가족 이야기"),
 ("보호자", "/app.html#family", "가족 이야기 추가/수정", "3", "보호자", "제목 · 내용 · 키워드 · 연도"),
 ("보호자", "/app.html#more", "설정", "2", "보호자", "태블릿 연결 · 처리 작업 · 개인정보 · 로그아웃"),
 ("백오피스", "/admin.html", "토큰 로그인", "1", "운영자(X-Admin-Token)", "운영자 토큰 입력"),
 ("백오피스", "/admin.html#home", "현황", "2", "운영자", "가족·대화·신청·작업 수 · 최근 작업 · 연락 전 신청"),
 ("백오피스", "/admin.html#families", "가족", "2", "운영자", "검색 · 가족 등록"),
 ("백오피스", "/admin.html#family/{id}", "가족 상세", "3", "운영자", "정보 · 페르소나 · 기준선 · 대화 · 작업 · 수정 · 삭제 · JSON 내보내기"),
 ("백오피스", "/admin.html#talks", "대화 기록", "2", "운영자", "가족·상태 필터 · 지표 표"),
 ("백오피스", "/admin.html#talk/{id}", "대화 상세", "3", "운영자", "지표 · 기록 정보 · 원문·태그"),
 ("백오피스", "/admin.html#apps", "신청 접수", "2", "운영자", "상태(신규·연락함·완료) · 메모"),
 ("백오피스", "/admin.html#jobs", "처리 작업", "2", "운영자", "상태 필터 · 다시 시도"),
 ("백오피스", "/admin.html#usage", "API 사용량", "2", "운영자", "목적별 집계 · 최근 호출"),
 ("백오피스", "/admin.html#api", "연동 안내", "2", "운영자", "인증 · 엔드포인트 · 연동 예시"),
 ("운영", "/docs", "API 문서", "1", "운영자", "Swagger UI (로컬 번들)"),
]
sheet("정보구조(IA)", ["영역", "경로", "화면", "깊이", "접근", "주요 요소"], IA, [10, 26, 22, 6, 20, 50])

# ---------- 3. 화면목록 (캡처 매핑) ----------
SC = [
 ("A", "랜딩", "PC 전체 / 첫 화면 / FAQ / 신청 폼(가정·기관) / 접수 완료 / 모바일 / 처리방침", "A01~A08"),
 ("B", "태블릿", "연결 / 비밀번호 오류 / 대기 / 첫마디 / 글 입력 / 가족 기록 반영 응답 / 대화 마치기", "B01~B07"),
 ("C", "보호자 앱", "로그인 / 홈 / 지표 상세 / 대화 목록 / 대화 상세 / AI 요약 / 주간 요약 / 가족 정보 / 이야기 추가 / 설정 / 실패 작업 재시도 / 신규 가족 / 기록 없음", "C01~C13"),
 ("D", "API", "같은 기록 JSON / health / 예외 점검 / Swagger", "D01~D04"),
 ("E", "시스템", "단위 테스트 / DB 테이블 / 연동 API(현황·내보내기) / 서버 로그 / 소스 구성", "E01~E05"),
 ("G", "백오피스", "로그인 / 토큰 오류 / 현황 / 가족 목록 / 가족 상세·기준선 / 대화 기록 / 대화 상세 / 신청 접수 / 처리 작업 / API 사용량 / 연동 안내", "G01~G11"),
 ("F", "브라우저", "Chrome PC / Edge PC / iPhone / Android 태블릿 × 랜딩·보호자 홈", "F01~F04"),
]
sheet("화면목록", ["묶음", "영역", "화면", "캡처 파일 (docs/captures/결과보고서용)"], SC, [6, 10, 80, 30])

# ---------- 4. API 목록 (openapi.json) ----------
o = json.load(open(os.path.join(ROOT, "docs", "openapi.json"), encoding="utf-8"))
AUTH = lambda p: "관리자 토큰" if "/admin/" in p else "없음" if p in ("/api/health", "/api/auth/login", "/api/applications") else "보호자" if any(k in p for k in ["persona", "memories", "summaries}", "retry"]) else "로그인(보호자/태블릿)"
API = []
for path, ms in o["paths"].items():
    for m, d in ms.items():
        desc = ((d.get("description") or "").splitlines() or [""])[0] or d.get("summary", "")
        API.append((m.upper(), path, ", ".join(d.get("tags", [])), AUTH(path), desc))
sheet("API목록", ["메서드", "경로", "태그", "인증", "설명"], API, [8, 40, 12, 18, 70], "docs/openapi.json 에서 자동 생성 · 실행 중 서버의 /docs 가 항상 최신")

# ---------- 5. 테이블 정의 (SQLAlchemy 메타데이터) ----------
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
from app.models import Base
TB = []
for t in Base.metadata.sorted_tables:
    TB.append(("§ " + t.name, "", "", "", "", t.comment or ""))
    for c in t.columns:
        typ = str(c.type)
        key = "PK" if c.primary_key else ("FK → " + ", ".join(fk.target_fullname for fk in c.foreign_keys) if c.foreign_keys else ("UK" if c.unique else ""))
        TB.append((t.name, c.name, typ, "N" if not c.nullable else "Y", key, "예약(향후)" if c.name.startswith("reserved_") else ""))
sheet("테이블정의", ["테이블", "컬럼", "타입", "NULL", "키", "비고"], TB, [22, 28, 18, 6, 30, 16], "server/app/models.py 에서 자동 생성 (11 테이블)")

out = os.path.join(ROOT, "docs", "다정이_MVP_기능명세서.xlsx")
wb.save(out); print("saved", out, "sheets:", wb.sheetnames)
