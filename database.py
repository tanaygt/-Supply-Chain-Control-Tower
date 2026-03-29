import json
import os
import sqlite3
from copy import deepcopy
from typing import Any

DB_FILE = "control_tower.db"
JSON_FILE = "data.json"
TABLES = ("inventory", "orders", "shipments", "vendors", "demand_history")

DEFAULT_DATA = {
    "inventory": [],
    "orders": [],
    "shipments": [],
    "vendors": [],
    "demand_history": {},
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def _deepcopy_default() -> dict[str, Any]:
    return deepcopy(DEFAULT_DATA)


def _normalize_data(data: dict[str, Any] | None) -> dict[str, Any]:
    merged = _deepcopy_default()
    if data:
        for key in TABLES:
            if key in data:
                merged[key] = data[key]
    if not isinstance(merged["demand_history"], dict):
        merged["demand_history"] = {}
    return merged


def _load_json_data() -> dict[str, Any]:
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            return _normalize_data(json.load(file))
    return _deepcopy_default()


def _write_json_data(data: dict[str, Any]) -> None:
    with open(JSON_FILE, "w", encoding="utf-8") as file:
        json.dump(_normalize_data(data), file, indent=2)


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_data (
                dataset TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )
            """
        )
        row = conn.execute("SELECT COUNT(*) AS count FROM app_data").fetchone()
        if row["count"] == 0:
            seed = _load_json_data()
            for dataset in TABLES:
                conn.execute(
                    "INSERT INTO app_data (dataset, payload) VALUES (?, ?)",
                    (dataset, json.dumps(seed.get(dataset, [] if dataset != "demand_history" else {}))),
                )
        conn.commit()


def load_all_data() -> dict[str, Any]:
    init_db()
    data = _deepcopy_default()
    with _connect() as conn:
        rows = conn.execute("SELECT dataset, payload FROM app_data").fetchall()
    for row in rows:
        payload = json.loads(row["payload"])
        data[row["dataset"]] = payload
    return _normalize_data(data)


def save_all_data(data: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_data(data)
    init_db()
    with _connect() as conn:
        for dataset in TABLES:
            conn.execute(
                """
                INSERT INTO app_data (dataset, payload)
                VALUES (?, ?)
                ON CONFLICT(dataset) DO UPDATE SET payload = excluded.payload
                """,
                (dataset, json.dumps(normalized.get(dataset))),
            )
        conn.commit()
    _write_json_data(normalized)
    return normalized


def reset_database() -> dict[str, Any]:
    data = _load_json_data()
    return save_all_data(data)

