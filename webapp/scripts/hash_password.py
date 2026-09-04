"""웹앱 자체 Basic Auth 비밀번호 해시 생성 스크립트.

.hermes/config.yaml의 dashboard.basic_auth 패턴(scrypt)을 참고하되, 이 웹앱은
Hermes의 plugins.dashboard_auth.basic 모듈에 접근할 수 없으므로 표준 라이브러리
hashlib.scrypt로 자체 구현한다 — Hermes 대시보드 계정과는 별개다.

사용법 (컨테이너 안에서):
    docker compose run --rm webapp python scripts/hash_password.py '<비밀번호>'

출력된 문자열을 WEBAPP_BASIC_AUTH_PASSWORD_HASH 환경변수(.env 또는
docker-compose.yml)에 넣는다.
"""
import base64
import hashlib
import os
import sys

N = 16384
R = 8
P = 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=N, r=R, p=P, dklen=32)
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(derived).decode("ascii")
    return f"scrypt${N}${R}${P}${salt_b64}${hash_b64}"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python scripts/hash_password.py '<비밀번호>'", file=sys.stderr)
        raise SystemExit(1)
    print(hash_password(sys.argv[1]))
