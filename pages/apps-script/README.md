# 랜딩 신청 저장 연결 (구글 시트) — 발주사 계정으로, 약 3분

GitHub Pages 에 올린 랜딩(https://juns0o0.github.io/dajeonge/)은 정적이라 서버가 없다.
신청은 구글 시트에 쌓고, Apps Script 웹앱이 `POST /api/applications` 대신 창구 역할을 한다.
신청자 열람 화면(https://juns0o0.github.io/dajeonge/applicants.html)도 같은 웹앱에서 키를 붙여 읽는다.

**시트와 Apps Script 는 발주사(인하우스앤파트너스) 구글 계정으로 만든다.** 신청자 개인정보가 발주사 소유여야 하고(계약 §6), 수행사 계정에 만들면 나중에 옮길 수 없기 때문이다.
아래 1~3 을 발주사가 하고, 3번의 **웹 앱 URL** 과 **시트 주소**를 수행사에 전달하면 수행사가 4번을 반영한다.

## 1. 시트 만들기
1. https://sheets.new 에서 새 스프레드시트 생성. 이름 예: `다정이_랜딩_신청`
2. 메뉴 **확장 프로그램 > Apps Script**

## 2. 스크립트 붙여넣기
1. 편집기의 기본 코드를 모두 지우고 `Code.gs` 내용을 붙여넣기
2. 맨 위 `ADMIN_KEY = "CHANGE-ME"` 를 **긴 임의 문자열**로 바꾼다. 이 값이 열람 화면 비밀번호다.
3. 저장 (⌘S)

## 3. 웹앱으로 배포
1. 오른쪽 위 **배포 > 새 배포** → 톱니 > **웹 앱**
2. 실행: **나** / 액세스 권한: **모든 사용자** → **배포** → 권한 승인
3. **웹 앱 URL** 복사 (`https://script.google.com/macros/s/.../exec`)

## 4. 사이트에 연결
`pages/config.json` 을 채우고 커밋·푸시하면 Actions 가 다시 배포한다.
```json
{ "applyEndpoint": "https://script.google.com/macros/s/XXXX/exec", "sheetUrl": "https://docs.google.com/spreadsheets/d/XXXX/edit" }
```

## 확인
- `웹앱URL` 을 열면 `{"ok":true,"service":"dajeong-landing","ready":true}`. `ready:false` 면 ADMIN_KEY 를 아직 안 바꾼 것.
- 랜딩에서 신청 → 시트에 `applications`, `log` 탭이 생기고 한 줄 쌓인다.
- 열람: `https://juns0o0.github.io/dajeonge/applicants.html` 에서 키 입력.

## 저장되는 것
서버 DB `applications` 테이블과 같은 열: id · created_at(서울) · kind(home/org) · name · org_name · phone · email · message · agreed · status(new/contacted/done) · note · user_agent · referrer.
나중에 서버(Railway 등)로 옮길 때 시트를 그대로 가져오면 된다.
