import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "captured_messages.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS captured_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                group_id INTEGER NOT NULL,
                group_name TEXT,
                user_id INTEGER NOT NULL,
                sender_name TEXT,
                raw_message TEXT NOT NULL,
                is_target INTEGER DEFAULT 1,
                intent TEXT,
                urgency TEXT,
                summary TEXT,
                entities TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_captured_message(
    group_id: int,
    user_id: int,
    raw_message: str,
    sender_name: str = "",
    group_name: str = "",
    is_target: bool = True,
    intent: str = "",
    urgency: str = "",
    summary: str = "",
    entities: dict = None
) -> int:
    init_db()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entities_str = json.dumps(entities or {}, ensure_ascii=False)
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO captured_messages (
                timestamp, group_id, group_name, user_id, sender_name,
                raw_message, is_target, intent, urgency, summary, entities
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now_str, group_id, group_name, user_id, sender_name,
            raw_message, 1 if is_target else 0, intent, urgency, summary, entities_str
        ))
        conn.commit()
        return cursor.lastrowid

def get_recent_records(limit: int = 50) -> list:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM captured_messages ORDER BY id DESC LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
