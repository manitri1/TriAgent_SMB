# 소상공인 AX 에이전트 시스템 (Hermes 기반)

## 1. 개요

Nous Research의 Hermes 에이전트를 기반으로, 소상공인(카페·식당·미용실·편의점)의 AX(AI Transformation)를 실현하는 멀티 에이전트 시스템을 구축한다.

- 최종 목표: 사장님/직원이 Discord를 통해 자연어로 매장 운영 업무(주문, 재고, 예약, 고객응대, 매출 분석, 마케팅 등)를 처리
- 검증 방식: 실제 POS 연동 전, Mock POS 시뮬레이터로 에이전트 Skill을 기능 테스트한 뒤 실제 POS 연동으로 전환

## 2. 시스템 아키텍처

### 2.1 Hermes Agent Core (Docker)

Hermes 에이전트 권장 구조인 **Soul / Skill / Memory** 3계층을 최대한 활용한다.

| 계층 | 역할 |
|---|---|
| **Soul** | 에이전트의 정체성과 시스템 프롬프트. 업종/역할별 페르소나, 톤, 응대 원칙 정의 |
| **Skill** | 에이전트가 호출하는 도구(tool-calling) 계층. POS 주문/재고 조회, 예약 생성, 정산 리포트 등 외부 액션을 함수로 노출 |
| **Memory** | 단기(세션 대화 컨텍스트) + 장기(매장 지식베이스, 고객 이력, 정책/FAQ) 메모리 |

### 2.2 LLM 백엔드

- OpenAI API `gpt-5-mini`를 OpenAI 호환 provider로 Hermes 프레임워크에 연결
- Hermes 자체 파인튜닝 모델 대신, 프레임워크(Soul/Skill/Memory 구조와 에이전트 런타임)만 채용하고 추론은 gpt-5-mini로 수행

### 2.3 인터페이스

- **Discord Bot**: 사장님/직원이 채널 또는 DM으로 에이전트와 상호작용
- Orchestrator Agent가 Discord 메시지를 받아 적절한 sub-agent로 라우팅

### 2.4 배포

- Docker Compose로 구성
  - Hermes Agent 컨테이너 (Soul/Skill/Memory 런타임 + Discord 커넥터)
  - (추후) Mock POS 컨테이너
  - 메모리/세션 저장소 컨테이너

```
Discord ── Orchestrator Agent (Hermes Core)
              ├─ 주문/결제 에이전트
              ├─ 재고관리 에이전트
              ├─ 예약/스케줄 에이전트
              ├─ 고객응대(CS) 에이전트
              ├─ 매출/정산 분석 에이전트
              ├─ 마케팅/CRM 에이전트
              └─ 사장님 비서(운영) 에이전트
                     │
                 Skill 계층
                     │
              Mock POS / 실POS API
```

## 3. 공통 에이전트 도출 (1차 범위)

업종별 특화보다 **4개 업종(카페·식당·미용실·편의점) 공통 에이전트**를 먼저 설계한다.

### Orchestrator / Router Agent
- Discord 요청을 의도에 따라 적절한 sub-agent로 라우팅
- 세션/대화 흐름 관리, 필요 시 여러 에이전트 결과를 취합해 응답

### 주문/결제 에이전트
- POS 주문 생성/조회, 결제 상태 확인
- Soul: 정확성·확인 절차 중시 톤
- Skill: `create_order`, `get_order_status`, `check_payment` 등
- Memory: 메뉴/가격표, 최근 주문 이력

### 재고관리 에이전트
- 재고 조회, 발주 알림, 임계치 경고
- Skill: `get_stock_level`, `request_reorder`
- Memory: 품목별 임계치, 발주처 정보

### 예약/스케줄 에이전트
- 예약 생성/변경/취소, 노쇼 리마인더 (특히 미용실·식당)
- Skill: `create_reservation`, `cancel_reservation`, `send_reminder`
- Memory: 예약 캘린더, 고객별 예약 이력

### 고객응대(CS) 에이전트
- FAQ 응대, 영업시간/메뉴 안내, 불만 접수
- Skill: `lookup_faq`, `log_complaint`
- Memory: 매장 정책/FAQ 지식베이스

### 매출/정산 분석 에이전트
- 일간/주간 매출 요약, 정산 리포트
- Skill: `get_sales_summary`, `get_settlement_report`
- Memory: 과거 매출 트렌드(요약 형태)

### 마케팅/CRM 에이전트
- 프로모션 안내, 단골 고객 관리, 리마인더 메시지 초안 작성
- Skill: `draft_promo_message`, `get_customer_segment`
- Memory: 고객 세그먼트, 과거 프로모션 이력

### 사장님 비서(운영) 에이전트
- 일정, 업무 체크리스트, 여러 에이전트의 알림 취합
- Orchestrator와 밀접하게 연동해 하루 운영 브리핑 제공

## 4. 업종별 특화 확장 (2차 이후 로드맵)

공통 에이전트 위에 업종별 Skill/Memory를 추가하는 방식으로 확장한다.

