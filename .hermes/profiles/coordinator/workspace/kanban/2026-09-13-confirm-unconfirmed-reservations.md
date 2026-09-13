title: 미확인 예약 확인 및 노쇼 처리
assignee: reservation-agent
status: done
created: 2026-09-13
details:
  - 대상 예약: 9월 13일 오전 01:00, 9월 12일 오후 09:00
  - 고객에게 연락을 시도해 참석 여부를 확인
  - 연락 두절 시 노쇼로 간주해 예약 취소 처리
verification:
  - verification_file: /opt/data/profiles/reservation-agent/workspace/reservations/2026-09-13-unconfirmed-reservations-check.md
  - 예약별 최종 상태(확인/노쇼/취소) 및 처리 로그 확인