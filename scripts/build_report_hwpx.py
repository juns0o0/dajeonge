"""용역 결과 보고서 생성 (한글 HWPX + HTML 미리보기).

- 서식: scripts/report_template/ (글꼴·문단·표 서식만 담긴 HWPX 골격)
- 캡처: docs/captures/결과보고서용/, 다이어그램: docs/diagrams/
- 출력: docs/결과보고서/다정이_MVP_용역결과보고서.hwpx, 같은 내용의 .html (→ scripts/report_pdf.js 로 .pdf)

실행: python3 scripts/build_report_hwpx.py
"""
import html, math, pathlib, struct, zipfile, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
T = ROOT / "scripts/report_template"
CAP = ROOT / "docs/captures/결과보고서용"
DIAG = ROOT / "docs/diagrams"
OUT = ROOT / "docs/결과보고서"; OUT.mkdir(exist_ok=True)
NAME = "다정이_MVP_용역결과보고서"
def cap(prefix):
    """캡처 파일을 번호 접두어로 찾는다 (대화 ID 등 가변 부분 무시)."""
    m = sorted(CAP.glob(prefix + "_*.png"))
    if not m: raise FileNotFoundError(f"캡처 없음: {prefix}_*")
    return m[0]

# =====================================================================
# 1. 보고서 내용
# =====================================================================
REPORT_DATE = "2026. 11. 13"
R = dict(
    title="용역 결과 보고서", subtitle="[AI Care Bot ‘다정이’ 웹 MVP 설계·디자인·개발]",
    date=REPORT_DATE, company="펄스픽시아", ceo="정준수",
    overview=[
        ("가. 용 역 명 : AI Care Bot ‘다정이’ 웹 MVP 설계·디자인·개발 용역", []),
        ("나. 사업기간 : 2026.10.13. - 2026.11.13.(5주)", []),
        ("다. 과업의 목적 및 필요성 :", [
            "시연 화면 수준이던 다정이에 실제 API·DB·대화 분석 로직을 연결해 리빙랩 검증이 가능한 MVP 확보",
            "부모님이 태블릿 버튼 하나로 자녀 말투의 다정이와 음성 대화, 대화 기록 자동 저장",
            "발화 길이·반복·불확실 표현·응답 간격·참여 지표를 개인 기준선과 비교해 보호자가 확인",
            "운영 데이터 관리 백오피스와 외부 시스템 연동 API, 서비스 소개·신청용 랜딩페이지 제작"]),
        ("라. 계약기간 : 2026.10.13. - 2026.11.13.", []),
        ("마. 용역예산 : 칠백만원(7,000,000원) *부가세 별도", []),
    ],
    requests=[
        ("음성 대화 저장", "태블릿 음성 대화 → 응답 → 저장", "완료", "브라우저 음성 인식 + 기본 TTS, 글 입력 대체"),
        ("대화 분류·지표", "태그 분류, 지표 5종, 개인 기준선", "완료", "14일·유효 5회 기준선, 평소/관찰/확인"),
        ("보호자 대시보드", "주간 지표·그래프·대화 기록", "완료", "휴대폰 브라우저, 홈 화면 추가"),
        ("AI 리포트", "대화·주간 AI 요약", "완료", "버튼 생성, 병명·진단 표현 제외"),
        ("백오피스·연동 API", "데이터 관리 화면, 외부 연동 API", "완료", "운영자 토큰 인증, Swagger 문서"),
        ("랜딩페이지", "디자인 확정본 구현·신청폼", "완료", "레퍼런스와 동일, 크롬·엣지·사파리·macOS"),
    ],
    features=[
        ("1) 태블릿 대화 화면", [
            "가족 코드 연결, 버튼 1개로 대화 시작, 다정이 첫마디 음성 재생",
            "브라우저 음성 인식(ko-KR)으로 발화 저장, 미지원 환경은 글 입력으로 전환",
            "가족 이야기(페르소나·추억)를 반영한 응답 생성, 대화 마치기·3분 무응답 자동 종료"]),
        ("2) 대화 분석", [
            "반복·불확실 표현 태그, 발화 길이·반복률·불확실 비율·응답 간격·참여 지표 계산",
            "첫 유효 대화 후 14일·5회 기준으로 개인 기준선 고정, 최근 7일과 비교(평소/관찰/확인)",
            "분석·요약 작업 대기열, 실패 시 상태·오류 기록과 재시도"]),
        ("3) 보호자 앱", [
            "홈: 이번 주 상태, 지표 5개 배지, 최근 14일 그래프, 마지막 대화",
            "지표 상세, 대화 기록 목록·상세(원문·태그·응답 간격), 대화 삭제",
            "버튼으로 생성하는 대화 요약·주간 요약, 가족 정보·페르소나·가족 이야기 관리, 처리 작업 재시도"]),
        ("4) 백오피스와 연동 API", [
            "현황, 가족 등록·수정·삭제, 대화 기록·지표 조회, 신청 접수 상태·메모, 처리 작업 재시도, API 사용량",
            "가족 기록 JSON 내보내기, 외부 시스템이 호출하는 연동 API 15종과 Swagger 문서"]),
        ("5) 랜딩페이지", [
            "히어로 → 태블릿 → 한 주 토글 → 작동 방식 → 자녀 앱 → 이용 전후 → 모집 → 진행 과정 → 신청 폼(가정용/기관용) → FAQ → 만든 사람들",
            "디자인 확정본과 동일 구현 (1280px·390px 레퍼런스 캡처 대조), PC·모바일 반응형"]),
    ],
    tech=[
        "프론트엔드: HTML5, CSS3, JavaScript (빌드 도구 없음), 자체 호스팅 글꼴 Jua·Pretendard Variable (OFL)",
        "백엔드: Python 3.11, FastAPI, SQLAlchemy, SQLite (PostgreSQL 전환 가능), 작업 워커",
        "음성: Web Speech API(음성 인식, ko-KR), speechSynthesis(TTS), 서버 STT는 파일 업로드용",
        "AI: OpenAI chat.completions·audio.transcriptions, 키 없을 때 MOCK 모드, 사용량 기록",
        "보안: 토큰 인증, 보호자/태블릿 역할, 가족별 기록 격리, 운영자 토큰, HTTPS",
        "배포: GitHub 저장소, Docker 구성, 환경변수(.env), 랜딩페이지는 GitHub Pages 로 공개",
        "브라우저: Chrome, Edge, Safari, Android 태블릿 Chrome 확인",
    ],
    deliverables=[
        ("1", "태블릿 대화 화면", "음성 대화·저장 (tablet.html)", "GitHub 배포"),
        ("2", "보호자 앱", "대시보드·대화 기록·AI 요약 (app.html)", "GitHub 배포"),
        ("3", "백오피스", "데이터 관리 화면 (admin.html)", "GitHub 배포"),
        ("4", "연동 API·DB", "FastAPI 서버, 테이블 11개, Swagger", "GitHub 배포"),
        ("5", "랜딩페이지", "반응형 소개·신청 페이지 (index.html)", "GitHub Pages 공개 (juns0o0.github.io/dajeonge)"),
        ("6", "완성 소스코드", "서버·웹·스크립트 전체 코드", "GitHub 저장소 이관"),
        ("7", "설계·운영 문서", "기능명세·흐름도·ERD·API·운영 매뉴얼·검수 체크리스트", "GitHub(docs/)·이메일"),
    ],
    schedule=[
        ("계약체결", "계약체결", "2026.10.13"),
        ("기획 및 설계", "범위·화면·분석 기준 확정, 기능명세·흐름도", "2026.10.17"),
        ("개발", "DB·음성 API·가족정보 연결, 지표·기준선, 랜딩페이지", "2026.10.31"),
        ("통합 점검", "대시보드·AI 요약·백오피스 구현, 대화 1건 전체 흐름 시연", "2026.11.07"),
        ("최종 납품", "오류 수정·검수·GitHub 배포·운영 안내", "2026.11.13"),
    ],
    gantt_weeks=["10월 3주", "10월 4주", "10월 5주", "11월 1주", "11월 2주"],
    gantt=[("기획 단계", [1, 0, 0, 0, 0]), ("디자인 단계", [1, 1, 0, 0, 0]), ("개발 단계", [0, 1, 1, 1, 0]),
           ("테스트 및 수정", [0, 0, 0, 1, 1]), ("최종 납품", [0, 0, 0, 0, 1])],
    effects=[
        ("부모님과 보호자", ["부모님은 버튼 하나로 매일 대화하고, 보호자는 대화 속 변화를 평소 기준과 비교해 확인",
                        "지표·요약은 참고 정보로 제공하며 병명·진단 표현은 쓰지 않음"]),
        ("서비스 확장 기반", ["리빙랩 운영으로 실제 대화 데이터 축적, 기준선·지표 검증",
                        "백오피스와 연동 API로 기관 관리 도구·알림 발송 등 후속 연동 가능",
                        "기억 회상·일관성 점수·자동 알림은 데이터 항목과 연결 위치를 설계해 둠"]),
    ],
    results=[   # (산출물명, [(라벨, 파일)])
        ("랜딩페이지\n(PC)", [("전체", cap("A01")), ("크롬", cap("F01")),
                           ("엣지", cap("F02")), ("신청 폼 (기관용)", cap("A05")),
                           ("신청 접수 완료", cap("A06"))]),
        ("랜딩페이지\n(모바일)", [("iPhone Safari", cap("F03")), ("Android 태블릿", cap("F04")),
                             ("모바일 전체", cap("A07"))]),
        ("태블릿\n대화 화면", [("연결", cap("B01")), ("대기 화면", cap("B03")),
                           ("대화 중 (가족 기록 반영 응답)", cap("B06")), ("대화 마치기", cap("B07"))]),
        ("보호자 앱", [("홈 (지표 5개·14일 그래프)", cap("C02")), ("지표 상세", cap("C03")),
                   ("대화 상세 (원문·태그·응답 간격)", cap("C05")), ("대화 AI 요약", cap("C06")),
                   ("주간 AI 요약", cap("C07")), ("가족 정보·페르소나", cap("C08")),
                   ("처리 작업 재시도", cap("C11"))]),
        ("백오피스", [("현황", cap("G03")), ("가족 상세·개인 기준선", cap("G05")),
                  ("대화 기록·지표", cap("G06")), ("신청 접수 상태·메모", cap("G08")),
                  ("처리 작업 재시도", cap("G09")), ("연동 안내", cap("G11"))]),
        ("연동 API·\n점검 결과", [("같은 기록의 저장·분석 결과 JSON", cap("D01")), ("예외 점검 (404 / 403 / 422)", cap("D03")),
                             ("연동 API 응답 (현황·기록 내보내기)", cap("E03")), ("단위 테스트", cap("E01")),
                             ("DB 테이블·저장 건수", cap("E02"))]),
        ("설계 문서", [("시스템 구조도", DIAG / "01_시스템구조도.png"), ("ERD", DIAG / "02_ERD.png"), ("정보구조도", DIAG / "03_정보구조도.png"),
                   ("데이터 흐름도", DIAG / "05_데이터흐름도.png")]),
    ],
    delivered=[
        ("가. 완성 결과물 : GitHub 저장소에 배포 (소스·문서·실행 구성 일체)", "https://github.com/juns0o0/dajeonge"),
        ("나. 랜딩페이지 : GitHub Pages 로 공개, 신청 접수는 구글 시트에 저장하고 신청자 확인 화면 제공", "https://juns0o0.github.io/dajeonge/ (신청 확인: https://juns0o0.github.io/dajeonge/applicants.html)"),
        ("다. 소스코드 : 전체 소스코드 및 개발 명세서 제공", "API 명세서 : 서버 /docs (Swagger), docs/04_API문서.md"),
        ("라. API 연동 : 가족·대화·신청·작업·사용량 연동 API 15종 및 백오피스 연동 완료", None),
        ("마. 결과보고서 : 주요 브라우저 렌더링 테스트 및 용역 결과", None),
        ("바. 운영 자료 : 운영 매뉴얼·검수 체크리스트·화면 캡처 56장", None),
        ("사. 하자보수 : 검수 완료 후 30일간 합의 기능의 하자 수정", None),
    ],
    delivered_pics=[("API 명세서 – 스웨거", cap("D04")), ("전체 소스코드 (GitHub 저장소 구성)", cap("E05"))],
    fixes=["1차 납품(2026.11.07. 통합 점검) 후 수정 반영 완료", "최종승인: 2026.11.13. 발주사 최종 승인"],
    sign=("상기 물품을 정히 영수함", "2026년 11월 13일", "확인자", ":", "김 현 정", "(인)"),
)

