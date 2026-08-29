# 구조

## 디렉토리 트리 (상위 2단계)

```
TriAgent_SMB/
├── .hermes/                        Hermes Agent 런타임 소스 (HERMES_HOME)
│   ├── config.yaml                 메인 Hermes Agent 설정 (기본 모델, 대시보드 인증 등)
│   ├── .env.example                OPENAI_API_KEY / MOCK_POS_* 시크릿 템플릿 (.env는 커밋하지 않음)
│   └── profiles/                   에이전트별 디렉토리 하나씩: coordinator, order-payment-agent,
│                                    inventory-agent, reservation-agent, customer-service-agent,
│                                    sales-analytics-agent, marketing-crm-agent
│       └── <role>/{config.yaml, SOUL.md, USER.md, MEMORY.md, skills/}
├── mock-pos/                       Mock POS REST 시뮬레이터 (FastAPI) — code_execution을 통해 호출됨
│   ├── mock_pos/
│   │   ├── main.py                 FastAPI 앱 진입점
│   │   ├── auth.py                 API 키 인증 의존성
│   │   ├── models.py               Pydantic 도메인 모델 (Order, InventoryItem, Reservation 등)
│   │   ├── store.py                인메모리 스토어/상태 계층
│   │   └── routers/                catalog, inventory, orders, payments, reports, reservations
│   ├── tests/test_flow.py          pytest 엔드투엔드 흐름 테스트
│   ├── requirements.txt / requirements-dev.txt
│   └── Dockerfile
├── smb-dashboard/                  SMB 사장님용 웹 대시보드 (진행 중, SPEC-DASHBOARD-001)
│   ├── backend/                    FastAPI 백엔드 — mock-pos를 프록시하고 승인 스토어를 소유
│   │   └── app/
│   │       ├── main.py             FastAPI 앱 진입점, 프런트엔드 정적 빌드 결과물 서빙
│   │       ├── auth.py             Basic 인증 의존성
│   │       ├── mock_pos_client.py  mock-pos 엔드포인트를 프록시하는 HTTP 클라이언트
│   │       ├── approvals_store.py  JSON 파일 기반 승인 레코드 스토어
│   │       ├── models.py           Pydantic 요청/응답 모델
│   │       └── routers/            orders, inventory, reservations, reports, approvals
│   ├── frontend/                   React 18 + TypeScript + Vite SPA
│   │   └── src/
│   │       ├── main.tsx / App.tsx  진입점 및 앱 셸
│   │       ├── api.ts              백엔드의 /api/* 라우트용 수작업 fetch 클라이언트
│   │       └── pages/              OrdersPage, InventoryPage, ReservationsPage,
│   │                                SalesSummaryPage, ApprovalsPage
│   ├── data/                       approvals.json용 바인드 마운트 볼륨 (재시작 후에도 유지)
│   └── Dockerfile                  멀티스테이지: 프런트엔드 정적 자산 빌드 후 FastAPI 이미지에 번들링
├── docs/                           설계 문서 (00-13): 아키텍처, HITL 설계, 배포,
│                                    사용 가이드, 유스케이스 테스트, 대시보드 MVP 설계
├── refs/                           원본 설계 아이디어 (idea.md) — 보존됨, 수정하지 않음
├── .claude/                        Claude Code / MoAI 하네스 (agents, skills, rules, hooks)
├── .moai/                          MoAI-ADK 상태: specs/, project/ (이 문서 세트), config/
├── .github/                        CI 워크플로, 브랜치 보호 템플릿, 이슈 라벨
├── .git_hooks/                     로컬 pre-commit / pre-push 훅
└── docker-compose.yml              4개 서비스 배포 토폴로지 (아래 참조)
```

## 아키텍처 패턴

상단은 에이전트 주도, 하단은 REST 기반으로 구성된 3계층 구조:

