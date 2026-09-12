---
name: review-reply-draft
description: "고객이 남긴 리뷰 원문을 받아 매장 톤에 맞는 답글 초안을 작성하고 기록한다. 게시는 하지 않는다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, customer-service, review]
platforms: [Linux, macOS, Windows]
---

## 사용 시점
사장님/직원이 리뷰 원문(네이버·구글 등에서 직접 복사해 붙여넣은 텍스트)을 전달하며
답글 작성을 요청할 때. 예: "이 리뷰에 답글 써줘: <리뷰 원문>"

## 전제 조건 (중요)
이 스킬은 리뷰 플랫폼과 API로 직접 연동하지 않는다. **리뷰 수집은 사람이 수동으로
붙여넣는 것을 전제**로 한다 — 네이버/구글 리뷰 API 연동은 별도 로드맵 항목이다
(`docs/24-review-reply-design.md` "향후 확장" 참고). 이 스킬에 리뷰 원문이 없는
상태로 "오늘 리뷰 답글 다 써줘" 같은 요청이 오면, 원문을 붙여넣어 달라고 되묻는다 —
리뷰를 지어내지 않는다.

## 절차
1. `workspace/customer-service/faq.md`를 참고해 매장 톤(친절하고 간결)과 사실관계
   (영업시간, 메뉴 등 리뷰에서 언급될 수 있는 정보)를 확인한다.
2. 리뷰의 별점/내용을 보고 톤을 정한다:
   - 긍정 리뷰 → 감사 인사 + 짧은 재방문 유도
   - 부정 리뷰 → 사과 + 개선 의지 표명. **구체적 보상(환불·쿠폰 등)은 언급하지 않는다**
     (금전이 걸린 결정은 이 스킬의 권한 밖 — `order-payment-agent`/coordinator 영역).
   - 불만 성격이 강한 리뷰는 `workspace/customer-service/complaints.md`에도 함께
     기록한다(기존 `faq_and_complaint` 스킬과 동일한 기준).
3. 답글 초안을 작성한다 (2~4문장, 매장명 서명 포함).
4. `workspace/customer-service/reviews.md`에 날짜·플랫폼(안내받은 경우)·원문·초안을
   기록한다.
5. **초안만 반환하고 게시는 하지 않는다.** 사장님이 초안을 그대로 복사해 해당
   플랫폼에 직접 게시해야 한다고 안내한다 — `marketing-crm-agent`의 홍보 문구 승인
   원칙과 동일하게, 이 시스템은 외부 플랫폼에 글을 직접 올리는 API 연동을 갖고
   있지 않다.

## 반환값
- 답글 초안 텍스트
- `reviews.md` 기록 여부
- (부정 리뷰인 경우) `complaints.md` 동시 기록 여부
