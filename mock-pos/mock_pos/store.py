"""매장(store_id) 단위로 격리된 인메모리 데이터 저장소.

매장 단위 데이터 격리 원칙(docs/03-hermes-agent-integration.md)에 따라 모든 데이터는 store_id로 구분된다.
현재 Hermes 프로필 구성은 매장 1곳(STORE_ID, 기본 store_demo)만 사용한다.
프로세스 재시작 시 데이터는 초기화된다 (Mock 용도이므로 영속화하지 않음).
"""
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict


@dataclass
class StoreData:
    catalog: Dict[str, dict] = field(default_factory=dict)
    inventory: Dict[str, dict] = field(default_factory=dict)
    orders: Dict[str, dict] = field(default_factory=dict)
    payments: Dict[str, dict] = field(default_factory=dict)
    reservations: Dict[str, dict] = field(default_factory=dict)


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._stores: Dict[str, StoreData] = {}

    def get(self, store_id: str) -> StoreData:
        with self._lock:
            if store_id not in self._stores:
                self._stores[store_id] = StoreData()
            return self._stores[store_id]


store = InMemoryStore()
