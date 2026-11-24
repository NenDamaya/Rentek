"""
Módulo de sesiones: Gestión de conversaciones y persistencia de historial.
"""

import uuid
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from src import database as db
from .config import config


MAX_CONTEXT_TOKENS = 6000
CHARS_PER_TOKEN = 4


class SessionManager:
    def __init__(self):
        self.memory_cache: Dict[str, List[Dict]] = {}

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        conn = db.get_conn()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO conversations (id) VALUES (%s)",
                    (session_id,)
                )
                conn.commit()
                cur.close()
            except Exception:
                pass
            finally:
                conn.close()
        self.memory_cache[session_id] = []
        return session_id

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        if session_id in self.memory_cache:
            return self.memory_cache[session_id]

        messages = []
        conn = db.get_conn()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    """SELECT role, content, tool_calls, tool_call_id, tool_name
                       FROM conversation_messages
                       WHERE conversation_id = %s
                       ORDER BY created_at""",
                    (session_id,)
                )
                rows = cur.fetchall()
                cur.close()

                for row in rows:
                    msg = {"role": row[0]}
                    if row[1] is not None:
                        msg["content"] = row[1]
                    if row[2] is not None:
                        msg["tool_calls"] = row[2] if isinstance(row[2], list) else json.loads(row[2])
                    if row[3] is not None:
                        msg["tool_call_id"] = row[3]
                    if row[4] is not None:
                        msg["name"] = row[4]
                    messages.append(msg)
            except Exception:
                pass
            finally:
                conn.close()

        self.memory_cache[session_id] = messages
        return messages

    def add_message(
        self,
        session_id: str,
        role: str,
        content: Optional[str] = None,
        tool_calls: Optional[List[Dict]] = None,
        tool_call_id: Optional[str] = None,
        tool_name: Optional[str] = None,
    ):
        msg = {"role": role}
        if content is not None:
            msg["content"] = content
        if tool_calls is not None:
            msg["tool_calls"] = tool_calls
        if tool_call_id is not None:
            msg["tool_call_id"] = tool_call_id
        if tool_name is not None:
            msg["name"] = tool_name

        if session_id not in self.memory_cache:
            self.memory_cache[session_id] = []
        self.memory_cache[session_id].append(msg)

        tokens_est = len(json.dumps(msg, ensure_ascii=False)) // CHARS_PER_TOKEN

        conn = db.get_conn()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO conversation_messages
                       (conversation_id, role, content, tool_calls, tool_call_id, tool_name, tokens_estimated)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        session_id,
                        role,
                        content,
                        json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None,
                        tool_call_id,
                        tool_name,
                        tokens_est,
                    )
                )
                cur.execute(
                    "UPDATE conversations SET updated_at = NOW() WHERE id = %s",
                    (session_id,)
                )
                conn.commit()
                cur.close()
            except Exception:
                pass
            finally:
                conn.close()

    def trim_history(self, session_id: str) -> List[Dict[str, Any]]:
        history = self.get_session_history(session_id)
        if not history:
            return history

        total_chars = sum(len(json.dumps(m, ensure_ascii=False)) for m in history)
        estimated_tokens = total_chars // CHARS_PER_TOKEN

        if estimated_tokens <= MAX_CONTEXT_TOKENS:
            return history

        system_msgs = [m for m in history if m.get("role") == "system"]
        other_msgs = [m for m in history if m.get("role") != "system"]

        kept = []
        current_tokens = sum(len(json.dumps(m, ensure_ascii=False)) for m in system_msgs) // CHARS_PER_TOKEN

        for msg in reversed(other_msgs):
            msg_tokens = len(json.dumps(msg, ensure_ascii=False)) // CHARS_PER_TOKEN
            if current_tokens + msg_tokens > MAX_CONTEXT_TOKENS:
                break
            kept.insert(0, msg)
            current_tokens += msg_tokens

        return system_msgs + kept

    def delete_session(self, session_id: str):
        if session_id in self.memory_cache:
            del self.memory_cache[session_id]

        conn = db.get_conn()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM conversations WHERE id = %s", (session_id,))
                conn.commit()
                cur.close()
            except Exception:
                pass
            finally:
                conn.close()


session_manager = SessionManager()
