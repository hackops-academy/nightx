#!/usr/bin/env python3
"""SQLite database for NightX scan history."""
import json, sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List

DB_DIR  = Path.home() / ".nightx"
DB_PATH = DB_DIR / "scans.db"

class Database:
    def __init__(self):
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH))
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'running'
        );
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (scan_id) REFERENCES scans(id)
        );
        """)
        self.conn.commit()

    def create_scan(self, target: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO scans (target, created_at) VALUES (?, ?)",
            (target, datetime.now().isoformat())
        )
        self.conn.commit()
        return cur.lastrowid

    def save_findings(self, scan_id: int, category: str, findings: List):
        self.conn.execute(
            "INSERT INTO findings (scan_id, category, data, created_at) VALUES (?, ?, ?, ?)",
            (scan_id, category, json.dumps(findings, default=str), datetime.now().isoformat())
        )
        self.conn.commit()

    def get_all_scans(self) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT s.id, s.target, s.created_at, COUNT(f.id) as finding_count
            FROM scans s
            LEFT JOIN findings f ON f.scan_id = s.id
            GROUP BY s.id ORDER BY s.created_at DESC
        """).fetchall()
        return [dict(row) for row in rows]

    def complete_scan(self, scan_id: int):
        self.conn.execute("UPDATE scans SET status='complete' WHERE id=?", (scan_id,))
        self.conn.commit()