- **카페/식당**: 메뉴 추천, 웨이팅 관리, 식자재 유통기한 관리
- **미용실**: 고객 스타일 이력 관리, 노쇼 방지 리마인더, 디자이너별 스케줄 조율
- **편의점**: 자동 발주, 유통기한/폐기 관리, 시즌 상품 추천

## 5. POS 연동 로드맵

### 5.1 표준 API 조사 결과

Mock POS를 임의로 설계하기보다 신뢰할 수 있는 기준에 맞춰 스키마를 잡기 위해 조사했다. "공식 표준"과 "사실상 표준"을 구분해서 봐야 한다.

| 구분 | 후보 | 특징 |
|---|---|---|
| 공식 표준 | NRF ARTS / UnifiedPOS(UPOS, OPOS) / POSLog | NRF 산하 ARTS가 제정한 유일한 벤더 중립 표준. UPOS/OPOS는 프린터·서랍·스캐너 등 *하드웨어 주변기기* 인터페이스, POSLog는 거래 로그 XML 스키마. 2000년대 제정된 XML/하드웨어 중심이라 최신 REST 에이전트 Skill 설계엔 무겁고 실전 채택 사례도 적음 |
| 사실상 표준 (de facto) | **Square API** (Orders/Payments/Inventory/Catalog/Customers) | 가장 널리 참조되는 REST/JSON 설계. 무료 Sandbox로 주문 생성→재고 반영→결제 확인까지 실제 돈 이동 없이 end-to-end 시뮬레이션 가능. 문서화 수준이 가장 높음 |
| 사실상 표준 (보조) | Clover API / Loyverse API | Clover는 Square와 유사한 REST 구조(리테일+레스토랑 겸용). Loyverse는 카페·소규모 매장 타깃이라 우리 타깃 업종과 가장 가까움. Toast API는 레스토랑 전용이나 파트너 승인이 필요해 참조 모델로는 부적합 |
| 오픈소스 (직접 구동 가능) | Odoo POS (Community, LGPL) | Docker로 자체 호스팅 가능한 오픈소스 ERP의 POS+Inventory 모듈. Mock을 직접 코딩하는 대신 실제 Odoo POS를 컨테이너로 띄워 진짜 주문/재고 로직에 Skill을 연결하는 방법도 가능 (더 사실적이나 초기 셋업 비용 큼) |
| 국내 벤더 (표준 아님, Phase 3 대상) | 토스플레이스 Open API, 카카오페이 오프라인결제/VAN 연동 | 국내 소상공인 시장 특성상 실제 연동 시 우선 검토 대상. 공식 표준은 아니고 각 사업자 API이므로 어댑터 계층에서 흡수 |

**결론**: NRF ARTS/UPOS는 참고만 하고, **Square의 Orders/Payments/Inventory/Catalog API 오브젝트 구조를 Mock POS의 1차 참조 모델**로 채택한다. 타깃 업종(카페·식당 등) 특화 부분은 Loyverse API를 보조 참조로 삼는다. 더 사실적인 검증이 필요하면 Odoo POS(Community)를 Docker로 직접 구동하는 옵션도 고려한다.

### 5.2 단계별 로드맵

| Phase | 내용 |
|---|---|
| Phase 1 | Mock POS 시뮬레이터 구축 — Square Orders/Payments/Inventory/Catalog API 오브젝트 구조를 참조 모델로 REST 엔드포인트 설계 (대안: Odoo POS Community를 Docker로 구동해 실제 오픈소스 POS를 시뮬레이터로 사용) |
| Phase 2 | Docker Compose에 Mock POS 컨테이너 추가, 에이전트 Skill 계층에서 이를 호출해 기능 테스트 |
| Phase 3 | 실제 POS 벤더 어댑터 계층 설계 — 국내 실연동 우선 후보: 토스플레이스 Open API, 카카오페이/VAN 연동. 벤더별 API 차이를 추상화하는 어댑터 패턴 적용 |
| Phase 4 | 실 매장 파일럿 연동 |

## 6. 기술 스택 요약

- **에이전트 프레임워크**: Hermes Agent (Docker, Soul/Skill/Memory 구조)
- **LLM**: OpenAI `gpt-5-mini`
- **인터페이스**: Discord Bot
- **메모리 저장소**: 벡터DB + 세션 스토어 (추후 결정)
- **Mock POS**: Square API 오브젝트 구조를 참조한 경량 REST 서버 (세부 엔드포인트는 추후 설계, [5.1](#51-표준-api-조사-결과) 참고)

## 7. 향후 결정 필요 사항 (Open Questions)

- 벡터DB/메모리 저장소 선택
- Discord 서버/채널 구조 (업종별 채널 vs 매장별 서버)
- Mock POS 세부 엔드포인트/데이터 모델 설계 (Square 참조 모델 확정, 상세 스펙은 추후 작성)
- 국내 POS 벤더(토스플레이스/카카오페이 등) 실연동 우선순위
- 매장별 데이터 격리 및 인증 방식
