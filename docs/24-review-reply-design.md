# 24. 리뷰 자동 응답 기능 설계 (신규)

> **상태**: 설계 완료, 코드/스킬 스캐폴드 작성 완료(2026-09-11). **아직 실제 챗으로
> 검증하지 않았다** — `hermes -p customer-service-agent chat -q "..."`로 실행해보고
> `workspace/customer-service/reviews.md`에 실제로 기록되는지 확인하는 절차가
> 남아있다.

## 1. 배경

이 기능은 로드맵에 원래 없던 항목이다. [마니카페_데모영상_스토리라인_검토.md](../course/마니카페_데모영상_스토리라인_검토.md)에서
검토한 홍보 영상 스토리라인이 "리뷰 답글 초안 작성"을 요구했는데, `refs/idea.md`/
`docs/` 전체를 확인한 결과 이 기능은 어디에도 설계되어 있지 않았다
([TriAgent_SMB_확장기능_검토.md](../course/TriAgent_SMB_확장기능_검토.md) §3 참고).
영상에 없는 기능을 있는 것처럼 넣을 수는 없으므로, 이번에 실제로 설계·구현했다.

## 2. 핵심 원칙

1. **리뷰 수집은 수동이다.** 네이버/구글 리뷰 API 연동은 하지 않는다(계약·인증
   필요, 로드맵 §5 실 POS 연동과 비슷한 성격의 외부 의존). 사장님/직원이 리뷰
   원문을 그대로 복사해 채팅에 붙여넣는 것을 전제로 한다.
2. **초안만 생성하고, 게시는 사람이 한다.** `marketing-crm-agent`의 홍보 문구 승인
   원칙([06-hitl-approval-design.md](06-hitl-approval-design.md))과 동일한 이유다 —
   이 시스템은 외부 플랫폼에 직접 글을 올리는 API를 갖고 있지 않고, 설령 있더라도
   브랜드 톤이 걸린 대외 커뮤니케이션은 사람이 마지막으로 확인하는 것이 원칙이다.
3. **금전이 걸린 약속을 하지 않는다.** 부정 리뷰에 환불·쿠폰 등 구체적 보상을
   답글에서 먼저 제안하지 않는다 — 그건 `order-payment-agent`/coordinator의
   HITL 게이트 영역이다.
4. **담당 에이전트는 `customer-service-agent`.** 이미 고객 응대를 전담하고 있어
   자연스럽게 확장된다 — 새 프로필을 만들지 않는다.

## 3. 구현

- 신규 스킬: `.hermes/profiles/customer-service-agent/skills/support/review_reply_draft/SKILL.md`
  (기존 `faq_and_complaint`와 같은 위치·형식)
- 신규 데이터 파일: `.hermes/workspace/customer-service/reviews.md` (원문·초안·게시
  상태를 기록하는 로그 — `complaints.md`와 동일한 패턴)
- `SOUL.md` 갱신: 리뷰 답글 원칙을 4번 항목으로 추가
- `docs/05-skills-and-tools.md`: 스킬 문서 항목 추가

## 4. 왜 HITL 게이트가 아닌가

프로모션 집행(게이트 1)과 달리 리뷰 답글은 게이트로 두지 않았다:
- 광고비 지출이 없다(금전 리스크 없음).
- 게시 자체를 애초에 사람이 수행한다(자동 게시 API가 없으므로 구조적으로 이미
  사람이 최종 관문).
- 따라서 별도 승인 절차를 추가하는 것은 불필요한 마찰이다 — "초안까지만 만들고
  게시는 사람이 한다"는 구조 자체가 이미 승인 역할을 한다.

## 5. 아직 하지 않은 것 / 향후 확장

| 항목 | 상태 |
|---|---|
| 실제 챗 검증 (`hermes -p customer-service-agent chat`으로 리뷰 원문 입력 → 초안 생성 → `reviews.md` 기록 확인) | ⬜ 미실시 |
| webapp 화면 노출 (현재는 CLI/Discord/Hermes 대시보드 챗으로만 요청 가능) | ⬜ 6번째 화면 후보로 보류 — 우선 채팅 기반으로 검증한 뒤 화면 필요성 재평가 |
| 네이버/구글 리뷰 API 연동으로 원문 자동 수집 | ⬜ 외부 계약 필요, 로드맵 후순위([TriAgent_SMB_확장기능_검토.md](../course/TriAgent_SMB_확장기능_검토.md) §2) |
| 부정 리뷰의 coordinator 보고 임계치(심각도 기준) | ⬜ 현재는 `faq_and_complaint`와 동일한 정성적 기준("심각도가 높다고 판단되면") — 정량 기준 필요 시 향후 정의 |

## 6. 검증 방법 (다음 단계)

1. `docker exec hermes-triagent-smb hermes -p customer-service-agent chat -q "이 리뷰에 답글 써줘: 라떼가 진짜 맛있어요! 사장님도 친절하시고 자주 올 것 같아요."`
2. 응답에 답글 초안이 포함되는지 확인.
3. `.hermes/workspace/customer-service/reviews.md`를 열어 원문·초안이 실제로
   기록됐는지 확인(Active Verification 원칙 — 텍스트 응답만으로 완료로 간주하지
   않는다).
4. 부정 리뷰로도 1회 반복해 `complaints.md` 동시 기록 여부까지 확인.