```
 사장님 (채팅)                     사장님 (브라우저)
      │                                 │
      ▼                                 ▼
┌─────────────┐                 ┌──────────────────────┐
│   hermes     │                 │   smb-dashboard :8652 │
│ coordinator  │                 │ FastAPI + React/Vite  │
│  + 6개 워커  │                 │  (정적 번들)           │
└──────┬───────┘                 └──────────┬─────┬──────┘
       │ code_execution                     │     │
       │ (승인 읽기/쓰기)                    │     │ 읽기 전용 프록시
       ▼                                     │     ▼
┌─────────────────┐   PATCH 동기화  ┌────────┴──────────┐
│ data/approvals   │◀───────────────│                    │
│    .json         │                │                    │
└─────────────────┘                 ▼                    │
       ▲                     ┌─────────────┐             │
       │ POST/GET/PATCH      │  mock-pos    │◀────────────┘
       └─────────────────────│  :8080       │
                              │ orders/inv/  │
                              │ reservations/│
                              │ payments/    │
                              │ reports      │
                              └─────────────┘
       │
       ▼ (기존, 변경 없음)
   Discord (병렬 HITL 채널)
```

- **hermes**(coordinator + 6개 워커 프로필)가 에이전트형 핵심이다. coordinator는 도메인 API를 직접 호출하지 않으며 — 동기식 `terminal` 호출을 통해 워커 프로필에 위임하고, 각 워커는 자신의 `code_execution` 스킬 스크립트를 통해 `mock-pos`를 호출한다.
- **mock-pos**는 CORS를 지원하지 않는 순수 FastAPI REST 서비스로, 서버 사이드 전용 API 표면이다. Hermes나 대시보드에 대해 아무런 지식이 없다.
- **smb-dashboard**는 가장 최근에 추가된 계층이다. 백엔드는 mock-pos의 읽기 전용 엔드포인트(orders/inventory/reservations/reports)를 프록시하여 브라우저가 mock-pos와 직접 통신하지 않도록 하며, 완전히 새로운 영속 계층(`data/approvals.json`)을 소유한다. 이 계층은 브라우저(승인/거절 버튼을 통해)와 Hermes coordinator(`code_execution`의 POST/GET/PATCH 호출을 통해) 양쪽 모두에서 읽고 쓴다. 이로써 대시보드의 승인 대기열은 기존 Discord 대화형 흐름과 나란히 동작하는 두 번째 HITL 채널이 된다 — 어느 채널이든 먼저 승인을 처리한 쪽이 우선하며, 반대편은 `PATCH /api/approvals/{id}`를 통해 맞춰진다.
- 호출 방향은 관계별로 단방향이다: 대시보드 → mock-pos(읽기 전용 프록시만), 대시보드 ↔ hermes(승인 읽기/쓰기), 브라우저 → 대시보드만(mock-pos나 hermes에는 절대 직접 접근하지 않음).

## 주요 파일 / 진입점 위치

| 구성 요소 | 진입점 | 비고 |
|---|---|---|
| Hermes 런타임 | `.hermes/config.yaml`, `.hermes/profiles/<role>/config.yaml` | `HERMES_HOME` 루트; `hermes -p coordinator chat`이 대화형 진입점 |
| Mock POS | `mock-pos/mock_pos/main.py` | `uvicorn mock_pos.main:app --port 8080`; `mock_pos/routers/`에서 라우터 마운트 |
| 대시보드 백엔드 | `smb-dashboard/backend/app/main.py` | `/api/*` 라우트와 빌드된 프런트엔드를 정적 파일로 서빙; `/health`를 제외하고 Basic 인증으로 보호 |
| 대시보드 프런트엔드 | `smb-dashboard/frontend/src/main.tsx` | (멀티스테이지 Dockerfile 내부에서 호출되는) `vite build`로 빌드되며, 결과물은 FastAPI 백엔드가 서빙 |
| 배포 토폴로지 | `docker-compose.yml` | 4개 서비스와 각각의 포트/볼륨 정의 (`tech.md` 참조) |
