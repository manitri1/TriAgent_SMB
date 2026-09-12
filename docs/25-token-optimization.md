# 25. 토큰 사용량 점검 및 최적화 (2026-09-11)

> 이 작업은 전부 `hermes prompt-size`/`hermes tools`/`hermes skills` 명령으로 진행했으며
> **OpenAI API를 한 번도 호출하지 않았다**(`prompt-size`는 공식적으로 "runs offline (no
> API call)"). 크레딧 소진 중에도 안전하게 진행 가능했던 이유다.

## 1. 문제 발견 경위

OpenAI API 크레딧 소진([docs/14-webapp-users-guide.md](14-webapp-users-guide.md) 트러블슈팅
표 참고) 이후, 재발 방지 차원에서 "이 앱이 턴마다 실제로 얼마나 많은 토큰을 고정
비용으로 쓰고 있는가"를 점검했다. `hermes prompt-size --profile <role>`(신규 세션의
고정 프롬프트 예산을 API 호출 없이 계산)로 7개 프로필을 전수 조사한 결과, **설계
문서([03-hermes-agent-integration.md](03-hermes-agent-integration.md) "프로필별 필요
툴셋" 표)와 실제 배포 설정이 크게 어긋나 있었다**:

- 설계는 프로필당 툴셋 2~4개만 켜도록 정의했는데, 실제로는 **7개 프로필 전부 20개
  안팎의 툴셋이 거의 동일하게 켜져 있었다**(이미지 생성, 음성 합성, 브라우저 자동화,
  컴퓨터 제어 등 이 프로젝트에 전혀 쓰이지 않는 기능 포함).
- 5개 프로필(coordinator/order-payment-agent/inventory-agent/reservation-agent/
  customer-service-agent)에 **카페 운영과 무관한 범용 번들 스킬 50개 이상**(영상 편집,
  PDF, 코딩 도구, 소셜미디어 등)이 인덱싱되어 있었다. 반면 sales-analytics-agent/
  marketing-crm-agent는 처음부터 프로젝트 전용 스킬 1개씩만 가진 "가벼운" 상태였다 —
  두 그룹 간 설정 방식이 애초에 달랐다는 뜻이다.
- **`delegation`(Task Delegation) 툴셋이 7개 프로필 전부에 켜져 있었다** — 이는
  단순 비용 문제가 아니라 **설계 위반**이다. coordinator는 하위 프로필 위임에
  `terminal`만 쓰고 `delegate_task`는 의도적으로 켜지 않기로 되어 있고([02-architecture.md](02-architecture.md)),
  다른 6개 프로필이 `delegation`을 가지면 [webapp_bff/routers/agent.py](../webapp/webapp_bff/routers/agent.py)
  주석이 지적한 것과 같은 클래스의 문제(승인 요청 수단이 없는 프로필이 스스로
  위임/실행해 HITL을 조용히 무력화)가 생길 수 있다.

## 2. 조치

### 2.1 불필요한 번들 스킬 제거 (5개 프로필)

```bash
hermes -p <role> skills opt-out --remove --yes
```

`coordinator`, `order-payment-agent`, `inventory-agent`, `reservation-agent`,
`customer-service-agent`에 실행. 이 프로젝트가 직접 작성한 스킬(`orchestration/
task_dispatch_and_verification`, `pos/order_and_payment`, `pos/stock_and_reorder`,
`pos/reservation_management`, `support/faq_and_complaint`, `support/review_reply_draft`)은
"local skill"이라 제거 대상에서 자동 제외됐다(명령어 자체의 보장 — `--remove`는
"unmodified bundled skills"만 지운다). `.no-bundled-skills` 마커가 생겨 앞으로
`hermes update`/재동기화 시에도 다시 설치되지 않는다.

### 2.2 프로필별 불필요 툴셋 비활성화 (7개 프로필)

`docs/03-hermes-agent-integration.md`의 "프로필별 필요 툴셋" 표를 실제로 강제 적용했다.

| 대상 | 비활성화한 툴셋 | 근거 |
|---|---|---|
| 전체 7개 프로필 | `browser`, `vision`, `image_gen`, `tts`, `computer_use`, `todo`, `session_search` | 이미지/영상/음성/GUI 자동화 — 이 프로젝트 어디에도 해당 작업 없음 |
| 전체 7개 프로필 | `delegation` | 설계 위반 교정 — coordinator만 `terminal`로 위임, 나머지는 위임 수단 자체를 갖지 않아야 HITL이 유지됨 |
| coordinator, order-payment-agent, inventory-agent, reservation-agent, sales-analytics-agent | `web` | docs/03: `web`/`search`는 customer-service-agent/marketing-crm-agent만 필요 |
| coordinator | `code_execution` | docs/03: coordinator는 `terminal`로 위임하지 mock-pos를 직접 호출하지 않음 |
| coordinator 제외 6개 프로필 | `clarify` | docs/03: HITL 승인 대화는 coordinator만 담당. 다른 프로필이 `clarify`를 가지면 사용자에게 직접 승인을 구해 coordinator의 승인 게이트를 우회할 위험(delegation과 동일한 클래스의 문제) |

`cronjob`은 의도적으로 유지했다 — [TriAgent_SMB_확장기능_검토.md](../course/TriAgent_SMB_확장기능_검토.md)에서
다음 순위로 잡은 "예약 자동 리마인더 cron 검증" 작업에 필요하다.

## 3. 결과 (신규 세션 첫 턴 기준, `hermes prompt-size`로 실측)

| 프로필 | 이전 (system+tools) | 이후 | 절감률 |
|---|---|---|---|
| coordinator | 58,850 B | 38,713 B | **34.2%** |
| order-payment-agent | 53,431 B | 34,146 B | **36.1%** |
| inventory-agent | 52,949 B | 33,668 B | **36.4%** |
| reservation-agent | 53,087 B | 33,804 B | **36.3%** |
| customer-service-agent | 53,337 B | 36,509 B | **31.5%** |
| sales-analytics-agent | 47,179 B | 33,354 B | **29.3%** |
| marketing-crm-agent | 47,549 B | 36,186 B | **23.9%** |
| **합계(7개 프로필)** | **366,382 B** | **246,380 B** | **32.8%** |

턴마다(특히 coordinator → 하위 에이전트 위임처럼 여러 프로필이 연쇄 호출되는 요청)
고정 오버헤드가 약 1/3 줄어든다. 실제 대화 내용(사용자 메시지, 도구 호출 결과)에
드는 토큰은 이번 작업으로 줄지 않으므로, 체감 절감폭은 "짧은 대화일수록 크고, 긴
대화일수록 상대적으로 작다."

## 4. 확인 방법 (재발 방지)

새 프로필을 추가하거나 툴셋 설정을 바꿀 때마다 아래로 회귀 여부를 확인한다(무료,
오프라인):

```bash
docker exec hermes-triagent-smb hermes -p <role> prompt-size
docker exec hermes-triagent-smb hermes -p <role> tools list
```

`hermes doctor`의 ✓ 표시는 "설정이 존재한다"만 확인하지 "실제로 필요한 만큼만
켜져 있다"는 보장하지 않는다는 점에 유의 — 이번 점검의 핵심 교훈이다.

## 5. 아직 하지 않은 것

- `memory` 툴셋(프로필별 3.2~3.3KB)은 SOUL.md에 명시적 사용 근거가 없어 후보이긴
  하지만, Hermes 내장 메모리 시스템과의 관계가 불확실해 이번에는 건드리지 않았다.
- `skills` 툴셋(3.4KB, 스킬 검색/설치용 런타임 도구)도 `review-reply-draft`/
  `faq_and_complaint` 같은 이미 설치된 스킬의 사용 경로와 겹칠 위험이 있어 보수적으로
  유지했다.
- 실제 API 호출 기준(대화 토큰 포함) 절감 효과는 크레딧 충전 후 실측 필요 —
  `hermes doctor`/`prompt-size`는 오프라인 추정치다.
