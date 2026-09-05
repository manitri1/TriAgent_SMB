# 20. VPS 배포 기준 — 운영 노트

`docs/08~15`는 대부분 Windows 로컬 개발(Docker Desktop, `E:/work/Hermes/`)을 전제로
작성됐습니다. 이 저장소는 실제로는 **Linux VPS 1대**에 배포되어 있고, 몇몇 절차와
가정이 VPS에서는 다르게 동작하거나 아예 다른 조치가 필요합니다. 이 문서는 그 차이를
한곳에 모아 "VPS 기준"으로 무엇을 확인·조정해야 하는지 정리합니다(2026-09-05 실측).

## 1. 이 VPS의 실체

- **호스팅사**: Hostinger VPS (호스트명 `srv1923951`, `*.srv1923951.hstgr.cloud`
  와일드카드 서브도메인이 이 VPS의 공인 IP로 자동 라우팅됨 — DNS 설정 불필요)
- **OS/런타임**: Ubuntu + Docker Engine(`docker.service`, systemd `enabled`/`active`)
  — Docker Desktop 없음, GUI 없음, 전부 CLI/`docker compose`로 운영
- **디스크**: 루트 파티션 96G 중 사용 13G(2026-09-05 기준) — 이미지 여러 개를 함께
  운용해도 당장 여유 있음
- **방화벽**: `ufw`는 비활성(inactive) — 실질적인 방화벽은 VPS 제공자의 클라우드
  보안그룹/방화벽 콘솔이 담당합니다. 즉 **`docker-compose.yml`의 `ports:`에 어떤
  주소로 바인딩하는지가 이 VPS에서 사실상 유일한 접근 제어**입니다
  (`127.0.0.1:...`면 이 서버 안에서만 접근 가능, `0.0.0.0:...`면 인터넷에 그대로
  노출). 클라우드 방화벽 콘솔도 별도로 확인해 불필요한 인바운드 포트를 막아두는
  것을 권장합니다.
