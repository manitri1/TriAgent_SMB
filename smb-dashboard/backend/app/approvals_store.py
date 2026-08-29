"""승인 큐 저장소 — Hermes gateway/HITL에는 구조화된 승인 저장소가 전혀 없었기 때문에
(docs/13-mvp-dashboard-design.md §1) 이 프로젝트에서 처음 만드는 신규 컴포넌트다.

mock-pos/store.py의 스레드 락 패턴을 따르되, 컨테이너 재시작에도 대기열이 유지되어야 하므로
인메모리가 아니라 JSON 파일(./smb-dashboard/data, bind mount)에 영속화한다.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Optional

from app.models import Approval

_DATA_FILE = Path(os.environ.get("APPROVALS_DATA_FILE", "/data/approvals.json"))
_lock = Lock()


def _read_all() -> dict[str, dict]:
    if not _DATA_FILE.exists():
        return {}
    with _DATA_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return {item["approval_id"]: item for item in raw}


def _write_all(records: dict[str, dict]) -> None:
    _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = _DATA_FILE.with_suffix(".tmp")
    with tmp_file.open("w", encoding="utf-8") as f:
        json.dump(list(records.values()), f, default=str, ensure_ascii=False, indent=2)
    tmp_file.replace(_DATA_FILE)


def list_approvals(status: Optional[str] = None) -> list[dict]:
    with _lock:
        records = list(_read_all().values())
    if status:
        records = [r for r in records if r["status"] == status]
    records.sort(key=lambda r: r["created_at"], reverse=True)
    return records


def get_approval(approval_id: str) -> Optional[dict]:
    with _lock:
        return _read_all().get(approval_id)


def create_approval(payload: dict) -> dict:
    record = Approval(
        approval_id=f"appr_{uuid.uuid4().hex[:12]}",
        type=payload["type"],
        summary=payload["summary"],
        details=payload["details"],
        requested_by=payload["requested_by"],
    ).model_dump(mode="json")

    with _lock:
        records = _read_all()
        records[record["approval_id"]] = record
        _write_all(records)
    return record


class AlreadyDecidedError(Exception):
    pass


class ApprovalNotFoundError(Exception):
    pass


def decide_approval(approval_id: str, status: str, reason: Optional[str], decided_by: str = "owner") -> dict:
    with _lock:
        records = _read_all()
        record = records.get(approval_id)
        if not record:
            raise ApprovalNotFoundError(approval_id)
        if record["status"] != "pending":
            raise AlreadyDecidedError(approval_id)

        record["status"] = status
        record["reason"] = reason
        record["decided_by"] = decided_by
        record["decided_at"] = datetime.now(timezone.utc).isoformat()
        records[approval_id] = record
        _write_all(records)
        return record