# =====================================================================
# 2. HWPX 빌더
# =====================================================================
W = 42520                      # 본문 폭 (HWPUNIT, 1/7200 inch)
PAGE_H = 60000                 # 그림 최대 높이
_ids = [1992611000]; _z = [0]
def nid(): _ids[0] += 1; return _ids[0]
def nz(): _z[0] += 1; return _z[0]
def esc(t): return html.escape(t, quote=False)
def LS(h=1400, w=W): return f'<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="{h}" textheight="{h}" baseline="{int(h*0.85)}" spacing="{int(h*0.6)}" horzpos="0" horzsize="{w}" flags="393216"/></hp:linesegarray>'

def run(text, cp):
    parts = text.split("\t"); inner = ""
    for i, p in enumerate(parts):
        if i: inner += '<hp:tab width="4000" leader="0" type="1"/>'
        inner += esc(p)
    return f'<hp:run charPrIDRef="{cp}"><hp:t>{inner}</hp:t></hp:run>'

def P(text="", pp=23, cp=15, pb=0, w=W, runs=None, h=1400):
    body = runs if runs is not None else (run(text, cp) if text else f'<hp:run charPrIDRef="{cp}"><hp:t/></hp:run>')
    return f'<hp:p id="0" paraPrIDRef="{pp}" styleIDRef="0" pageBreak="{pb}" columnBreak="0" merged="0">{body}{LS(h, w)}</hp:p>'

