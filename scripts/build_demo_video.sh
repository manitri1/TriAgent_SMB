#!/usr/bin/env bash
# 4개의 10초 화면 녹화 클립을 2x2 그리드로 동시 합성해 16:9, 10초짜리
# demo_10s_grid.mp4 하나를 만든다. (순차 이어붙이기가 아니라 동시 재생 합성)
#
# 사용법:
#   ./scripts/build_demo_video.sh <chat.mp4> <order.mp4> <inventory.mp4> <dashboard.mp4>
#
# 배치는 좌상단=$1, 우상단=$2, 좌하단=$3, 우하단=$4 순서.
# 로컬에 ffmpeg가 설치되어 있어야 한다(이 저장소/Claude Code 세션에는 없음).
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "사용법: $0 <chat.mp4> <order.mp4> <inventory.mp4> <dashboard.mp4>" >&2
  exit 1
fi

CELL1="$1"   # 좌상단 — 고객 채팅
CELL2="$2"   # 우상단 — 주문 접수
CELL3="$3"   # 좌하단 — 재고 파악 및 주문
CELL4="$4"   # 우하단 — 실시간 매장 대시보드
OUT="${OUT:-demo_10s_grid.mp4}"
DURATION="${DURATION:-10}"
CELL_W=960
CELL_H=540
FONT="${DRAWTEXT_FONT:-}"   # 비워두면 ffmpeg 기본 폰트 사용, 필요 시 폰트 경로 지정

label() {
  # drawtext는 콜론/작은따옴표를 이스케이프해야 하므로 라벨은 영문/숫자만 권장
  local text="$1"
  local fontopt=""
  if [ -n "$FONT" ]; then
    fontopt="fontfile='$FONT':"
  fi
  echo "drawtext=${fontopt}text='${text}':fontcolor=white:fontsize=28:box=1:boxcolor=black@0.5:boxborderw=6:x=16:y=16"
}

ffmpeg -y \
  -t "$DURATION" -i "$CELL1" \
  -t "$DURATION" -i "$CELL2" \
  -t "$DURATION" -i "$CELL3" \
  -t "$DURATION" -i "$CELL4" \
  -filter_complex "
    [0:v]scale=${CELL_W}:${CELL_H},setsar=1,$(label '1 Customer Chat')[c1];
    [1:v]scale=${CELL_W}:${CELL_H},setsar=1,$(label '2 Order Intake')[c2];
    [2:v]scale=${CELL_W}:${CELL_H},setsar=1,$(label '3 Inventory Check')[c3];
    [3:v]scale=${CELL_W}:${CELL_H},setsar=1,$(label '4 Live Dashboard')[c4];
    [c1][c2]hstack=inputs=2[top];
    [c3][c4]hstack=inputs=2[bottom];
    [top][bottom]vstack=inputs=2[gridv]
  " \
  -map "[gridv]" -map 0:a? \
  -t "$DURATION" -c:v libx264 -pix_fmt yuv420p -c:a aac \
  "$OUT"

echo "완료: $OUT (16:9, ${DURATION}초, 2x2 동시 재생 그리드)"
echo "확인: ffprobe -v error -show_entries format=duration -of csv=p=0 \"$OUT\""
