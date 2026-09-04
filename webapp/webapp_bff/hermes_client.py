"""hermes CLI를 통한 에이전트 연동.

Phase 0 실측(2026-09-04, curried-percolating-ocean.md)에서 확정된 방식: Docker SDK로
이미 실행 중인 hermes 컨테이너(gateway run 데몬)에 exec하여
`hermes -p <profile> chat -Q --source tool [--resume <session_id>] -q "<메시지>"`를
실행한다. 이 저장소의 coordinator가 하위 프로필에 위임할 때 쓰는
`terminal(hermes -p <role> chat -q ...)`와 동일한 메커니즘이다(docs/02-architecture.md).

중요한 제약(실측으로 확인됨): exec 연결이 타임아웃/끊겨도 컨테이너 안의 위임
작업 자체는 계속 진행되어 완료될 수 있다 — 즉 "타임아웃"은 "작업이 멈췄다"는
뜻이 아니라 "지켜보길 포기했다"는 뜻이다. 그래서 이 클라이언트는 타임아웃을
예외로 취급하지 않고 명시적 상태(status="timeout")로 반환하며, 호출부(화면
2·3)는 반드시 mock-pos를 재조회해 실제 완료 여부를 재확인해야 한다(Active
Verification, docs/02-architecture.md).
"""
import asyncio
import re
from dataclasses import dataclass

import docker
from docker.errors import APIError, NotFound

from webapp_bff.config import settings

_HANGUL_RE = re.compile(r"[가-힣]")
# session_id 줄은 보통 출력 맨 끝에 나오지만, 실측 결과 가끔 앞쪽(스트림 버퍼링
# 순서 차이로 추정)에 나오는 경우도 있었다 — 위치를 가정하지 않고 어디서든
# 찾아서 제거한다.
_SESSION_ID_LINE_RE = re.compile(r"^session_id:\s*(\S+)\s*$\n?", re.MULTILINE)
_BOLD_HEADER_RE = re.compile(r"^\*\*.+\*\*\s*$", re.MULTILINE)
# --resume 사용 시 CLI가 앞에 붙이는 상태 줄(Phase 0 실측: "↻ Resumed session ...").
_RESUME_BANNER_RE = re.compile(r"^↻ .*$\n?", re.MULTILINE)


@dataclass
class AgentReply:
    status: str  # "ok" | "timeout" | "error"
    text: str
    session_id: str | None


def _extract_answer(raw: str) -> tuple[str, str | None]:
    """CLI 원문 출력에서 session_id와 '진짜' 최종 답변을 분리한다.

    -Q(quiet)가 모델 reasoning 블록을 항상 완전히 숨기지는 못한다(Phase 0 실측 —
    호출마다 나올 때도, 안 나올 때도 있었고, 형태도 제각각이었다: '**소제목**'
    블록으로 나올 때도, 빈 줄 구분 없이 개행 하나로 답변에 바로 이어 붙을 때도
    있었다). 최선의 근사치로 처리한다: (1) 마지막 '**소제목**' 단독 줄 이후를
    취하고, (2) 그 안에서 한글이 처음 나오는 '줄'부터를 답으로 본다(문단이 아니라
    줄 단위로 자르는 이유: reasoning 잔여물이 빈 줄 없이 바로 다음 줄의 답변과
    붙어 나온 실측 사례가 있었다). 이 프로젝트의 모든 에이전트는 한국어로
    응답하도록 설계되어 있으므로, 첫 한글 줄 이전은 영문 reasoning 잔여물로
    간주해도 안전하다. reasoning이 아예 없는 출력(관찰된 사례 다수)에는 아무
    영향이 없다.
    """
    session_match = _SESSION_ID_LINE_RE.search(raw)
    session_id = session_match.group(1) if session_match else None
    body = _SESSION_ID_LINE_RE.sub("", raw, count=1)
    body = _RESUME_BANNER_RE.sub("", body, count=1)

    bold_headers = list(_BOLD_HEADER_RE.finditer(body))
    if bold_headers:
        body = body[bold_headers[-1].end():]

    first_hangul = _HANGUL_RE.search(body)
    if first_hangul:
        line_start = body.rfind("\n", 0, first_hangul.start()) + 1
        body = body[line_start:]

    return body.strip(), session_id


class AgentClient:
    def __init__(self) -> None:
        self._docker = docker.from_env()

    def _exec_sync(self, profile: str, message: str, session_id: str | None) -> str:
        container = self._docker.containers.get(settings.hermes_container_name)
        cmd = [settings.hermes_bin_path, "-p", profile, "chat", "-Q", "--source", "tool"]
        if session_id:
            cmd += ["--resume", session_id]
        cmd += ["-q", message]
        _exit_code, output = container.exec_run(cmd=cmd, workdir="/opt/data", demux=False)
        return output.decode("utf-8", errors="replace")

    async def send(self, profile: str, message: str, session_id: str | None = None) -> AgentReply:
        loop = asyncio.get_running_loop()
        try:
            raw = await asyncio.wait_for(
                loop.run_in_executor(None, self._exec_sync, profile, message, session_id),
                timeout=settings.hermes_exec_timeout_seconds,
            )
        except asyncio.TimeoutError:
            # 작업이 실패한 게 아니라 "지켜보길 포기"한 것뿐이다 — 컨테이너 안의
            # 위임은 계속 진행 중일 수 있다(Phase 0 실측). 호출부가 읽기 패널을
            # 재조회하도록 안내한다.
            return AgentReply(
                status="timeout",
                text="아직 처리 중일 수 있습니다. 잠시 후 아래 목록을 새로고침해 확인해 주세요.",
                session_id=session_id,
            )
        except (NotFound, APIError) as exc:
            return AgentReply(status="error", text=f"에이전트 연결 오류: {exc}", session_id=session_id)

        answer, new_session_id = _extract_answer(raw)
        if not answer:
            answer = "(빈 응답을 받았습니다 — 다시 시도해 주세요.)"
        return AgentReply(status="ok", text=answer, session_id=new_session_id or session_id)


agent_client = AgentClient()