def TC(paras, w, h, bf, col, row, cs=1, rs=1, valign="CENTER"):
    return (f'<hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="{bf}">'
            f'<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="{valign}" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">{paras}</hp:subList>'
            f'<hp:cellAddr colAddr="{col}" rowAddr="{row}"/><hp:cellSpan colSpan="{cs}" rowSpan="{rs}"/><hp:cellSz width="{w}" height="{h}"/>'
            f'<hp:cellMargin left="510" right="510" top="141" bottom="141"/></hp:tc>')

def TBL(rows, w, h, rowCnt, colCnt, outm=283, pp=23, cp=15):
    tbl = (f'<hp:tbl id="{nid()}" zOrder="{nz()}" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="{rowCnt}" colCnt="{colCnt}" cellSpacing="0" borderFillIDRef="3" noAdjust="0">'
           f'<hp:sz width="{w}" widthRelTo="ABSOLUTE" height="{h}" heightRelTo="ABSOLUTE" protect="0"/>'
           f'<hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
           f'<hp:outMargin left="{outm}" right="{outm}" top="{outm}" bottom="{outm}"/><hp:inMargin left="510" right="510" top="141" bottom="141"/>'
           + "".join(f"<hp:tr>{r}</hp:tr>" for r in rows) + "</hp:tbl>")
    return P(pp=pp, cp=cp, runs=f'<hp:run charPrIDRef="{cp}">{tbl}</hp:run>')

