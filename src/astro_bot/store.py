import json
import sqlite3


class Store:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS natal (
            user_id INTEGER PRIMARY KEY,
            data TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            ts DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        self.conn.commit()

    def set_natal(self, user_id, data: dict):
        self.conn.execute(
            "INSERT INTO natal(user_id, data) VALUES(?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET data=excluded.data",
            (user_id, json.dumps(data)))
        self.conn.commit()

    def get_natal(self, user_id) -> dict | None:
        row = self.conn.execute(
            "SELECT data FROM natal WHERE user_id=?", (user_id,)).fetchone()
        return json.loads(row["data"]) if row else None

    def add_message(self, user_id, role, content):
        self.conn.execute(
            "INSERT INTO history(user_id, role, content) VALUES(?,?,?)",
            (user_id, role, content))
        self.conn.commit()

    def recent_messages(self, user_id, limit=20):
        rows = self.conn.execute(
            "SELECT role, content FROM history WHERE user_id=? "
            "ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
