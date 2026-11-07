# 다정이 MVP ERD

소스: `server/app/models.py`. 기본 SQLite 파일(`server/data/dajeong.db`), `DATABASE_URL` 로 PostgreSQL 전환 가능.

```mermaid
erDiagram
  families ||--|| personas : has
  families ||--o{ memories : has
  families ||--o{ conversations : has
  families ||--o| baselines : has
  families ||--o{ summaries : has
  families ||--o{ sessions : logs_in
  conversations ||--o{ turns : has
  conversations ||--o| conversation_metrics : scored
  conversations ||--o{ summaries : summarized

  families {
    int id PK
    string code UK "가족 코드 (로그인)"
    string parent_name
    int parent_age
    string region
    string guardian_name
    string guardian_relation
    string guardian_password "해시"
    string tablet_password "해시"
    int keep_audio_days "음성 보관 일수"
    datetime created_at
  }
  personas {
    int id PK
    int family_id FK
    string display_name "자녀 이름"
    string calls_parent "호칭"
    string formality
    json endings
    json expressions
    json personality
    json habits
    json avoid_topics
    text family_notes
  }
  memories {
    int id PK
    int family_id FK
    string title
    text detail
    json keywords "응답 생성 시 검색 키"
    int year
    text reserved_recall_question "(예약) 기억 회상 질문"
  }
  conversations {
    int id PK
    int family_id FK
    datetime started_at
    datetime ended_at
    string source "tablet | upload | seed"
    string status "open | finished | analyzed | failed"
    string audio_path
    text error
  }
  turns {
    int id PK
    int conversation_id FK
    string speaker "bot | parent"
    text text
    datetime started_at
    datetime ended_at
    string input_mode "voice | text"
    json tags "repeat | uncertain"
    int char_len
    float response_gap_sec
    string reserved_recall_result "(예약)"
  }
  conversation_metrics {
    int id PK
    int conversation_id FK
    int family_id FK
    int parent_turns
    float avg_utterance_len
    float repeat_rate
    float uncertain_rate
    float avg_response_gap
    float participation
    float duration_sec
    bool valid "부모 발화 3회 이상"
    datetime computed_at
    float reserved_consistency "(예약) 일관성 점수"
  }
  baselines {
    int id PK
    int family_id FK
    datetime fixed_at
    int n_conversations
    json values "{metric: {mean, sd, n}}"
  }
  summaries {
    int id PK
    int family_id FK
    string kind "conversation | weekly"
    int conversation_id FK
    datetime period_start
    datetime period_end
    text text
    string status "pending | done | failed"
    text error
    string model
  }
  jobs {
    int id PK
    string kind "analyze | summarize"
    int ref_id "conversation_id | summary_id"
    int family_id
    string status "queued | running | done | failed"
    int attempts
    text error
  }
  api_usage {
    int id PK
    int family_id
    string provider
    string purpose "reply | stt | tags | summary"
    string model
    int input_tokens
    int output_tokens
    bool ok
    text error
  }
  applications {
    int id PK
    string kind "home | org"
    string name
    string org_name
    string phone
    string email
    string region
    text message
    bool agreed
  }
  sessions {
    int id PK
    string token UK
    int family_id
    string role "guardian | tablet"
  }
```

## 향후 연결 위치 (이번 범위 밖, 작업지시서 §7)
| 향후 항목 | 연결 위치 |
| --- | --- |
| 기억 회상 정답률 | `memories.reserved_recall_question` 에 질문을 두고, 부모 발화에 `turns.reserved_recall_result`(ok/fail) 를 기록 → `conversation_metrics` 에 비율 컬럼 추가 |
| 일관성 점수 | `conversation_metrics.reserved_consistency` (LLM 채점) |
| 자동 알림 | `baselines` 비교 결과가 `notable` 로 2주 연속이면 새 `alerts` 테이블에 생성, 보호자 연락처로 발송 |
| 음성 감정 | `turns` 에 `emotion` 컬럼 추가, 음성 파일(`conversations.audio_path`) 기반 |
