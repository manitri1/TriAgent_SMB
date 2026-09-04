"""브라우저 conversation_id ↔ hermes session_id 매핑.

Phase 0 실측(2026-09-04, curried-percolating-ocean.md)에서 hermes CLI의
`--resume <session_id>`가 대화 연속성을 완벽히 처리함을 확인했다 — 그래서 이
저장소는 메시지 이력을 통째로 들고 재전송하지 않고, 최근 hermes session_id만
기억했다가 다음 호출에 `--resume`으로 넘긴다. 인메모리·TTL 방식이며(데모 규모,
재시작 시 초기화되어도 문제없음 — 다음 메시지가 새 세션으로 시작될 뿐), 여러
워커 프로세스 간 공유는 하지 않는다.
"""
import time
from dataclasses import dataclass
from threading import Lock

_TTL_SECONDS = 2 * 60 * 60  # 2시간 — 매장 하루 영업 시간 내 재방문을 커버


@dataclass
class _Entry:
    session_id: str
    updated_at: float


class ConversationStore:
    def __init__(self, ttl_seconds: int = _TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._entries: dict[str, _Entry] = {}
        self._lock = Lock()

    def get_session_id(self, conversation_id: str) -> str | None:
        with self._lock:
            entry = self._entries.get(conversation_id)
            if entry is None:
                return None
            if time.time() - entry.updated_at > self._ttl:
                del self._entries[conversation_id]
                return None
            return entry.session_id

    def set_session_id(self, conversation_id: str, session_id: str) -> None:
        with self._lock:
            self._entries[conversation_id] = _Entry(session_id=session_id, updated_at=time.time())


conversation_store = ConversationStore()
