# 다정이 (Dajeong) MVP

AI Care Bot ‘다정이’ 웹 MVP. 부모님은 태블릿 버튼 하나로 자녀 말투의 다정이와 대화하고, 보호자는 대화 속 변화를 본인의 평소와 비교해 확인한다.

- 발주: 인하우스앤파트너스(주) · 수행: 펄스픽시아 · 계약 범위: `contract/3. 다정이 MVP 작업지시서 (R4).pdf`
- 저장소: https://github.com/juns0o0/dajeonge (다정이 전용, Private)
- 의료 진단 서비스가 아니다. 지표와 요약은 참고용이며 병명·진단 표현을 쓰지 않는다.

## 구성
```
server/   API 서버 + 작업 워커 (대화 저장 · 지표 분석 · AI 요약 · 백오피스/연동 API)   → /docs 에 Swagger
web/      정적 프론트엔드  index.html(랜딩, 디자인 확정본) · tablet.html(부모님) · app.html(보호자) · admin.html(백오피스) · fonts/(Jua·Pretendard Variable, OFL)
docs/     기능명세 · 흐름도 · ERD · API 문서 · 운영 매뉴얼 · 검수 체크리스트 · 디자인 가이드 · design/(디자인 사양·토큰·레퍼런스) · 캡처
contract/ 견적서 · 계약서 · 작업지시서 (R4, docx+pdf) · 개정 요약
scripts/  e2e 점검(캡처) 스크립트
archive/  계약 전 시연 자료 (참고용)
```

## 빠르게 실행
```bash
cd server
python3 -m pip install -r requirements.txt
python3 seed.py                                  # 검수용 가족 DEMO1 (보호자 1234 / 태블릿 0000)
python3 -m uvicorn app.main:app --reload         # http://localhost:8000  (백오피스 /admin.html · 토큰 admin-dev-token)
```
`OPENAI_API_KEY` 가 없으면 MOCK 모드로 전체 흐름이 돌아간다 (`.env.example` 참고). 테스트: `python3 -m pytest -q`.

## 산출물 ↔ 작업지시서 §4
| 작업지시서 산출물 | 위치 |
| --- | --- |
| 음성 대화 저장과 연동 API (태블릿 웹앱 · API · DB) | `server/`, `web/tablet.html`, `docs/04_API문서.md`, `Dockerfile`, `docker-compose.yml` |
| 데이터 관리 백오피스 | `web/admin.html`, `web/assets/admin.js`, `server/app/main.py` (`/api/admin/*`) |
| 대화 분류와 지표 (소스·계산식·테스트) | `server/app/metrics.py`, `server/tests/test_metrics.py`, `docs/01_기능명세서.md` F2 |
| 보호자 대시보드와 AI 리포트 | `web/app.html`, `web/assets/app.js`, `server/app/main.py` (dashboard·summaries) |
| 랜딩페이지 | `web/index.html` (+ `privacy.html`) |
| 설계·원본자료 | `docs/01~04`, `docs/07_디자인가이드.md`(코드가 원본) |
| 검수·운영 자료 | `docs/06_검수체크리스트.md`, `docs/captures/`(10장), `docs/05_운영매뉴얼.md` |

## 상태
계약 범위(작업지시서 R4 §2)의 기능이 모두 동작한다. 검수 기준은 `docs/06_검수체크리스트.md` 26항목, 화면 캡처는 `docs/captures/결과보고서용/`. 실제 운영에는 OpenAI 키, 도메인(HTTPS), 발주사 검토본 동의 문구가 필요하다.
