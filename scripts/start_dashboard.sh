#!/usr/bin/env bash
# Hermes 대시보드(hermes-triagent-smb-dashboard) 컨테이너를 기동하고 상태를 확인한다.
#
# 사용법 (VPS 또는 docker-compose.yml이 있는 이 저장소 루트에서):
#   ./scripts/start_dashboard.sh
#
# 대시보드는 127.0.0.1:19128로만 노출되므로(docs/08-docker-deployment.md 참고), 이 VPS
# 밖에서 브라우저로 접속하려면 SSH 터널이 필요하다:
#   ssh -N -L 19128:127.0.0.1:19128 <사용자>@<VPS주소>
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

HOST_PORT="19128"
URL="http://127.0.0.1:${HOST_PORT}/"

echo "== dashboard 의존 서비스(hermes) 확인 =="
docker compose up -d hermes

echo "== dashboard 기동 =="
docker compose up -d dashboard

echo "== 헬스체크 (최대 30초 대기) =="
for i in $(seq 1 15); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$URL" || echo "000")
  if [ "$code" = "200" ] || [ "$code" = "302" ] || [ "$code" = "401" ]; then
    echo "정상 응답: HTTP $code"
    echo
    echo "대시보드가 떴습니다: $URL"
    echo "이 VPS 밖에서 접속하려면 SSH 터널을 사용하세요:"
    echo "  ssh -N -L ${HOST_PORT}:127.0.0.1:${HOST_PORT} <사용자>@<VPS주소>"
    echo "로그인 정보는 .hermes/config.yaml의 dashboard.basic_auth 참고."
    exit 0
  fi
  sleep 2
done

echo "경고: ${URL} 응답이 비정상입니다(마지막 코드: $code)." >&2
echo "크래시 루프 여부를 로그로 확인하세요:" >&2
echo "  docker compose logs dashboard --tail=50" >&2
exit 1
