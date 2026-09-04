title: 콜드브루 재입고 요청
assignee: inventory-agent
status: in_progress
created: 2026-09-04

details:
  - 품목: 콜드브루
  - 수량: 15
  - 사유: 여름철 수요 증가 대비
  - 우선순위: 높음
  - 요청자: 사장님
  - 요청작업:
    1) 현재 재고 재확인(재고 위치, 출고예정 포함)
    2) 공급사 후보 최소 2곳 조사(단가, MOQ, 납기, 연락처 포함)
    3) 권장 발주안(수량 15 기준), 예상 비용, 결제수단, 예상 납기 제시
    4) 산출물(제안서 .md 또는 .pdf) 경로를 Kanban 카드에 첨부하고 status를 in_progress->ready_for_approval로 변경
  - 주의: 실제 발주·결제는 coordinator(사장님)의 명시적 승인 없이 진행하지 마세요(재고 대량 발주 확정 전 HITL 승인 필요).

notes: "긴급성은 '여름철 수요 증가 대비'로 표시했습니다. inventory-agent가 Mock POS 및 공급사 확인 후 결과를 보고하면 제가 최종 검토(및 승인 여부 판단)를 진행하겠습니다."