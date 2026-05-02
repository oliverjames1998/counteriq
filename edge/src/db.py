"""Local SQLite buffer for events that haven't synced yet.

The agent writes every detected event here first, then a background sync
thread drains them up to FastAPI. If the cloud is unreachable, events
queue locally and flush on reconnect.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

DDL = """
create table if not exists events (
  id            text primary key,
  camera_id     text not null,
  type          text not null,
  severity      text not null default 'info',
  started_at    text not null,
  ended_at      text,
  confidence    real not null default 0,
  metadata      text not null default '{}',
  synced        integer not null default 0,
  created_at    text not null default current_timestamp
);
create index if not exists idx_events_synced on events(synced, created_at);
"""


@contextmanager
def open_db(path: str | Path) -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(str(path), isolation_level=None)
    try:
        con.executescript(DDL)
        yield con
    finally:
        con.close()


def insert_event(con: sqlite3.Connection, *, event_id: str, camera_id: str,
                 event_type: str, severity: str, started_at: datetime,
                 ended_at: datetime | None, confidence: float,
                 metadata: dict[str, Any]) -> None:
    con.execute(
        "insert into events (id, camera_id, type, severity, started_at, ended_at, confidence, metadata) "
        "values (?,?,?,?,?,?,?,?)",
        (
            event_id,
            camera_id,
            event_type,
            severity,
            started_at.astimezone(timezone.utc).isoformat(),
            ended_at.astimezone(timezone.utc).isoformat() if ended_at else None,
            float(confidence),
            json.dumps(metadata),
        ),
    )


def fetch_unsynced(con: sqlite3.Connection, limit: int = 100) -> list[dict[str, Any]]:
    cur = con.execute(
        "select id, camera_id, type, severity, started_at, ended_at, confidence, metadata "
        "from events where synced = 0 order by created_at asc limit ?",
        (limit,),
    )
    rows = []
    for r in cur.fetchall():
        rows.append({
            "id": r[0], "camera_id": r[1], "type": r[2], "severity": r[3],
            "started_at": r[4], "ended_at": r[5], "confidence": r[6],
            "metadata": json.loads(r[7]),
        })
    return rows


def mark_synced(con: sqlite3.Connection, ids: list[str]) -> None:
    if not ids:
        return
    placeholders = ",".join("?" * len(ids))
    con.execute(f"update events set synced = 1 where id in ({placeholders})", ids)
