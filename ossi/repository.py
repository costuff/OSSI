"""SQLite repositories and persistence rules for Phase 1."""

import json
import sqlite3
import uuid
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .db import Database
from .domain import (
    Capture,
    CaptureState,
    Decision,
    Episode,
    Event,
    Memory,
    Note,
    PrivacyState,
    Project,
    Session,
    SessionStatus,
    Task,
    TaskStatus,
    utc_now,
)


def new_id() -> str:
    return str(uuid.uuid4())


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _loaded_json(value: str, expected: type) -> Any:
    try:
        result = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("malformed persisted JSON") from exc
    if not isinstance(result, expected):
        raise ValueError("persisted JSON has an unexpected shape")
    return result


class Repository:
    def __init__(self, database: Database) -> None:
        self.db = database
        self.connection = database.connection

    def create_project(self, name: str, root_path: Optional[str] = None) -> Project:
        if not name.strip():
            raise ValueError("project name cannot be empty")
        project = Project(new_id(), name.strip(), root_path, utc_now())
        self.connection.execute(
            "INSERT INTO projects(id, name, root_path, created_at) VALUES (?, ?, ?, ?)",
            (project.id, project.name, project.root_path, project.created_at),
        )
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        row = self.connection.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if row is None:
            return None
        return Project(row["id"], row["name"], row["root_path"], row["created_at"])

    def get_or_create_project(self, name: str, root_path: Optional[str] = None) -> Project:
        row = self.connection.execute(
            "SELECT * FROM projects WHERE name = ? AND COALESCE(root_path, '') = COALESCE(?, '')",
            (name.strip(), root_path),
        ).fetchone()
        if row is not None:
            return Project(row["id"], row["name"], row["root_path"], row["created_at"])
        return self.create_project(name, root_path)

    def start_session(self, project_id: Optional[str] = None) -> Session:
        if project_id is not None and self.get_project(project_id) is None:
            raise ValueError("project does not exist")
        active = self.connection.execute(
            "SELECT id FROM sessions WHERE status = 'active' AND project_id IS ?",
            (project_id,),
        ).fetchone()
        if active is not None:
            raise ValueError("an active session already exists for this project")
        session = Session(new_id(), utc_now(), None, project_id, SessionStatus.ACTIVE, None)
        self.connection.execute(
            "INSERT INTO sessions(id, started_at, project_id, status, summary) VALUES (?, ?, ?, ?, ?)",
            (session.id, session.started_at, session.project_id, session.status.value, session.summary),
        )
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        row = self.connection.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            return None
        return Session(row["id"], row["started_at"], row["ended_at"], row["project_id"], SessionStatus(row["status"]), row["summary"])

    def active_session(self, project_id: Optional[str] = None) -> Optional[Session]:
        if project_id is None:
            row = self.connection.execute(
                "SELECT * FROM sessions WHERE status = 'active' ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
        else:
            row = self.connection.execute(
                "SELECT * FROM sessions WHERE status = 'active' AND project_id = ? ORDER BY started_at DESC LIMIT 1",
                (project_id,),
            ).fetchone()
        if row is None:
            return None
        return self.get_session(row["id"])

    def end_session(self, session_id: str, summary: Optional[str] = None) -> Session:
        session = self.get_session(session_id)
        if session is None:
            raise ValueError("session does not exist")
        if session.status != SessionStatus.ACTIVE:
            raise ValueError("session is already ended")
        ended = utc_now()
        self.connection.execute(
            "UPDATE sessions SET ended_at = ?, status = 'ended', summary = ? WHERE id = ? AND status = 'active'",
            (ended, summary, session_id),
        )
        return self.get_session(session_id)  # type: ignore

    def insert_event(self, event: Event) -> Event:
        self.connection.execute(
            """INSERT INTO events(id, kind, occurred_at, application, window_title,
               project_id, payload_json, source, retention_class, session_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (event.id, event.kind, event.occurred_at, event.application, event.window_title,
             event.project_id, _json(event.payload), event.source, event.retention_class, event.session_id),
        )
        return event

    def list_events(self, session_id: str) -> List[Event]:
        rows = self.connection.execute(
            "SELECT * FROM events WHERE session_id = ? ORDER BY occurred_at, id", (session_id,)
        ).fetchall()
        return [self._event_from_row(row) for row in rows]

    def _event_from_row(self, row: sqlite3.Row) -> Event:
        payload = _loaded_json(row["payload_json"], dict)
        return Event(row["id"], row["kind"], row["occurred_at"], row["application"], row["window_title"], row["project_id"], payload, row["source"], row["retention_class"], row["session_id"])

    def save_episode(self, episode: Episode) -> Episode:
        self.connection.execute(
            """INSERT OR REPLACE INTO episodes(
               id, start_at, end_at, project_id, session_id, activity, goal, summary,
               problems_json, decisions_json, resources_json, unfinished_json, confidence, provenance_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (episode.id, episode.start_at, episode.end_at, episode.project_id, episode.session_id,
             episode.activity, episode.goal, episode.summary, _json(episode.problems), _json(episode.decisions),
             _json(episode.resources), _json(episode.unfinished), episode.confidence, _json(episode.provenance_event_ids)),
        )
        return episode

    def list_episodes(self, session_id: str) -> List[Episode]:
        rows = self.connection.execute(
            "SELECT * FROM episodes WHERE session_id = ? ORDER BY start_at, id", (session_id,)
        ).fetchall()
        return [self._episode_from_row(row) for row in rows]

    def _episode_from_row(self, row: sqlite3.Row) -> Episode:
        return Episode(
            row["id"], row["start_at"], row["end_at"], row["project_id"], row["session_id"],
            row["activity"], row["goal"], row["summary"], _loaded_json(row["problems_json"], list),
            _loaded_json(row["decisions_json"], list), _loaded_json(row["resources_json"], list),
            _loaded_json(row["unfinished_json"], list), row["confidence"], _loaded_json(row["provenance_json"], list),
        )

    def create_capture(self, raw_text: str, project_id: Optional[str], session_id: Optional[str], source: str = "explicit_user") -> Capture:
        if not raw_text.strip():
            raise ValueError("capture text cannot be empty")
        capture = Capture(new_id(), raw_text, utc_now(), project_id, session_id, source, CaptureState.CAPTURED, None)
        self.connection.execute(
            "INSERT INTO captures(id, raw_text, created_at, project_id, session_id, source, processing_state, converted_entity_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (capture.id, capture.raw_text, capture.created_at, capture.project_id, capture.session_id, capture.source, capture.processing_state.value, capture.converted_entity_id),
        )
        return capture

    def get_capture(self, capture_id: str) -> Optional[Capture]:
        row = self.connection.execute("SELECT * FROM captures WHERE id = ?", (capture_id,)).fetchone()
        if row is None:
            return None
        return Capture(row["id"], row["raw_text"], row["created_at"], row["project_id"], row["session_id"], row["source"], CaptureState(row["processing_state"]), row["converted_entity_id"])

    def list_captures(self, session_id: Optional[str] = None) -> List[Capture]:
        if session_id is None:
            rows = self.connection.execute("SELECT * FROM captures ORDER BY created_at").fetchall()
        else:
            rows = self.connection.execute("SELECT * FROM captures WHERE session_id = ? ORDER BY created_at", (session_id,)).fetchall()
        return [Capture(row["id"], row["raw_text"], row["created_at"], row["project_id"], row["session_id"], row["source"], CaptureState(row["processing_state"]), row["converted_entity_id"]) for row in rows]

    def convert_capture_to_note(self, capture_id: str, tags: Optional[Sequence[str]] = None) -> Note:
        capture = self.get_capture(capture_id)
        if capture is None:
            raise ValueError("capture does not exist")
        if capture.processing_state == CaptureState.CONVERTED and capture.converted_entity_id:
            existing = self.get_note(capture.converted_entity_id)
            if existing is not None:
                return existing
            raise ValueError("capture is marked converted but its note is missing")
        note = Note(new_id(), capture.raw_text, capture.created_at, capture.project_id, None, capture.session_id, list(tags or []), "capture:%s" % capture.id, None)
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            self.connection.execute(
                "INSERT INTO notes(id, content, created_at, project_id, episode_id, session_id, tags_json, source, deleted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (note.id, note.content, note.created_at, note.project_id, note.episode_id, note.session_id, _json(note.tags), note.source, note.deleted_at),
            )
            self._fts_insert("notes_fts", note.id, note.content)
            self.connection.execute(
                "UPDATE captures SET processing_state = 'converted', converted_entity_id = ? WHERE id = ? AND processing_state != 'converted'",
                (note.id, capture.id),
            )
            self.connection.execute("COMMIT")
        except Exception:
            self.connection.execute("ROLLBACK")
            raise
        return note

    def create_note(self, content: str, project_id: Optional[str], session_id: Optional[str], episode_id: Optional[str] = None, tags: Optional[Sequence[str]] = None, source: str = "explicit_user") -> Note:
        if not content.strip():
            raise ValueError("note content cannot be empty")
        note = Note(new_id(), content, utc_now(), project_id, episode_id, session_id, list(tags or []), source, None)
        self.connection.execute(
            "INSERT INTO notes(id, content, created_at, project_id, episode_id, session_id, tags_json, source, deleted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (note.id, note.content, note.created_at, note.project_id, note.episode_id, note.session_id, _json(note.tags), note.source, note.deleted_at),
        )
        self._fts_insert("notes_fts", note.id, note.content)
        return note

    def get_note(self, note_id: str) -> Optional[Note]:
        row = self.connection.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        return self._note_from_row(row) if row is not None else None

    def _note_from_row(self, row: sqlite3.Row) -> Note:
        return Note(row["id"], row["content"], row["created_at"], row["project_id"], row["episode_id"], row["session_id"], _loaded_json(row["tags_json"], list), row["source"], row["deleted_at"])

    def search_notes(self, query: str, exact: bool = False) -> List[Note]:
        if not query.strip():
            return []
        if exact:
            rows = self.connection.execute("SELECT * FROM notes WHERE deleted_at IS NULL AND content = ? ORDER BY created_at", (query,)).fetchall()
        elif self.db.supports_fts:
            safe = ' '.join('"%s"' % word.replace('"', ' ') for word in query.split())
            rows = self.connection.execute("SELECT n.* FROM notes n JOIN notes_fts f ON f.id = n.id WHERE notes_fts MATCH ? AND n.deleted_at IS NULL ORDER BY n.created_at", (safe,)).fetchall()
        else:
            rows = self.connection.execute("SELECT * FROM notes WHERE deleted_at IS NULL AND content LIKE ? ORDER BY created_at", ("%%%s%%" % query,)).fetchall()
        return [self._note_from_row(row) for row in rows]

    def create_task(self, title: str, project_id: Optional[str], session_id: Optional[str], episode_id: Optional[str] = None, source: str = "explicit_user") -> Task:
        if not title.strip():
            raise ValueError("task title cannot be empty")
        task = Task(new_id(), title, TaskStatus.OPEN, utc_now(), None, project_id, episode_id, session_id, source)
        self.connection.execute(
            "INSERT INTO tasks(id, title, status, created_at, due_at, project_id, episode_id, session_id, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (task.id, task.title, task.status.value, task.created_at, task.due_at, task.project_id, task.episode_id, task.session_id, task.source),
        )
        return task

    def list_tasks(self, session_id: Optional[str] = None) -> List[Task]:
        query = "SELECT * FROM tasks"
        parameters: Tuple[Any, ...] = ()
        if session_id is not None:
            query += " WHERE session_id = ?"
            parameters = (session_id,)
        rows = self.connection.execute(query + " ORDER BY created_at", parameters).fetchall()
        return [Task(row["id"], row["title"], TaskStatus(row["status"]), row["created_at"], row["due_at"], row["project_id"], row["episode_id"], row["session_id"], row["source"]) for row in rows]

    def create_memory(self, content: str, kind: str, source: str, project_id: Optional[str], session_id: Optional[str], source_ids: Optional[Sequence[str]] = None, confidence: Optional[float] = None) -> Memory:
        if not content.strip():
            raise ValueError("memory content cannot be empty")
        memory = Memory(new_id(), content, kind, source, confidence, utc_now(), project_id, None, session_id, list(source_ids or []), None)
        self.connection.execute(
            "INSERT INTO memories(id, content, kind, source, confidence, created_at, project_id, episode_id, session_id, source_ids_json, deleted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (memory.id, memory.content, memory.kind, memory.source, memory.confidence, memory.created_at, memory.project_id, memory.episode_id, memory.session_id, _json(memory.source_ids), memory.deleted_at),
        )
        self._fts_insert("memories_fts", memory.id, memory.content)
        return memory

    def list_memories(self, session_id: Optional[str] = None) -> List[Memory]:
        query = "SELECT * FROM memories"
        parameters: Tuple[Any, ...] = ()
        if session_id is not None:
            query += " WHERE session_id = ?"
            parameters = (session_id,)
        rows = self.connection.execute(query + " ORDER BY created_at", parameters).fetchall()
        return [Memory(row["id"], row["content"], row["kind"], row["source"], row["confidence"], row["created_at"], row["project_id"], row["episode_id"], row["session_id"], _loaded_json(row["source_ids_json"], list), row["deleted_at"]) for row in rows]

    def create_decision(self, statement: str, project_id: Optional[str], session_id: Optional[str], source: str = "explicit_user") -> Decision:
        if not statement.strip():
            raise ValueError("decision cannot be empty")
        decision = Decision(new_id(), statement, utc_now(), project_id, None, session_id, source, None)
        self.connection.execute(
            "INSERT INTO decisions(id, statement, confirmed_at, project_id, episode_id, session_id, source, supersedes_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (decision.id, decision.statement, decision.confirmed_at, decision.project_id, decision.episode_id, decision.session_id, decision.source, decision.supersedes_id),
        )
        return decision

    def _fts_insert(self, table: str, item_id: str, content: str) -> None:
        if self.db.supports_fts:
            self.connection.execute("INSERT INTO %s(id, content) VALUES (?, ?)" % table, (item_id, content))

    def get_privacy(self) -> PrivacyState:
        row = self.connection.execute("SELECT * FROM privacy_state WHERE id = 1").fetchone()
        return PrivacyState(**{key: bool(row[key]) for key in row.keys() if key != "id"})

    def set_privacy(self, **values: bool) -> PrivacyState:
        allowed = set(PrivacyState.__dataclass_fields__.keys())
        if set(values) - allowed:
            raise ValueError("unknown privacy setting")
        current = self.get_privacy().__dict__
        current.update(values)
        ordered_keys = sorted(current)
        self.connection.execute(
            "UPDATE privacy_state SET %s WHERE id = 1" % ", ".join("%s = ?" % key for key in ordered_keys),
            tuple(int(current[key]) for key in ordered_keys),
        )
        return self.get_privacy()

    def forget_session(self, session_id: str) -> None:
        if self.get_session(session_id) is None:
            raise ValueError("session does not exist")
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            for table in ("notes", "tasks", "memories", "decisions", "captures", "events", "episodes"):
                self.connection.execute("DELETE FROM %s WHERE session_id = ?" % table, (session_id,))
            self.connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            self.connection.execute("COMMIT")
        except Exception:
            self.connection.execute("ROLLBACK")
            raise