def cell_text(text, w, cp=18, pp=0, size=1100):
    """셀 안 문단들. 줄바꿈은 문단으로 나눈다. 높이 추정값도 돌려준다."""
    lines = text.split("\n") if text else [""]
    paras = "".join(P(l, pp=pp, cp=cp, w=w - 1020, h=size) for l in lines)
    cpl = max(1, (w - 1020) // int(size * 0.95))
    n = sum(max(1, math.ceil(len(l) / cpl)) for l in lines)
    return paras, 282 + n * int(size * 1.6) + 400

def simple_table(header, rows, widths, cp_head=19, cp_body=18, size=1100, head_bf=5, body_bf=3, body_pp=0):
    out = []; heights = []
    hs = [cell_text(h, w, cp_head, 0, 1200) for h, w in zip(header, widths)]
    hh = max(x[1] for x in hs)
    out.append("".join(TC(p, w, hh, head_bf, c, 0) for c, ((p, _), w) in enumerate(zip(hs, widths)))); heights.append(hh)
    for r, row in enumerate(rows, 1):
        cs = [cell_text(v, w, cp_body, body_pp, size) for v, w in zip(row, widths)]
        rh = max(x[1] for x in cs)
        out.append("".join(TC(p, w, rh, body_bf, c, r) for c, ((p, _), w) in enumerate(zip(cs, widths)))); heights.append(rh)
    return TBL(out, sum(widths), sum(heights), len(rows) + 1, len(widths))

# ---- 그림 ----
IMAGES = []     # (id, path)
def png_size(p): b = open(p, "rb").read(24); return struct.unpack(">II", b[16:24])
def PIC(path, box_w, max_h=PAGE_H):
    """셀 폭(box_w)에 맞춘 그림. (xml, cur_w, cur_h)"""
    IMAGES.append(path); iid = f"image{len(IMAGES)}"
    pw, ph = png_size(path); ow, oh = pw * 50, ph * 50; dw, dh = pw * 75, ph * 75
    cw = box_w; ch = int(cw * ph / pw)
    if ch > max_h: ch = max_h; cw = int(ch * pw / ph)
    xml = (f'<hp:pic id="{nid()}" zOrder="{nz()}" numberingType="PICTURE" textWrap="SQUARE" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" href="" groupLevel="0" instid="{nid()}" reverse="0">'
           f'<hp:offset x="0" y="0"/><hp:orgSz width="{ow}" height="{oh}"/><hp:curSz width="{cw}" height="{ch}"/><hp:flip horizontal="0" vertical="0"/>'
           f'<hp:rotationInfo angle="0" centerX="{cw//2}" centerY="{ch//2}" rotateimage="1"/>'
           f'<hp:renderingInfo><hc:transMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/><hc:scaMatrix e1="{cw/ow:.6f}" e2="0" e3="0" e4="0" e5="{ch/oh:.6f}" e6="0"/><hc:rotMatrix e1="1" e2="0" e3="0" e4="0" e5="1" e6="0"/></hp:renderingInfo>'
           f'<hc:img binaryItemIDRef="{iid}" bright="0" contrast="0" effect="REAL_PIC" alpha="0"/>'
           f'<hp:imgRect><hc:pt0 x="0" y="0"/><hc:pt1 x="{ow}" y="0"/><hc:pt2 x="{ow}" y="{oh}"/><hc:pt3 x="0" y="{oh}"/></hp:imgRect>'
           f'<hp:imgClip left="0" right="{dw}" top="0" bottom="{dh}"/><hp:inMargin left="0" right="0" top="0" bottom="0"/><hp:imgDim dimwidth="{dw}" dimheight="{dh}"/><hp:effects/>'
           f'<hp:sz width="{cw}" widthRelTo="ABSOLUTE" height="{ch}" heightRelTo="ABSOLUTE" protect="0"/>'
           f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>'
           f'<hp:outMargin left="0" right="0" top="0" bottom="0"/><hp:shapeComment>그림입니다.\n원본 그림의 이름: {esc(path.name)}\n원본 그림의 크기: 가로 {pw}pixel, 세로 {ph}pixel</hp:shapeComment></hp:pic>')
    return xml, cw, ch

def pic_para(path, box_w, max_h=PAGE_H):
    xml, cw, ch = PIC(path, box_w, max_h)
    return P(pp=20, cp=15, runs=f'<hp:run charPrIDRef="15">{xml}</hp:run>', w=box_w, h=ch), ch

# ---- 문서 조립 ----
def build_section():
    head = (T / "Contents/section_head.xml").read_text(encoding="utf-8")
    secpr = (T / "Contents/secpr_run.xml").read_text(encoding="utf-8")
    ps = []
    # 표지
    cover_w = 41954
    cp_paras = P(R["title"], pp=20, cp=9, w=cover_w - 1020, h=2400) + P(R["subtitle"], pp=20, cp=12, w=cover_w - 1020, h=2400)
    cover = TBL([TC(cp_paras, cover_w, 12912, 3, 0, 0)], cover_w, 12912, 1, 1, pp=0, cp=0)
    ps.append(cover.replace('<hp:run charPrIDRef="0">', secpr + '<hp:run charPrIDRef="0">', 1))
    ps += [P(pp=20, cp=11, h=2000) for _ in range(17)]
    ps.append(P(R["date"], pp=20, cp=11, h=2000))
    ps += [P(pp=20, cp=11, h=2000) for _ in range(4)]
    ps.append(P(R["company"], pp=20, cp=11, h=2000))
    ps.append(P(f"대표자:   {R['ceo']}   (인)", pp=20, cp=10, h=2000))
    # 1. 용역 개요
    ps.append(P("용역 개요", pp=22, cp=16, pb=1, h=1600)); ps.append(P())
    for line, subs in R["overview"]:
        ps.append(P("   " + line))
        for s in subs: ps.append(P("\t- " + s))
        ps.append(P())
    # 2. 주요 요청 사항
    ps.append(P("주요 요청 사항", pp=22, cp=16, h=1600))
    ps.append(simple_table(["항목", "요청사항", "달성도", "비고"], R["requests"], [11000, 13000, 4800, 13720]))
    ps.append(P())
    # 3. 용역결과 및 주요성과
    ps.append(P("용역결과 및 주요성과", pp=22, cp=16, h=1600))
    ps.append(P("   가. 완료된 주요 기능"))
    for t, subs in R["features"]:
        ps.append(P("\t" + t))
        for s in subs: ps.append(P("\t - " + s))
        ps.append(P())
    ps.append(P("   나. 기술적 구현사항"))
    for s in R["tech"]: ps.append(P("\t- " + s))
    ps.append(P()); ps.append(P("   다. 산출물 내역")); ps.append(P())
    ps.append(simple_table(["번호", "산출물명", "상세내용", "전달방법"], R["deliverables"], [3200, 11000, 18320, 10000]))
    ps.append(P())
    # 4. 추진일정
    ps.append(P("추진일정", pp=22, cp=16, h=1600))
    ps.append(simple_table(["구분", "주요 업무", "일정"], R["schedule"], [9000, 24520, 9000], cp_body=14, size=1200))
    ps.append(P())
    # 5. 과업의 수행일정 (간트)
    ps.append(P("과업의 수행일정", pp=22, cp=16, h=1600))
    weeks = R["gantt_weeks"]; cw = 5000; widths = [9000] + [cw] * len(weeks) + [W - 9000 - cw * len(weeks)]
    rh = 2998
    r0 = TC(cell_text("구분", widths[0], 19, 0, 1200)[0], widths[0], rh, 5, 0, 0, rs=2) + TC(cell_text("추진일정", cw * len(weeks), 19, 0, 1200)[0], cw * len(weeks), rh, 5, 1, 0, cs=len(weeks)) + TC(cell_text("비고", widths[-1], 19, 0, 1200)[0], widths[-1], rh, 5, len(weeks) + 1, 0, rs=2)
    r1 = "".join(TC(cell_text(wk, cw, 19, 0, 1200)[0], cw, rh, 5, i + 1, 1) for i, wk in enumerate(weeks))
    rows = [r0, r1]
    for r, (name, on) in enumerate(R["gantt"], 2):
        cells = TC(cell_text(name, widths[0], 14, 0, 1200)[0], widths[0], rh, 3, 0, r)
        cells += "".join(TC(P(pp=0, cp=14, w=cw - 1020, h=1200), cw, rh, 4 if v else 3, i + 1, r) for i, v in enumerate(on))
        cells += TC(P(pp=0, cp=14, w=widths[-1] - 1020, h=1200), widths[-1], rh, 3, len(weeks) + 1, r)
        rows.append(cells)
    ps.append(TBL(rows, W, rh * len(rows), len(rows), len(weeks) + 2))
    ps.append(P())
    # 6. 기대효과 및 활용방안
    ps.append(P("기대효과 및 활용방안", pp=22, cp=16, h=1600))
    eff = ""; n = 0
    for t, subs in R["effects"]:
        eff += P(t, pp=0, cp=19, w=cover_w - 1020, h=1200); n += 1
        for s in subs: eff += P("- " + s, pp=21, cp=14, w=cover_w - 1020, h=1200); n += 1
    ps.append(TBL([TC(eff, cover_w, 282 + n * 1900, 3, 0, 0)], cover_w, 282 + n * 1900, 1, 1, outm=141))
    ps.append(P())
    # 7. 결과물
    ps.append(P("결과물", pp=22, cp=16, pb=1, h=1600))
    lw, rw = 8525, 33429; rows = []; heights = []
    rows.append(TC(cell_text("산출물명", lw, 15, 20, 1400)[0], lw, 1682, 6, 0, 0) + TC(cell_text("개별항목", rw, 15, 20, 1400)[0], rw, 1682, 6, 1, 0)); heights.append(1682)
    r = 1
    for name, items in R["results"]:
        first = True
        for label, path in items:
            pic, ch = pic_para(path, rw - 1020, 52000)
            lab = TC(cell_text(label, rw, 15, 20, 1400)[0], rw, 1682, 7, 1, r)
            if first:
                rows.append(TC(cell_text(name, lw, 15, 20, 1400)[0], lw, 1682, 3, 0, r, rs=2 * len(items)) + lab); first = False
            else:
                rows.append(lab)
            heights.append(1682); r += 1
            rows.append(TC(pic, rw, ch + 282, 3, 1, r)); heights.append(ch + 282); r += 1
    ps.append(TBL(rows, lw + rw, sum(heights), r, 2, outm=141))
    ps.append(P())
    # 8. 납품 완료 항목
    ps.append(P("납품 완료 항목", pp=22, cp=16, pb=1, h=1600))
    for line, sub in R["delivered"]:
        ps.append(P("   " + line))
        if sub: ps.append(P(runs=run("\t", 15) + run(sub, 17 if sub.startswith("http") else 15)))
    ps.append(P())
    for label, path in R["delivered_pics"]:
        tw = 42202; pic, ch = pic_para(path, tw - 1020, 40000)
        rows = [TC(cell_text(label, tw, 15, 20, 1400)[0], tw, 1682, 7, 0, 0), TC(pic, tw, ch + 282, 3, 0, 1)]
        ps.append(TBL(rows, tw, 1682 + ch + 282, 2, 1, outm=141)); ps.append(P())
    # 9. 수정 반영 현황
    ps.append(P("수정 반영 현황", pp=22, cp=16, h=1600))
    for f in R["fixes"]: ps.append(P("   - " + f))
    ps += [P() for _ in range(6)]
    sw = [14543, 10950, 5617, 1372, 6770, 3375]; scp = [25, 26, 26, 26, 26, 26]
    ps.append(TBL(["".join(TC(cell_text(t, w, c, 20, 1400)[0], w, 3463, 9, i, 0) for i, (t, w, c) in enumerate(zip(R["sign"], sw, scp)))], sum(sw), 3463, 1, 6, outm=141))
    return head + "".join(ps) + "</hs:sec>"

def content_hpf():
    items = "".join(f'<opf:item id="image{i}" href="BinData/image{i}.png" media-type="image/png" isEmbeded="1"/>' for i in range(1, len(IMAGES) + 1))
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><opf:package xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph" xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history" xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page" xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf/" xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart" xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar" xmlns:epub="http://www.idpf.org/2007/ops" xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0" version="" unique-identifier="" id="">'
            f'<opf:metadata><opf:title>{esc(R["title"])}</opf:title><opf:language>ko</opf:language><opf:meta name="creator" content="text">{R["company"]}</opf:meta><opf:meta name="subject" content="text"/><opf:meta name="description" content="text"/><opf:meta name="lastsaveby" content="text">{R["company"]}</opf:meta><opf:meta name="CreatedDate" content="text">{now}</opf:meta><opf:meta name="ModifiedDate" content="text">{now}</opf:meta><opf:meta name="keyword" content="text"/></opf:metadata>'
            f'<opf:manifest><opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>{items}<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/><opf:item id="settings" href="settings.xml" media-type="application/xml"/></opf:manifest>'
            '<opf:spine><opf:itemref idref="header" linear="yes"/><opf:itemref idref="section0" linear="yes"/></opf:spine></opf:package>')

