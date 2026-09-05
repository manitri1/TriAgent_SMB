title: 아메리카노 재고 수량 변경 요청
assignee: inventory-agent
status: assigned
created_at: 2026-09-04
details:
  - 요청자: 사용자
  - 요청 내용: "아메리카노" 재고를 20개로 변경
  - 우선 순위: normal
acceptance_criteria:
  - POS/재고시스템에서 아메리카노의 재고가 실제로 20으로 반영되어야 함
  - 변경 전/후의 증빙(API 응답 스니펫 또는 DB 쿼리 결과)을 카드에 첨부
instructions_for_agent:
  - 확인 및 작업 순서:
    1) 아메리카노의 정확한 식별자(SKU)가 필요한지 검사. 필요하면 즉시 사용자에게 질문하고 작업 중단.
    2) 변경 전 현재 재고값을 캡처(스크린샷 또는 API 응답/쿼리 결과 스니펫).
    3) POS/재고시스템에서 재고를 20으로 업데이트.
    4) 변경 직후 재조회하여 재고가 20으로 반영된 것을 캡처.
    5) 캡처한 증빙(전/후)을 이 카드의 "verification" 섹션에 추가하고 status를 "ready-for-verification"으로 변경.
    6) 증빙을 파일로 저장했다면 절대 경로를 명시할 것.
  - 중요: 카드가 "done"으로 표시되면 제가 직접 재확인한 뒤 최종 승인함. 스스로 완료 처리하지 마세요.
notes:
  - coordinator는 직접 재고를 변경하지 않음. 본 작업은 inventory-agent가 수행해야 함.

verification: |
  (여기에 agent가 전/후 증빙을 붙여 주세요)
