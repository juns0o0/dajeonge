# 다정이 MVP API 문서

서버 실행 중 `/docs`(Swagger UI)와 `/openapi.json` 에서 항상 최신 명세를 볼 수 있다. 아래는 2026-11-04 기준 요약. 인증은 `Authorization: Bearer <token>` (로그인 응답의 token), 백오피스·연동 API(`/api/admin/*`)는 `X-Admin-Token` 헤더(서버 환경변수 `ADMIN_TOKEN`). 백오피스 화면 `/admin.html` 이 쓰는 API 를 외부 시스템이 그대로 호출한다.

| 메서드 | 경로 | 태그 | 설명 |
| --- | --- | --- | --- |
| GET | `/api/health` | system | Health |
| POST | `/api/auth/login` | auth | Api Login |
| POST | `/api/auth/logout` | auth | Api Logout |
| GET | `/api/family` | family | Get Family |
| PUT | `/api/family` | family | Update Family |
| PUT | `/api/family/persona` | family | Update Persona |
| GET | `/api/family/memories` | family | List Memories |
| POST | `/api/family/memories` | family | Add Memory |
| PUT | `/api/family/memories/{memory_id}` | family | Edit Memory |
| DELETE | `/api/family/memories/{memory_id}` | family | Delete Memory |
| POST | `/api/conversations` | conversation | 대화 시작. 다정이의 첫마디를 함께 돌려준다. |
| GET | `/api/conversations` | conversation | List Conversations |
| POST | `/api/conversations/{conversation_id}/turns` | conversation | 부모님 발화 1개 저장 → 가족 기록 기반 다정이 응답 생성·저장 → 응답 텍스트 반환 (TTS는 브라우저). |
| POST | `/api/conversations/{conversation_id}/audio` | conversation | 브라우저 음성 인식이 안 되는 환경용: 녹음 파일을 올리면 서버에서 글자로 바꿔 돌려준다 (저장만, 발화 등록은 /turns). |
| POST | `/api/conversations/{conversation_id}/finish` | conversation | 대화 종료 → 분석 작업(analyze)을 큐에 넣는다. |
| GET | `/api/conversations/{conversation_id}` | conversation | Get Conversation |
| DELETE | `/api/conversations/{conversation_id}` | conversation | 운영자(보호자) 삭제 절차: 대화·발화·지표·음성 파일을 함께 지운다 (계약 §13). |
| GET | `/api/dashboard/overview` | dashboard | 최근 7일 지표 + 개인 기준선 + 비교 + 14일 일별 추이. |
| POST | `/api/summaries` | summary | 보호자가 버튼을 눌러 요약을 요청한다 (자동 생성 없음). 결과는 GET /api/summaries/{id} 로 확인. |
| GET | `/api/summaries` | summary | List Summaries |
| GET | `/api/summaries/{summary_id}` | summary | Get Summary |
| GET | `/api/jobs` | jobs | List Jobs |
| GET | `/api/jobs/{job_id}` | jobs | Get Job |
| POST | `/api/jobs/{job_id}/retry` | jobs | Retry Job |
| POST | `/api/applications` | landing | Create Application |
| POST | `/api/admin/families` | admin | 가족 등록 (코드·부모님·보호자·비밀번호 2종·페르소나) |
| GET | `/api/admin/families` | admin | 가족 목록 (q= 코드·이름 검색, 대화·이야기 수, 기준선 고정 여부) |
| GET | `/api/admin/stats` | admin | 백오피스 현황 카드: 가족·대화·신청·작업·외부 API 호출 수. |
| GET | `/api/admin/families/{family_id}` | admin | 가족 상세 (페르소나·가족 이야기·기준선·최근 대화·작업) |
| PUT | `/api/admin/families/{family_id}` | admin | 가족 정보 수정 · 비밀번호 재설정 |
| DELETE | `/api/admin/families/{family_id}` | admin | 가족 삭제(운영자 삭제 절차). 대화·발화·지표·기준선·요약·작업·세션·음성 파일을 함께 지운다. |
| GET | `/api/admin/families/{family_id}/export` | admin | 가족 1곳의 전체 기록을 JSON 한 벌로 내보낸다 (이관·외부 분석 연동용). |
| GET | `/api/admin/conversations` | admin | 모든 가족의 대화 목록 + 지표 (family_id, status 필터) |
| GET | `/api/admin/conversations/{conversation_id}` | admin | 대화 상세 (원문·태그·응답 간격·지표) |
| GET | `/api/admin/jobs` | admin | 분석·요약 작업 목록 (status 필터) |
| POST | `/api/admin/jobs/{job_id}/retry` | admin | 실패 작업 재시도 |
| GET | `/api/admin/applications` | admin | 랜딩 신청 목록 (status 필터) |
| PUT | `/api/admin/applications/{application_id}` | admin | 신청 상태(new·contacted·done)·메모 변경 |
| GET | `/api/admin/usage` | admin | 외부 API 사용량·오류 집계 (계약 §13). |
| GET | `/api/admin/usage/log` | admin | 최근 외부 API 호출 기록 |

## 주요 흐름

1. `POST /api/auth/login` {code, password, role: tablet|guardian} → token
2. `POST /api/conversations` → 대화 id + 첫마디
3. `POST /api/conversations/{id}/turns` {text, started_at, ended_at, input_mode, bot_spoke_until} → 다정이 응답
4. `POST /api/conversations/{id}/finish` → 분석 job
5. `GET /api/dashboard/overview` → 최근 7일 지표 · 기준선 · 비교 · 14일 추이
6. `POST /api/summaries` {kind: conversation|weekly, conversation_id?} → `GET /api/summaries/{id}` 로 결과 확인

오류 형식: `{"detail": "메시지"}` · 401 로그인 필요 · 403 역할/관리자 권한 · 404 가족 밖 기록 · 422 입력 검증 · 502 외부 API 실패

## 연동 API (백오피스 · 외부 시스템)

```bash
curl -H "X-Admin-Token: $ADMIN_TOKEN" https://<도메인>/api/admin/stats
curl -H "X-Admin-Token: $ADMIN_TOKEN" https://<도메인>/api/admin/families/1/export   # 가족 전체 기록 JSON
curl -X POST -H "X-Admin-Token: $ADMIN_TOKEN" -H "content-type: application/json" https://<도메인>/api/admin/families \
  -d '{"code":"SJ001","parent_name":"김영희","parent_age":78,"region":"세종시","guardian_name":"김보호","guardian_relation":"딸","guardian_password":"guardian-pw","tablet_password":"tablet-pw"}'
```

연동 순서(기관 관리 도구 예): ① 가족 등록 → ② 태블릿·보호자 앱은 그 가족 코드로 로그인 → ③ `GET /api/admin/conversations?status=analyzed` 와 `…/export` 로 지표를 가져가 기관 화면에 표시 → ④ 알림 발송(이번 범위 밖)은 같은 조회 결과로 연결한다.
