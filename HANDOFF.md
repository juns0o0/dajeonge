# 다정이 MVP 인수인계 (2026-11-07)

## 한 줄 상태
작업지시서 R4 범위의 기능이 모두 동작하고(단위 테스트 7개·e2e·캡처 60장 통과), 계약 문서 R4·결과보고서·설계 문서까지 만들어져 저장소 https://github.com/juns0o0/dajeonge 에 올라가 있다. 남은 것은 **배포(HTTPS 주소)**, **발주사 확정값 입력**, **실제 OpenAI 키 연결**이다.

## 지금까지 결정된 것
| 결정 | 내용 | 근거 |
| --- | --- | --- |
| 음성 입력 | 브라우저 음성 인식(Web Speech API, Chrome) + 기본 TTS, 미지원 기기는 글 입력. 서버 STT는 파일 업로드용 보조 | 5주·700만 원에서 실시간 서버 STT는 무리, 브라우저 인식은 비용 0 |
| 서버 범위 | "서버 1식" 대신 연동 API(`/api/admin/*` 15종) + 데이터 관리 백오피스(`/admin.html`) | 발주사가 나중에 기관 도구를 붙일 수 있게. 계약서 R4 §3 |
| 배지 | 평소 / 관찰 / 확인 · 기준 수집 중 (긍정·부정·중립 아님) | 의료 판정이 아니라는 원칙 |
| 디자인 | 발주사(정준수)가 Claude Design으로 확정한 핸드오프 패키지(`docs/design/`)를 그대로 구현. 같은 토큰을 태블릿·앱·백오피스에 적용 | 처음 라임 플랫 UI는 템플릿처럼 보여 폐기 |
| 글꼴 | Jua(제목) + Pretendard Variable(본문), 자체 호스팅 | 디자인 확정본 지정, CDN 차단 환경 대응 |
| 저장소 | juns0o0/dajeonge 전용 계정. 회사 계정(brandnaut-dev) 사용 금지 | 발주사 이관 대비 |
| 결과보고서 | 레코 양식(용역 결과 보고서)을 따라 한글 HWPX로 생성 (`scripts/build_report_hwpx.py`) | 발주사 요청 양식 |

## 남은 일 (우선순위 순)
1. **배포**: Dockerfile로 바로 올라간다. Railway(볼륨 지원) 권장: GitHub 저장소 연결 → 환경변수(`ADMIN_TOKEN`, `PASSWORD_SALT`, `OPENAI_API_KEY`, `DATABASE_URL=sqlite:////data/dajeong.db`, `AUDIO_DIR=/data/audio`) → 볼륨을 `/data`에 마운트 → 생성된 https 주소 확인. Dockerfile의 포트는 8000 고정이므로 플랫폼이 `PORT`를 주면 CMD를 `--port ${PORT:-8000}`로 바꾼다. 음성 인식은 HTTPS에서만 동작한다.
2. **랜딩 대괄호 채우기** (`web/index.html`): 참여 조건 5줄(대상 가정·테스트 기간·비용·태블릿 준비·참여자가 할 일), FAQ 5·6번 답변, 만든 사람들(팀명·이름·이메일·정책 링크). 발주사 확정값만 넣는다.
3. **실제 키·도메인**: OpenAI 키(발주사 명의), 도메인 연결, 개인정보·음성 동의 문구 검토본 반영(`web/privacy.html`).
4. **검수**: `docs/06_검수체크리스트.md` 26항목을 발주사와 같이 점검, 결과보고서의 날짜(12.11 기준)·수정 반영 현황·확인자 서명란을 실제 값으로.
5. **결과보고서 한글 파일**: 이 환경에서는 한글(HWP)을 열 수 없어 XML 구조 검증만 했다. 한글에서 열어 표 높이·페이지 나눔을 한 번 확인한다. PDF는 같은 내용을 브라우저로 그린 미리보기다.

## 폴더 지도
```
server/            FastAPI 앱 (main.py 라우터 40개, metrics.py 지표, jobs.py 워커, ai.py OpenAI/MOCK) · seed.py · tests/
web/               index.html(랜딩 확정본) · tablet.html · app.html+assets/app.js · admin.html+assets/admin.js · assets/dajeong.css(토큰) · illus.js · fonts/
docs/              01 기능명세(md+xlsx) · 02 흐름도 · 03 ERD · 04 API · 05 운영 매뉴얼 · 06 검수 체크리스트 · 07 디자인 가이드 · design/(디자인 사양·토큰·레퍼런스) · diagrams/ · captures/ · 결과보고서/
contract/          견적서·계약서·작업지시서 R4 (docx+pdf) · revise_docs.py · 개정요약 · _src/(원본, git 제외)
scripts/           e2e.js · capture_report.js · render_diagrams.js · build_spec_xlsx.py · build_report_hwpx.py(+report_template/) · report_pdf.js · diagrams/
```

## 외부 문서 (claude.ai)
- 과업지시서(편집용): https://claude.ai/artifact/9k1NEkagaXk5ypYxCEeVpJ
- 다정이 대표 공유용 진행 현황: https://claude.ai/artifact/M9NjKrxAHm79HMrfBBt98x
- 디자인 요청서(확정 전 브리프, 참고용): https://claude.ai/artifact/F5gypfWSw2eEa5eyZsXPiH

## 주의
- 계약 원본(R2) docx 3개는 `contract/_src/`에만 있고 git에 올리지 않는다. 문서를 다시 만들 때 이 폴더가 필요하다.
- 캡처 파일명의 대화 번호는 실행할 때마다 바뀐다. 보고서 생성기는 번호 접두어(A01, C05 …)로 찾는다.
- 세션 컨테이너는 사라진다. 결과물은 반드시 저장소에 커밋·푸시한다.
