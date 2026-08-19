---
name: promo-and-segment
description: "트렌드를 조사해 홍보 문구 초안을 작성하고, 실제 집행 전 승인 절차를 안내한다"
version: 1.0.0
author: TriAgent_SMB
license: MIT
tags: [smb, marketing, crm]
platforms: [Linux, macOS, Windows]
---

## 사용 시점
프로모션/홍보 문구 작성 요청, 캠페인 아이디어 요청을 받았을 때.

## 절차
1. `web`/`search`로 트렌드·경쟁 매장 정보를 조사한다.
2. 매장 톤앤매너(`USER.md` 참고)에 맞춰 홍보 문구 초안을 작성하고, 반드시 "초안"임을
   명시한다.
3. `workspace/marketing/<날짜>.md`에 저장한다.
4. 유료 광고나 대량 발송 집행 의사가 확인되면 coordinator에게 게이트 1(프로모션 집행)
   승인이 필요함을 안내한다 — 이 프로필 자체는 발송하지 않는다.

## 반환값
- 홍보 문구 초안
- 산출물 파일 경로
- HITL 게이트 필요 여부
