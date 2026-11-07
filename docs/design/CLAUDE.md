# 다정이 랜딩 페이지 — Claude Code 작업 지침

이 폴더는 디자인 확정본을 그대로 구현하기 위한 핸드오프 패키지다.
**목표는 재해석이 아니라 픽셀·모션 동일 재현이다.**

## 정답(source of truth)

1. `index.html` — 브라우저에서 바로 열리는 완성본. 레이아웃, 카피, 색, 크기, 애니메이션, 인터랙션이 모두 들어 있다. 다른 문서와 값이 다르면 **index.html이 이긴다.**
2. `reference/desktop-full.png`, `reference/mobile-full.png` — 1280px / 390px 전체 페이지 캡처(2x). 구현 후 같은 폭으로 캡처해 나란히 비교한다.
3. `DESIGN.md` — 토큰, 컴포넌트 규칙, 모션 사양을 사람이 읽기 좋게 정리한 것.
4. `tokens.css` — 프레임워크로 옮길 때 쓰는 CSS 변수.
5. `assets/*.svg` — 로고와 캐릭터(블롭) 원본. 경로(`d`)와 눈 위치를 바꾸지 않는다.

## 규칙

- 숫자를 반올림하거나 4/8px 그리드, Tailwind 기본값, 프레임워크 기본값으로 "정리"하지 않는다. `clamp()`, `%`, `cubic-bezier` 값까지 그대로 옮긴다.
- 카피(문구)를 다듬거나 바꾸지 않는다. `[대괄호]` 안의 문구는 사용자가 채울 자리표시자다. 그대로 둔다.
- 글꼴: 제목은 **Jua**(`fonts/jua.css`, 로컬 번들, OFL), 본문은 **Pretendard Variable**(`fonts/PretendardVariable.woff2`). 다른 글꼴로 대체하지 않는다.
- 그림자는 쓰지 않는다(헤더의 1px 링, 토글 손잡이만 예외). 면 색 차이로 층을 나눈다.
- 이모지·아이콘 폰트 금지. 아이콘은 index.html의 인라인 SVG를 그대로 쓴다.
- `prefers-reduced-motion: reduce`에서는 모든 애니메이션·트랜지션을 끈다(index.html의 미디어 쿼리 참고).
- 1px라도 가로 스크롤이 생기면 버그다. 390px 폭에서 확인한다.

## 프레임워크로 옮길 때 (React / Next.js 등)

요청받은 스택이 있으면 그 스택으로 옮기되 다음을 지킨다.

- 컴포넌트 분리 예: `Header`, `HeroCard`, `TabletCard`, `WeekCard`(토글 포함), `HowCard`, `StepsCard`, `FamilyAppCard`(폰 목업), `BeforeAfterCard`, `RecruitCard`, `ProcessCard`, `ApplyForm`, `FaqCard`, `TeamCard`, `Footer`, `Blob`(SVG 캐릭터), `ArrowCircle`, `PillButton`.
- 인라인 스타일을 CSS Modules / Tailwind arbitrary values / styled 등으로 옮겨도 **계산 결과 값은 동일**해야 한다.
- `app.js` 로직(index.html 하단 `<script>`)의 상태와 동작:
  - 한 주 토글: 켜짐이 기본값. 켜질 때 평일 칸의 캐릭터가 요일 순서대로 70ms 간격(stagger)으로 나타나고, 꺼질 때는 지연 없이 사라진다.
  - FAQ: 한 번에 하나만 열린다. 첫 질문이 열린 상태로 시작한다.
  - 신청 폼: 가정용/기관용 라디오에 따라 필드가 바뀐다. 이름이 비어 있으면 에러를 표시한다. 제출하면 완료 화면, '처음으로'를 누르면 초기화한다. 실제 전송은 `TODO` 자리에 연결한다.
- 다 옮긴 뒤 `reference/` 캡처와 비교하고, 다른 곳을 목록으로 보고한다.

## 열어 보기

```bash
npx serve .        # 또는 python3 -m http.server
# http://localhost:3000 (serve) / http://localhost:8000 (python)
```

`file://`로 열어도 동작한다.
