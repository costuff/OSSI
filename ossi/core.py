"""Application services for the local OSSI Phase 1 core."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .context import group_events_into_episodes, normalize_event, reconstruct_context
from .domain import Capture, Context, Episode, Event, Note, Project, Session
from .repository import Repository


class OssiCore:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def start_session(self, project_name: Optional[str] = None, root_path: Optional[str] = None) -> Session:
        project_id = None
        if project_name:
            project_id = self.repository.get_or_create_project(project_name, root_path).id
        return self.repository.start_session(project_id)

    def current_session(self, project_name: Optional[str] = None) -> Optional[Session]:
        project_id = None
        if project_name:
            project = self.repository.get_or_create_project(project_name)
            project_id = project.id
        return self.repository.active_session(project_id)

    def add_raw_event(self, raw: Dict[str, Any], session_id: str, project_id: Optional[str] = None) -> Event:
        session = self.repository.get_session(session_id)
        if session is None or session.status.value != "active":
            raise ValueError("events require an active session")
        event = normalize_event(raw, session_id, project_id if project_id is not None else session.project_id)
        return self.repository.insert_event(event)

    def build_session_episodes(self, session_id: str) -> List[Episode]:
        events = self.repository.list_events(session_id)
        episodes = group_events_into_episodes(events)
        existing = self.repository.list_episodes(session_id)
        if existing:
            return existing
        for episode in episodes:
            self.repository.save_episode(episode)
        return episodes

    def current_context(self, session_id: str) -> Context:
        return reconstruct_context(self.repository.list_events(session_id))

    def capture(self, text: str, session_id: Optional[str] = None, project_id: Optional[str] = None) -> Capture:
        session = self.repository.get_session(session_id) if session_id else None
        if session_id and session is None:
            raise ValueError("session does not exist")
        if session and session.status.value != "active":
            raise ValueError("captures require an active session")
        effective_project = project_id if project_id is not None else (session.project_id if session else None)
        return self.repository.create_capture(text, effective_project, session_id)

    def note(self, text: str, session_id: Optional[str] = None, project_id: Optional[str] = None) -> Note:
        session = self.repository.get_session(session_id) if session_id else None
        if session_id and session is None:
            raise ValueError("session does not exist")
        if session and session.status.value != "active":
            raise ValueError("notes require an active session")
        effective_project = project_id if project_id is not None else (session.project_id if session else None)
        return self.repository.create_note(text, effective_project, session_id)

    def recall(self, query: str) -> List[Note]:
        exact = self.repository.search_notes(query, exact=True)
        return exact or self.repository.search_notes(query)

    def today(self) -> Dict[str, Any]:
        today = datetime.now(timezone.utc).date().isoformat()
        rows = self.repository.connection.execute(
            "SELECT * FROM sessions WHERE date(started_at) = ? OR date(ended_at) = ? ORDER BY started_at",
            (today, today),
        ).fetchall()
        sessions = [self.repository.get_session(row["id"]) for row in rows]
        return {
            "date": today,
            "sessions": [session for session in sessions if session is not None],
            "episodes": [episode for session in sessions if session for episode in self.repository.list_episodes(session.id)],
            "notes": [self.repository._note_from_row(row) for row in self.repository.connection.execute("SELECT * FROM notes WHERE date(created_at) = ? AND deleted_at IS NULL ORDER BY created_at", (today,)).fetchall()],
            "captures": [capture for session in sessions if session for capture in self.repository.list_captures(session.id)],
            "tasks": [task for session in sessions if session for task in self.repository.list_tasks(session.id)],
            "memories": [memory for session in sessions if session for memory in self.repository.list_memories(session.id)],
        }