- **이 VPS에 이미 떠 있는 다른 프로젝트**: `/opt/adcreator`(형제 Hermes 프로젝트),
  Hostinger hPanel의 "Docker Compose Catalog" 기능으로 배포된 관리형 Hermes Agent
  인스턴스 2개(`/docker/hermes-agent-<id>/`), 그리고 아래 2번의 공유 Traefik —
  새 서비스를 배포하기 전에 항상 `docker ps -a`로 포트/컨테이너명이 겹치지 않는지
  먼저 확인하세요([08-docker-deployment.md](08-docker-deployment.md) "VPS 배포 현황
  실측" 표 참고).

## 2. 공유 Traefik 리버스 프록시 — 이 VPS의 기본 노출 경로

이 VPS에는 hPanel이 기본 제공하는 **Traefik**이 이미 별도 컨테이너(`traefik-traefik-1`)
로 떠 있고, `network_mode: host`로 `80`/`443` 포트를 직접 점유하며 Let's Encrypt
인증서를 자동 발급합니다. Docker 라벨만 붙이면 이 Traefik이 자동으로 라우팅해 주므로,
nginx를 직접 설치하거나 인증서를 손으로 관리할 필요가 없습니다.

**동작 원리**: Traefik이 Docker 소켓을 읽어(`--providers.docker=true`,
`exposedbydefault=false`) `traefik.enable=true` 라벨이 붙은 컨테이너만 골라 라우팅
규칙을 만듭니다. Traefik이 `host` 네트워크 모드라 이 서버의 모든 Docker 브리지
네트워크에 직접 도달할 수 있으므로, 대상 컨테이너의 **호스트 포트(`ports:`)를 열 필요
없이 컨테이너 내부 포트**만 라벨로 알려주면 됩니다.

**적용 예시 — Hermes 대시보드를 서브도메인으로 노출**:

```yaml
# docker-compose.yml의 dashboard 서비스에 추가
  dashboard:
    # ...기존 설정 그대로 유지 (ports: "127.0.0.1:9128:9119"도 그대로 둬도 무방 —
    # 로컬 SSH 세션에서는 계속 127.0.0.1로 접근하고, 외부에서는 아래 라벨로 접근)
    labels:
      traefik.enable: "true"
      traefik.http.routers.smb-dashboard.entrypoints: websecure
      traefik.http.routers.smb-dashboard.rule: "Host(`smb-dashboard.srv1923951.hstgr.cloud`)"
      traefik.http.routers.smb-dashboard.tls.certresolver: letsencrypt
      traefik.http.services.smb-dashboard.loadbalancer.server.port: "9119"
```

웹앱(`webapp`)도 같은 방식으로(내부 포트는 `8090`) `smb-webapp.srv1923951.hstgr.cloud`
같은 이름을 붙일 수 있습니다. 라벨 추가 후:

```bash
docker compose up -d dashboard   # 라벨만 바뀌었으므로 재생성만 필요, 재빌드 불필요
curl -I https://smb-dashboard.srv1923951.hstgr.cloud/
```

몇 초 안에 302(로그인 리다이렉트)가 TLS로 돌아오면 성공입니다. 이 방식은
[19-hermes-desktop-vps-guide.md](19-hermes-desktop-vps-guide.md)에서 다룬 "방법 B —
리버스 프록시 + TLS"를 처음부터 손으로 구성하는 대신, 이 VPS에 이미 있는 인프라를
그대로 재사용하는 버전입니다 — **VPS에서는 이 방법을 우선 검토**하세요.

> ⚠️ **여전히 `dashboard.basic_auth` 인증은 그대로 켜져 있어야 합니다.** Traefik은
> TLS 종단·라우팅만 담당할 뿐 로그인 자체를 대신 처리하지 않습니다. 공개 서브도메인을
> 붙이기 전에 [19장](19-hermes-desktop-vps-guide.md) 6번의 기본 비밀번호 교체를
> 반드시 먼저 하세요.

> 라우터 이름(`smb-dashboard` 등)은 이 VPS의 다른 Traefik 라벨(현재
> `hermes-agent-q66p`, `hermes-agent-htjj`)과 겹치지 않아야 합니다 — 겹치면 Traefik이
> 둘 중 하나만 무작위로 채택합니다. 새 라우터를 추가하기 전에
> `docker inspect <다른 컨테이너> --format '{{json .Config.Labels}}'`로 기존 이름을
> 확인하는 습관을 들이세요.

## 3. 웹앱·대시보드를 외부에 노출하기 — 세 가지 선택지 비교

| 방법 | 언제 쓰나 | 장점 | 단점 |
|---|---|---|---|
| SSH 터널 | 혼자 개발 중, 가끔만 접속 | 방화벽/DNS 설정 전혀 불필요, 가장 안전 | 터널이 끊기면 접속도 끊김, 매번 SSH 필요 |
| 수동 nginx + Let's Encrypt | Hostinger 외 VPS(공유 Traefik 없는 환경) | 어디서든 적용 가능 | 인증서 갱신·설정을 직접 관리 |
| **Traefik 라벨(이 VPS)** | 상시 접속, 여러 사람/기기 | 라벨 몇 줄로 끝, 인증서 자동 갱신 | 이 VPS(Hostinger Docker Compose Catalog 환경)에서만 바로 됨 |

세 방법 모두 [19-hermes-desktop-vps-guide.md](19-hermes-desktop-vps-guide.md)의
"기본 비밀번호 교체"가 선행돼야 안전합니다. SSH 터널 절차 자체는 15장에 이미 정리돼
있으므로 반복하지 않습니다.

## 4. 백업 시 실제로 챙겨야 할 것

이 VPS 배포는 named volume이 아니라 **bind mount**를 씁니다(`./.hermes:/opt/data`)
— 즉 컨테이너를 지워도 데이터는 VPS 디스크의 저장소 경로(`/opt/smb/.hermes/`)에
그대로 남습니다. 백업이 필요하면 Docker가 아니라 이 디렉터리를 직접 백업하면
됩니다:

```bash
tar czf smb-hermes-backup-$(date +%F).tar.gz -C /opt/smb .hermes mock-pos/data 2>/dev/null
```

`mock-pos`는 인메모리 저장소라(재시작 시 초기화) 백업 대상이 아닙니다 — 데모
데이터가 필요하면 `mock-pos/scripts/seed_manicafe_demo.sh`로 다시 채우면 됩니다
([14-webapp-users-guide.md](14-webapp-users-guide.md) 참고).

## 5. 재부팅·장애 복구

- VPS가 재부팅되면: `docker.service`가 systemd로 자동 기동 → 각 컨테이너의
  `restart: unless-stopped`에 따라 자동으로 다시 올라옵니다. **수동 개입 불필요**
  (Windows Docker Desktop처럼 사람이 로그인해서 앱을 띄워야 하는 단계가 없습니다).
- 재부팅 후에는 [08-docker-deployment.md](08-docker-deployment.md)의 "함정 5"(대시보드가
  "Up"인데 내부는 죽어있는 크래시 루프)가 재발하지 않았는지 `docker compose logs
  dashboard`로 한 번 확인하는 습관을 들이세요 — 인증 설정은 `.hermes/config.yaml`에
  파일로 저장되므로 재부팅으로 사라지지는 않지만, 이미지 업데이트나 설정 변경 이후에는
  재확인이 안전합니다.