def preview_text():
    L = [f"<{R['title']} {R['subtitle']}>", "", R["date"], "", R["company"], f"대표자:   {R['ceo']}   (인)", "", "1. 용역 개요"]
    for line, subs in R["overview"]: L.append("   " + line); L += ["     - " + s for s in subs]
    L += ["", "2. 주요 요청 사항"] + [" | ".join(r) for r in R["requests"]]
    L += ["", "3. 용역결과 및 주요성과", "   가. 완료된 주요 기능"]
    for t, subs in R["features"]: L.append("    " + t); L += ["     - " + s for s in subs]
    L += ["   나. 기술적 구현사항"] + ["     - " + s for s in R["tech"]]
    L += ["   다. 산출물 내역"] + [" | ".join(r) for r in R["deliverables"]]
    L += ["", "4. 추진일정"] + [" | ".join(r) for r in R["schedule"]]
    L += ["", "8. 납품 완료 항목"] + ["   " + a + (("\n     " + b) if b else "") for a, b in R["delivered"]]
    L += ["", "9. 수정 반영 현황"] + ["   - " + f for f in R["fixes"]]
    return "\n".join(L)

def write_hwpx(path):
    sec = build_section()
    import xml.dom.minidom  # 정형식 검사
    xml.dom.minidom.parseString(sec.encode("utf-8"))
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), (T / "mimetype").read_bytes(), compress_type=zipfile.ZIP_STORED)
        for rel in ["version.xml", "settings.xml", "META-INF/container.xml", "META-INF/container.rdf", "META-INF/manifest.xml", "Contents/header.xml"]:
            z.write(T / rel, rel, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("Contents/content.hpf", content_hpf(), compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("Contents/section0.xml", sec, compress_type=zipfile.ZIP_DEFLATED)
        for i, p in enumerate(IMAGES, 1): z.write(p, f"BinData/image{i}.png", compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("Preview/PrvText.txt", preview_text(), compress_type=zipfile.ZIP_DEFLATED)
    return len(IMAGES)

# =====================================================================
# 3. HTML 미리보기 (같은 내용 · A4)
# =====================================================================
def build_html():
    e = esc; fonts = (ROOT / "web/assets/fonts").as_uri()
    def tbl(header, rows, cls="t", widths=None):
        colg = "".join(f'<col style="width:{w}%">' for w in widths) if widths else ""
        return f'<table class="{cls}">{colg}<tr>{"".join(f"<th>{e(h)}</th>" for h in header)}</tr>' + "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in rows) + "</table>"
    h = [f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{e(R["title"])}</title><style>
@font-face{{font-family:"Gothic A1";font-weight:400;src:url({fonts}/gothic-a1-korean-400-normal.woff2)}}@font-face{{font-family:"Gothic A1";font-weight:700;src:url({fonts}/gothic-a1-korean-700-normal.woff2)}}
@page{{size:A4;margin:22mm 20mm 18mm}} body{{font-family:"Gothic A1","Malgun Gothic",sans-serif;font-size:11pt;line-height:1.75;color:#111;margin:0}}
.cover{{height:245mm;position:relative;text-align:center}} .cover .box{{border:1px solid #111;padding:14px 20px;font-size:19pt;font-weight:700;line-height:1.6;margin:0 10mm}}
.cover .date{{position:absolute;top:120mm;left:0;right:0;font-size:17pt;font-weight:700}} .cover .co{{position:absolute;top:210mm;left:0;right:0;font-size:15pt}} .cover .co b{{display:block;font-size:16pt}}
h2{{font-size:14pt;margin:18px 0 8px;page-break-after:avoid}} .pb{{page-break-before:always}} p{{margin:2px 0 2px 12px}} p.sub{{margin-left:36px}} p.sub2{{margin-left:52px}}
table{{border-collapse:collapse;width:100%;margin:6px 0 12px;font-size:10pt;page-break-inside:auto}} th,td{{border:1px solid #333;padding:5px 8px;vertical-align:middle}} th{{background:#E8EEF7;font-weight:700;text-align:left}}
table.g td{{text-align:center;height:24px}} table.g td.on{{background:#8a8a8a}} table.g th{{text-align:center}}
.box{{border:1px solid #111;padding:8px 12px;margin:6px 0 12px}} .box b{{display:block}} .box div{{margin-left:10px}}
table.r tr{{page-break-inside:avoid}} table.r td{{padding:0}} table.r td.n{{text-align:center;font-weight:700;width:18%;padding:6px}} table.r td.l{{background:#E6E6E6;text-align:center;font-weight:700;padding:3px}} table.r td.i{{text-align:center;padding:4px}} table.r img{{max-width:100%;max-height:225mm;display:inline-block}}
table.s td{{text-align:center;height:34px;font-size:11pt}} a{{color:#00f}}
</style></head><body>''']
    h.append(f'<div class="cover"><div class="box">{e(R["title"])}<br>{e(R["subtitle"])}</div><div class="date">{e(R["date"])}</div><div class="co"><b>{e(R["company"])}</b>대표자: &nbsp; {e(R["ceo"])} &nbsp; (인)</div></div>')
    h.append('<h2 class="pb">1. 용역 개요</h2>')
    for line, subs in R["overview"]:
        h.append(f"<p>{e(line)}</p>"); h += [f'<p class="sub">- {e(s)}</p>' for s in subs]
    h.append("<h2>2. 주요 요청 사항</h2>" + tbl(["항목", "요청사항", "달성도", "비고"], R["requests"], widths=[26, 30, 11, 33]))
    h.append('<h2 class="pb">3. 용역결과 및 주요성과</h2><p>가. 완료된 주요 기능</p>')
    for t, subs in R["features"]:
        h.append(f'<p class="sub">{e(t)}</p>'); h += [f'<p class="sub2">- {e(s)}</p>' for s in subs]
    h.append("<p>나. 기술적 구현사항</p>" + "".join(f'<p class="sub">- {e(s)}</p>' for s in R["tech"]))
    h.append("<p>다. 산출물 내역</p>" + tbl(["번호", "산출물명", "상세내용", "전달방법"], R["deliverables"], widths=[8, 24, 44, 24]))
    h.append('<h2 class="pb">4. 추진일정</h2>' + tbl(["구분", "주요 업무", "일정"], R["schedule"], widths=[22, 56, 22]))
    wk = R["gantt_weeks"]
    g = f'<table class="g"><tr><th rowspan="2">구분</th><th colspan="{len(wk)}">추진일정</th><th rowspan="2">비고</th></tr><tr>{"".join(f"<th>{w}</th>" for w in wk)}</tr>'
    for name, on in R["gantt"]: g += f"<tr><td style='text-align:left'>{e(name)}</td>" + "".join(f'<td class="{"on" if v else ""}"></td>' for v in on) + "<td></td></tr>"
    h.append("<h2>5. 과업의 수행일정</h2>" + g + "</table>")
    h.append('<h2>6. 기대효과 및 활용방안</h2><div class="box">' + "".join(f"<b>{e(t)}</b>" + "".join(f"<div>- {e(s)}</div>" for s in subs) for t, subs in R["effects"]) + "</div>")
    h.append('<h2 class="pb">7. 결과물</h2><table class="r"><tr><th style="text-align:center;width:18%">산출물명</th><th style="text-align:center">개별항목</th></tr>')
    for name, items in R["results"]:
        for i, (label, path) in enumerate(items):
            h.append("<tr>" + (f'<td class="n" rowspan="{2*len(items)}">{e(name).replace(chr(10), "<br>")}</td>' if i == 0 else "") + f'<td class="l">{e(label)}</td></tr><tr><td class="i"><img src="{path.as_uri()}"></td></tr>')
    h.append("</table>")
    h.append('<h2 class="pb">8. 납품 완료 항목</h2>')
    for line, sub in R["delivered"]:
        h.append(f"<p>{e(line)}</p>")
        if sub: h.append(f'<p class="sub">{("<a>" + e(sub) + "</a>") if sub.startswith("http") else e(sub)}</p>')
    for label, path in R["delivered_pics"]:
        h.append(f'<table class="r"><tr><td class="l">{e(label)}</td></tr><tr><td class="i"><img src="{path.as_uri()}" style="max-height:120mm"></td></tr></table>')
    h.append("<h2>9. 수정 반영 현황</h2>" + "".join(f"<p>- {e(f)}</p>" for f in R["fixes"]))
    s = R["sign"]
    h.append(f'<br><br><table class="s"><tr><td style="width:34%">{e(s[0])}</td><td style="width:26%">{e(s[1])}</td><td>{e(s[2])}</td><td>{e(s[3])}</td><td>{e(s[4])}</td><td>{e(s[5])}</td></tr></table>')
    h.append("</body></html>")
    return "".join(h)

if __name__ == "__main__":
    n = write_hwpx(OUT / f"{NAME}.hwpx")
    (OUT / f"{NAME}.html").write_text(build_html(), encoding="utf-8")
    print("wrote", OUT / f"{NAME}.hwpx", f"({n} images)", "and .html")
