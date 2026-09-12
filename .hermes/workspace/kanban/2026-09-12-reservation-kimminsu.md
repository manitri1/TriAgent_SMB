title: 예약 - 김민수 (4명) 2026-09-12 14:00
assignee: reservation-agent
status: blocked
created_by: coordinator
created_at: 2026-09-11T02:32:40Z

details:
  - customer_name: 김민수
  - party_size: 4
  - datetime: 2026-09-12 14:00
  - requested_via: user (coordinator)
  - contact_phone: (not provided)  # reservation-agent: ask coordinator if required

instructions_for_assignee:
  - Create the reservation in the reservation system for the above customer.
  - If additional details (phone number, seating preference) are required, ask the coordinator before proceeding.
  - After successful creation, update this file: set status: done, add reservation_id and confirmation_time, and add verification: reservation_lookup_command and reservation_record_snapshot.
  - If creation fails, set status: blocked and paste the error output.

verification:
  - creation_attempt: 2026-09-11T02:32:40Z
  - result: error
  - error_output: |
      {"status_code": 422, "body": {"detail": [{"type": "missing", "loc": ["body", "customer_id"], "msg": "Field required", "input": {"customer_name": "김민수", "party_size": 4, "datetime": "2026-09-12T14:00:00+09:00", "note": "Created by coordinator task. kanban:/opt/data/workspace/kanban/2026-09-12-reservation-kimminsu.md"}}]}}

notes: "Blocked: API requires customer_id. Ask coordinator for customer_id or permission to create a guest customer record."
