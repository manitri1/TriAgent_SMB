---
name: faq-and-complaint
description: "매장 FAQ를 조회해 응대하고, 답을 찾지 못하면 웹 검색으로 보완하며 불만을 기록한다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, customer-service, faq]
platforms: [Linux, macOS, Windows]
---

## 사용 시점
고객 문의(영업시간, 메뉴, 정책 등) 응대 또는 불만 접수가 필요할 때.

## 절차
1. `file` 툴셋으로 `workspace/customer-service/faq.md`를 조회한다.
2. FAQ에 없으면 `web`/`search`로 일반 정보를 보완하되, 매장 고유 정책은 추측하지 않고
   담당자 확인이 필요하다고 안내한다.
3. 불만이 접수되면 `workspace/customer-service/complaints.md`에 날짜와 함께 기록하고,
   심각도가 높다고 판단되면 coordinator에게 보고한다.

## 반환값
- 응대 답변
- (해당 시) 불만 티켓 기록 여부
