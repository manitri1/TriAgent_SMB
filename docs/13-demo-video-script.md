# 13. 4분할 동시 재생 10초 데모 영상 — 촬영 스크립트

이 문서는 웹 GUI의 4가지 화면(① 고객 채팅, ② 주문 접수, ③ 재고 파악 및 주문,
④ 실시간 매장 대시보드)이 실제로 동작하는 모습을 **16:9, 10초, 2×2 동시 재생 그리드**
영상 한 편으로 만들기 위한 촬영·조립 가이드입니다. `docs/12-web-gui-demo.md`에서
이미 검증한 화면(Hermes 대시보드 `/chat`, mock-pos `/dashboard`)을 그대로 사용하며,
이 저장소에는 없는 도구(docker, ffmpeg, 브라우저)가 필요하므로 **촬영·조립은 로컬
환경에서 직접 진행**합니다.

## 1. 준비

```bash
docker compose build && docker compose up -d
cd mock-pos/scripts && ./seed_demo_video.sh
```

`seed_demo_video.sh`는 카탈로그(아메리카노 재고 0으로 등록 — ③ 장면용)와 사전
주문/결제 몇 건(대시보드 매출·인기메뉴가 빈 화면이 아니게)을 만듭니다. 인메모리
저장소라 컨테이너를 재시작하면 초기화되므로 **녹화 세션마다 다시 실행**하세요.

## 2. 4개 클립 — 무엇을, 어떤 순서로 녹화할까

최종 영상은 4개 클립이 **동시에 재생**되므로(순차 컷 아님), 각 클립은 독립적으로
정확히 10초 이상 촬영한 뒤 10.0초로 잘라 씁니다. 다만 ②→④는 실제 인과관계이므로
**②③을 먼저 녹화하고 곧이어 ④를 녹화**하는 것을 권장합니다(그래야 ④ 화면에 진짜
방금 만든 주문이 보임). ①은 내용상 독립적이라 아무 때나 녹화해도 됩니다.

| 위치 | 파일명 | 화면(URL) | 대사/액션 |
|---|---|---|---|
| 좌상단 ① | `cell1_chat.mp4` | `localhost:19128/chat` (customer-service-agent) | 손님 채팅 예: "매장 영업시간이 어떻게 되나요?" → 응답 |
| 우상단 ② | `cell2_order.mp4` | 동일 `/chat` (coordinator) | "아메리카노 2잔 주문 들어왔어, 결제까지 처리해줘" → 완료 응답 |
| 좌하단 ③ | `cell3_inventory.mp4` | 동일 `/chat` (inventory-agent) | "재고 확인해줘" → 아메리카노 재고 0개(부족) 확인 → 발주 요청 응답 |
| 우하단 ④ | `cell4_dashboard.mp4` | `localhost:18080/dashboard` | ②③ 녹화 직후 새로고침 → 매출/재고 변화가 반영되는 순간 |

로그인: `admin` / `smb-dev-2026` (`docs/08-docker-deployment.md`, 로컬 데모 전용 계정 —
다른 용도로는 반드시 교체).

## 3. 녹화 설정

- 창 크기: 그리드 셀 하나가 최종 960×540이 되므로, 각 화면을 960×540 배수(예: 1920×1080
  전체화면도 가능, 조립 시 어차피 스케일됨)로 녹화
- 도구: Windows 기본 Xbox Game Bar(`Win+Alt+R`) 또는 OBS 중 편한 것
- 여유 있게(11~15초) 찍고 조립 스크립트가 정확히 10.0초로 자릅니다
- 채팅 텍스트가 960×540로 축소돼도 읽히도록 브라우저 확대(Ctrl+`+`)를 1~2단계 해두는 것을 권장

## 4. 조립

```bash
./scripts/build_demo_video.sh cell1_chat.mp4 cell2_order.mp4 cell3_inventory.mp4 cell4_dashboard.mp4
```

`demo_10s_grid.mp4`(16:9, 10.0초, 2×2 동시 재생)가 생성됩니다. 셀 배치나 자막 문구를
바꾸고 싶으면 `scripts/build_demo_video.sh`의 인자 순서/`label` 호출부만 수정해 재실행하면
되고, 재녹화는 필요 없습니다.

## 5. 검증

- `ffprobe -v error -show_entries format=duration -of csv=p=0 demo_10s_grid.mp4` → `10.0` 근처
- 재생해서 4분할이 모두 동시에 움직이는지, 자막이 잘리지 않는지 육안 확인
- 대시보드(④) 화면 값이 실제로 ②③에서 만든 주문/재고와 일치하는지 확인:
  `curl -s -H "X-API-Key: dev-key" http://localhost:18080/v1/stores/store_demo/inventory/menu_americano`
