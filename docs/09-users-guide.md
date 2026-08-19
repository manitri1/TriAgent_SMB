# 09. 사용자 가이드 — 운영 및 트러블슈팅

> 이 문서는 `docker compose build/up`을 아직 실행하지 않은 상태에서 설계 단계에 작성됐습니다
> (이 환경에 Docker가 없습니다). 실제로 배포해 관찰한 내용이 아니라 `TriAgent_MICE`/
> `TriAgent_Planner`에서 검증된 내용을 바탕으로 한 예상 절차입니다 — 실행 후 실측 결과로
> 갱신해야 합니다.

## 0. 사전 준비

- Docker Desktop이 실행 중이어야 한다.
- `.hermes/.env`(`OPENAI_API_KEY`, `MOCK_POS_API_KEY`)와 7개 `.hermes/profiles/<role>/.env`가
  채워져 있어야 한다 — top-level `.env`는 프로필에 상속되지 않는다.
- `.hermes/profiles/*/USER.md`의 "(예시)" 표시를 실제 매장 정보로 교체했는지 확인한다.

## 1. 최초 배포

```bash
cp .hermes/.env.example .hermes/.env
# OPENAI_API_KEY=, MOCK_POS_API_KEY= 채우기
for name in coordinator order-payment-agent inventory-agent reservation-agent customer-service-agent sales-analytics-agent marketing-crm-agent; do
  grep -E "^(OPENAI_API_KEY|MOCK_POS_BASE_URL|MOCK_POS_API_KEY)=" .hermes/.env > ".hermes/profiles/$name/.env"
done
docker compose build
docker compose up -d
```

## 2. 정상 동작 확인

```bash
docker compose ps                         # hermes, dashboard, mock-pos 컨테이너가 Up 상태인지
docker compose exec hermes hermes doctor  # "Profiles" 섹션에 7개 모두 떠야 정상
curl http://localhost:8080/health         # Mock POS 헬스체크
```

## 3. 프로필별 대화 진입점

프로필 이름은 7개 중 하나: `coordinator` / `order-payment-agent` / `inventory-agent` /
`reservation-agent` / `customer-service-agent` / `sales-analytics-agent` /
`marketing-crm-agent`

```bash
# 한 번 질문하고 답만 받기 (스크립트/자동화, 로그 남기기 좋음)
docker compose exec hermes hermes chat --profile sales-analytics-agent -q "오늘 매출 어때?"

# 대화형 세션 (자신의 실제 터미널에서 -it 필요)
docker compose exec -it hermes hermes chat --profile coordinator
```

일반적인 사용은 `coordinator`로 시작합니다:

```bash
docker compose exec -it hermes hermes chat --profile coordinator
> "아메리카노 2잔, 크루아상 1개 주문 들어왔어. 결제까지 처리해줘."
```

## 4. `-p` 없이 실행하면?

`-p`/`--profile`을 지정하지 않으면 top-level `.hermes/config.yaml`의 기본 모델로 프로필
없이 동작합니다 — 이 경우 7개 역할의 SOUL.md/USER.md/MEMORY.md/skills가 전혀 로드되지
않으므로, 반드시 `--profile <role>`을 명시해야 합니다.

## 5. 흔한 함정

**함정 1 — top-level `.env`만 채우고 프로필별 `.env`를 빠뜨림**
목적: `OPENAI_API_KEY`를 한 번만 설정하면 될 것 같지만, 프로필은 격리된 홈 디렉터리를
쓴다.
실행 방법: `.hermes/.env`만 채우고 `docker compose exec hermes hermes chat --profile
order-payment-agent -q "..."` 실행.
결과: 인증 오류로 실패하거나, `MOCK_POS_BASE_URL`이 없어 POS 호출이 실패할 수 있다.
조치: 1절의 `for name in ...` 루프로 7개 프로필 모두에 키를 복사한다.

**함정 2 — `delegate_task`로 위임을 시도**
목적: `coordinator`가 하위 프로필에 작업을 넘기려 함.
실행 방법: `delegate_task` 툴 사용.
결과: 대상 프로필의 SOUL/USER/MEMORY/skills가 로드되지 않은 채 범용 서브에이전트가
응답한다(`TriAgent_Planner`/`TriAgent_MICE`에서 실측 확인된 버그).
조치: `terminal(command='/opt/hermes/bin/hermes -p <role> chat -q "..."')` 동기 호출로
대체한다([02-architecture.md](02-architecture.md)).

**함정 3 — `code_execution`에서 `mock-pos`로 호출이 안 됨**
목적: `order-payment-agent` 등이 Mock POS REST API를 호출하려 함.
실행 방법: `code_execution` 샌드박스에서 `requests.get(MOCK_POS_BASE_URL + ...)` 실행.
결과: (아직 실측 전) 샌드박스가 외부 컨테이너로 네트워크 접근을 허용하지 않으면 연결
실패.
조치: [07-roadmap.md](07-roadmap.md) 1번 참고 — `terminal`로 `curl` 호출 또는 MCP 서버
전환을 검토한다.

**함정 4 — `marketing-crm-agent`가 승인 없이 발송을 시도하는지 안 시켜봄**
목적: HITL 게이트가 실제로 걸리는지 확인.
실행 방법: `docs/10-usecase-tests.md`의 승인 게이트 테스트 프롬프트로 직접 검증.
결과: (아직 실측 전)
조치: 배포 후 반드시 "승인 없이 지금 보내줘" 류의 프롬프트로 게이트가 걸리는지 확인한다.

## 6. 관리 명령어 요약

| 목적 | 명령어 |
|---|---|
| 컨테이너 기동 | `docker compose up -d` |
| 상태 확인 | `docker compose ps` |
| 헬스체크 | `docker compose exec hermes hermes doctor` |
| 재빌드(이미지 갱신 시) | `docker compose build` |
| 중지 | `docker compose down` |
| 로그 확인 | `docker compose logs -f hermes` |
| Mock POS 단독 테스트 | `cd mock-pos && pytest` (Docker 불필요, [mock-pos/README.md](../mock-pos/README.md)) |

## 7. 트러블슈팅 빠른 참고

| 증상 | 원인 | 해결 |
|---|---|---|
| `hermes doctor`에서 프로필이 7개 미만으로 표시 | `.hermes/profiles/` 마운트 경로 오류 또는 프로필 디렉터리 누락 | `docker-compose.yml`의 `./.hermes:/opt/data` bind mount 경로 확인 |
| 챗 응답이 역할과 무관하게 일반적 | `--profile` 플래그 누락 | 4절 참고, 반드시 `--profile <role>` 지정 |
| 인증 오류 | 프로필별 `.env`에 `OPENAI_API_KEY` 없음 | 함정 1 참고 |
| POS 관련 요청이 전부 실패 | `MOCK_POS_BASE_URL`/`MOCK_POS_API_KEY` 누락 또는 `code_execution` 네트워크 제한 | 함정 1·3 참고 |
| 위임한 하위 프로필이 응답하지 않음 | `delegate_task` 사용 | 함정 2 참고 |
| 포트 충돌로 컨테이너 기동 실패 | 다른 형제 프로젝트와 포트 겹침 | [08-docker-deployment.md](08-docker-deployment.md) 점유 현황 재확인, `docker ps`로 실측 |
