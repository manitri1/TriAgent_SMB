title: 마니카페 대시보드 데모 데이터 확인 및 재시딩
assignee: coordinator
status: done
created: 2026-09-08
details:
  - 요청: "마니카페 대시보드에 데이터가 안 보여, 확인하고 필요하면 데모 데이터 다시 채워줘"
  - 작업 요약:
    1. mock-pos 카탈로그 조회: GET /v1/stores/store_demo/catalog/items (X-API-Key: dev-key)
    2. 결과가 빈 배열([])이라서 데모 시딩 스크립트 실행
    3. 시딩 완료 후 카탈로그 재조회하여 항목 수을 확인(기대 12개)
verification:
  - initial_check: "curl -s -H \"X-API-Key: dev-key\" http://mock-pos:8080/v1/stores/store_demo/catalog/items" -> []
  - seed_script_output_summary: "카탈로그 등록 12종, 고객 6명, 주문/결제 20건 생성, 환불 데모 2건 등 (스크립트 출력 확인)"
  - final_check: "curl -s -H \"X-API-Key: dev-key\" http://mock-pos:8080/v1/stores/store_demo/catalog/items | python3 -c 'import sys,json;print(len(json.load(sys.stdin)))'" -> 12
  - verification_file: /opt/data/workspace/kanban/2026-09-08-seed-manicafe-demo-data.md
  - expected_items_count: 12
notes:
  - 행동: 데모 데이터가 비어 있어 시딩을 실행했고, 카탈로그에서 12개 항목이 확인되어 작업을 완료 처리했습니다.
  - 참고: 시딩 스크립트 로그 일부는 터미널 출력에 남아 있습니다(주문 ID, 환불 ID 등). 만약 대시보드가 여전히 데이터가 보이지 않으면 브라우저 캐시/프론트엔드 재시작 또는 대시보드가 참조하는 백엔드 URL이 mock-pos가 아닌 다른 엔드포인트인지 확인해야 합니다.
