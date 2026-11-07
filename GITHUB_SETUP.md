# 다정이 전용 GitHub 계정·저장소 만들기 (5분)

이 폴더는 이미 로컬 Git 저장소로 초기화되어 커밋이 들어 있다. 아래만 하면 바로 푸시할 수 있다.

## 1. 계정 (선택: 전용 계정 또는 기존 계정의 Organization)
- 전용 계정: https://github.com/signup → 이메일은 다정이 운영용(예: dev@…) 권장. 사용자명 예: `dajeong-ai`
- 또는 기존 계정에서 Organization 만들기: 프로필 → Your organizations → New organization (Free) → 이름 `dajeong-ai`

## 2. 저장소
- https://github.com/new → Owner `dajeong-ai` · Repository name `dajeong-mvp` · **Private** · README 추가 안 함 → Create

## 3. Claude 에게 권한 주기
- https://github.com/apps/claude/installations/select_target → `dajeong-ai` 선택 → Only select repositories → `dajeong-mvp` → Save
- (전용 계정을 새로 만든 경우) https://claude.ai/connect-github 에서 그 계정으로 한 번 연결

## 4. 푸시
저장소 주소(`dajeong-ai/dajeong-mvp`)를 Claude 에게 알려주면 세션에 연결해 푸시한다. 직접 하려면:
```bash
cd dajeong-mvp
git remote add origin git@github.com:dajeong-ai/dajeong-mvp.git
git push -u origin main
```

## 5. 발주사 인수인계 때
- 발주사 GitHub 계정을 Collaborator(또는 저장소 이전)로 추가 → 계약 §10 소유권 이전 근거.
- `.env`, 도메인·클라우드·OpenAI 계정은 처음부터 발주사 명의로 만든다 (계약 §6).
