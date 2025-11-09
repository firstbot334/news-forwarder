import sqlite3
from typing import Optional

class DB:
    def __init__(self, path: str):
        self.path = path
        self._init()

    def _init(self):
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS checkpoints (source TEXT PRIMARY KEY, last_id INTEGER NOT NULL)"
        )
        con.commit()
        con.close()

    def get_last_id(self, source: str) -> int:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute("SELECT last_id FROM checkpoints WHERE source=?", (str(source),))
        row = cur.fetchone()
        con.close()
        return int(row[0]) if row else 0

    def set_last_id(self, source: str, last_id: int):
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO checkpoints(source, last_id) VALUES (?, ?) "
            "ON CONFLICT(source) DO UPDATE SET last_id=excluded.last_id",
            (str(source), int(last_id)),
        )
        con.commit()
        con.close()
