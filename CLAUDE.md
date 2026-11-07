# 다정이 MVP — 작업 지침 (Claude Code가 자동으로 읽는 파일)

AI Care Bot ‘다정이’ 웹 MVP. 발주 인하우스앤파트너스(주), 수행 펄스픽시아(대표 정준수). 계약 ₩7,000,000(VAT 별도), 21.5 M/D, 2026.10.13 ~ 11.13.
현재 상태와 남은 일은 `HANDOFF.md`, 계약 범위는 `contract/3. 다정이 MVP 작업지시서 (R4).pdf`.

## 저장소·계정
- 원본 저장소: https://github.com/juns0o0/dajeonge (Private, 다정이 전용). 회사 계정 `brandnaut-dev`나 회사 저장소에는 절대 올리지 않는다.
- 커밋 작성자: 정준수 <jesse@brandnaut.xyz>. PR은 요청받을 때만 만든다.

## 실행
```bash
cd server && python3 -m pip install -r requirements.txt && python3 seed.py   # 검수용 가족 DEMO1 (보호자 1234 / 태블릿 0000)
python3 -m uvicorn app.main:app --reload                                      # http://localhost:8000  백오피스 /admin.html (토큰 admin-dev-token), API 문서 /docs
python3 -m pytest -q                                                          # 단위 테스트 7개
```
`OPENAI_API_KEY`가 없으면 MOCK 모드로 전체 흐름이 돈다. `.env.example` 참고. `python3`은 3.11, pip은 반드시 `python3 -m pip`.

## 산출물 다시 만들기 (순서대로)
```bash
node scripts/e2e.js http://localhost:8000                                            # 전체 흐름 점검
NODE_PATH=$(npm root -g) node scripts/capture_report.js docs/captures/결과보고서용 http://localhost:8000   # 캡처 60장
node scripts/render_diagrams.js                                                      # docs/diagrams/*.png
python3 scripts/build_spec_xlsx.py                                                   # docs/다정이_MVP_기능명세서.xlsx
python3 scripts/build_report_hwpx.py && node scripts/report_pdf.js                   # docs/결과보고서/*.hwpx, *.pdf
python3 contract/revise_docs.py contract/_src contract                               # 계약 문서 (원본 docx는 _src/, git 제외)
```

## 바꾸면 안 되는 것
- 랜딩 `web/index.html`은 디자인 확정본(`docs/design/`) 그대로. 바꾼 곳은 신청 폼 전송(`POST /api/applications`)과 처리방침 링크 두 곳뿐. 카피·값·애니메이션을 다듬지 않는다. `[대괄호]`는 발주사 확정값으로만 채운다.
- 글꼴은 Jua·Pretendard Variable 자체 호스팅(`web/fonts/`). 외부 CDN 금지. 그림자 금지, 사람 얼굴 그리지 않음, 캐릭터는 블롭+눈.
- 배지는 평소 / 관찰 / 확인 · 기준 수집 중. 병명·진단·위험·점수·경고 표현 금지. 문구는 합니다체, 다정이 대사만 자녀 말투.
- 지표 5개와 기준선 규칙(첫 유효 대화 +14일·유효 5회, 1σ/1.5σ)은 `server/app/metrics.py`와 기능명세 F2가 원본.
- 디자인 토큰은 `docs/design/tokens.css` = `web/assets/dajeong.css :root`. 값이 다르면 tokens.css가 이긴다.

## 문서 어조
- 납품 문서(docs/, contract/, 결과보고서)는 발주사가 읽는 문서다. 내부 진행 서술("착수 전", "시연용", "AI가 만든")을 쓰지 않는다.
- 글을 쓰거나 고칠 때 `.claude/skills/void/SKILL.md`(VOID 검수) 기준을 먼저 적용한다: 맞는 말만 있고 판단이 없는 문장을 찾아 고친다.
