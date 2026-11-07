# 다정이 디자인 사양

모든 값은 `index.html`에서 그대로 뽑은 것이다.

## 1. 색

| 토큰 | 값 | 쓰임 |
|---|---|---|
| `--ink` | `#111111` | 글자, 주 버튼, 로고, 캐릭터 눈 |
| `--page` | `#F4F0EA` | 페이지 바탕, 보조 칩·말풍선 바탕 |
| `--card` | `#FFFDFA` | 모든 카드 바탕 |
| `--blob` | `#F1ECE4` | 히어로 메인 캐릭터 |
| `--yellow` | `#FFE59A` | 화살표 원, 모집 카드, 캐릭터 |
| `--pink` | `#FFB5C1` | '안부 전화' 칩, 캐릭터 |
| `--mint` | `#B7E1D1` | 자녀 앱 요약 카드, 캐릭터 |
| `--sky` | `#A9D3FF` | 태블릿 카드 그라디언트, 캐릭터 |
| `--green` | `#5BBE8E` | 토글 켜짐, '평소' 점 |
| `--amber` | `#F2B33D` | '관찰' 점 |
| `--text-2` | `#3C3934` | 본문 |
| `--text-3` | `#6B665E` | 보조 글자, 라벨 |
| `--text-4` | `#A39C90` | 비활성 라벨, 자리표시자 값 |
| `--line` | `#F0EAE0` | 목록 구분선 |
| `--line-2` | `#ECE6DC` | 카드 테두리(1.5px) |
| `--field` | `#D9D2C6` | 입력칸 테두리, 토글 꺼짐 |
| `--error` | `#C2414F` | 입력 오류 |

하늘 카드 그라디언트: `linear-gradient(170deg,#CFE6FB 0%,#A9D3FF 70%,#9CCAF5 100%)`

## 2. 글꼴

- **Jua 400**: 모든 제목, 로고 글자, 강조 문장. 줄 간격은 1.2(히어로), 1.35(섹션 제목), 1.4(카드 제목).
- **Pretendard Variable**: 본문 14px/1.85, 보조 12–13px, 라벨 11px 800 대문자, 글자 간격 .1em(`.lbl`).
- 크기:
  - 히어로 `clamp(40px,5.2vw,64px)`
  - 섹션 제목 `clamp(26px,3vw,38px)`
  - 모집 카드 제목 `clamp(24px,2.6vw,32px)`
- 한국어 줄바꿈: `word-break:keep-all`.

## 3. 레이아웃

- 컨테이너 `max-width:1200px`, 좌우 `clamp(12px,2vw,24px)`, 카드 간격 16px.
- 카드 모서리 28px, 안쪽 카드 22px, 입력칸 10px, 버튼·칩은 999px(알약).
- 카드 패딩 `clamp(24px,3.4vw,44px)`.
- 첫 줄: 히어로 `flex:1.45 1 520px` + 태블릿 카드 `flex:1 1 360px`. 공간이 모자라면 줄바꿈된다.
- 2단 섹션: `repeat(auto-fit,minmax(min(100%,340px),1fr))`.
- 헤더는 `position:sticky; top:12px`.
- 640px 이하:
  - 메뉴 글자 링크 숨김
  - 히어로 `padding-top:190px`, 캐릭터는 위쪽(`top:-3%; right:-8%; width:60%`)
  - 태블릿 카드 `min-height:440px`

## 4. 컴포넌트

- **주 버튼(PillButton)**: 검정 알약, 높이 52, 패딩 `0 10px 0 26px`, 14px 700, 오른쪽에 32px 노란 원 + 화살표 SVG.
- **화살표 원(ArrowCircle)**: 노랑 원 24/26/32px, 화살표 path `M3 8h9M8.5 4.5 12 8l-3.5 3.5`, 선 두께 1.8–2.
- **칩**: 높이 약 32, 패딩 `8px 14px`, 12px 800, 파스텔 바탕. 선택된 칩은 검정 바탕 + 흰 글자.
- **입력칸**: 높이 48, 테두리 1.5px `#D9D2C6`, 모서리 10.
- **토글**: 64×36, 손잡이 30, 켜짐 `#5BBE8E` / 꺼짐 `#D9D2C6`.
- **목록 행**: 왼쪽 10px 색 점 + 제목 14px 800 + 설명 12px, 행 사이 1px 선.
- **캐릭터(Blob)**: 비정형 SVG 덩어리 + 검정 타원 눈 두 개. 입은 없다. 원본은 `assets/`.
- **푸터**: 위쪽 물결 SVG(높이 20) + 카드, 분홍 캐릭터가 아래에서 빼꼼 나온다.

## 5. 모션

| 이름 | 대상 | 사양 |
|---|---|---|
| blink | 캐릭터 눈 `<g>` | `5s infinite`, 키프레임 `0%,92%,100% scaleY(1)` / `95% scaleY(.1)`, `transform-box:fill-box; transform-origin:center` |
| blink2 | 일부 캐릭터 눈 | 같은 키프레임, `6.2s`, 지연 `1.4s` (동시에 깜빡이지 않게) |
| float | 히어로 캐릭터, 구름, 모집 캐릭터 | `6s ease-in-out infinite`, `0%,100% translateY(0) rotate(0)` / `50% translateY(-8px) rotate(-1.5deg)` |
| float2 | 구름, 푸터 캐릭터 | 같은 키프레임, `7s`, 지연 `1s` |
| pill hover | 주 버튼 | `translateY(-2px)`, 누르면 `translateY(1px)`. 화살표 원은 `translateX(2px)`. `.16s cubic-bezier(.16,1,.3,1)` |
| lift hover | 클릭 가능한 카드 | `translateY(-4px)`, `.2s cubic-bezier(.16,1,.3,1)` |
| toggle | 스위치 | 손잡이 `translateX(28px)` `.25s cubic-bezier(.65,0,.35,1)`, 바탕색 `.25s ease`, 양옆 라벨 색 `.25s` |
| week reveal | 평일 칸 캐릭터 | 켜짐: `opacity 0→1`, `translateY(10px) scale(.5) → none`, `.45s cubic-bezier(.16,1,.3,1)`, 지연 `요일 번호 × 70ms`. 꺼짐: 같은 시간, 지연 0. `transform-origin:0 100%` |
| faq | 아코디언 | 패널 `grid-template-rows 0fr↔1fr .32s cubic-bezier(.65,0,.35,1)`, 아이콘 `rotate(45deg)` + 바탕 `#F4F0EA→#FFE59A` `.3s` |
| chips | 선택 칩 | 바탕색·글자색 `.2s ease` |

- 모션 원칙: 자동으로 반복되는 움직임은 눈 깜빡임과 느린 둥실거림뿐이다. 나머지는 모두 사용자 행동에 대한 반응이다. 스크롤 등장 애니메이션은 넣지 않는다.
- `@media (prefers-reduced-motion: reduce)`: `animation:none !important; transition-duration:.01ms !important`.
