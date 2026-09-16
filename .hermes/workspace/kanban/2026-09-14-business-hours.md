title: 오늘 영업시간 확인
assignee: customer-service-agent
status: done
created: 2026-09-14
details:
  - 사장님 질문: "오늘 영업시간이 몇시부터야?"
  - 오늘 매장 영업 시작 시간을 확인해 간단히 보고
verification:
  - verification_file: workspace/customer-service/faq.md
  - checked_lines: 12-13
  - confirmed: 매일 08:00~22:00, 명절 당일 휴무
notes:
  - customer-service-agent 호출은 OpenAI 크레딧 부족으로 실패했으나, coordinator가 FAQ 원본 파일을 직접 조회해 Active Verification 완료
