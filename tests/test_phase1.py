import json
import os
import tempfile
import unittest

from ossi.context import group_events_into_episodes, normalize_event, reconstruct_context
from ossi.core import OssiCore
from ossi.db import Database
from ossi.domain import CaptureState, SessionStatus
from ossi.fixtures import SESSION_FIXTURE
from ossi.repository import Repository


class Phase1TestCase(unittest.TestCase):
    def setUp(self):
        self.database = Database(":memory:")
        self.repository = Repository(self.database)
        self.core = OssiCore(self.repository)

    def tearDown(self):
        self.database.close()

    def test_empty_database_migrates_with_correct_relationship_schema(self):
        versions = [row[0] for row in self.database.connection.execute("SELECT version FROM schema_migrations ORDER BY version")]
        self.assertEqual(versions, [1, 2])
        session_columns = [row[1] for row in self.database.connection.execute("PRAGMA table_info(sessions)")]
        capture_columns = [row[1] for row in self.database.connection.execute("PRAGMA table_info(captures)")]
        self.assertNotIn("episode_ids_json", session_columns)
        self.assertNotIn("context_id", capture_columns)
        self.assertTrue(self.database.supports_fts)

    def test_project_creation_and_session_lifecycle(self):
        project = self.repository.create_project("OSSI", "/tmp/ossi")
        session = self.repository.start_session(project.id)
        self.assertEqual(session.status, SessionStatus.ACTIVE)
        with self.assertRaises(ValueError):
            self.repository.start_session(project.id)
        ended = self.repository.end_session(session.id, "Paused after debugging")
        self.assertEqual(ended.status, SessionStatus.ENDED)
        with self.assertRaises(ValueError):
            self.repository.end_session(session.id)

    def test_event_fixture_normalizes_groups_and_reconstructs_context(self):
        project = self.repository.create_project("OSSI")
        session = self.repository.start_session(project.id)
        for raw in SESSION_FIXTURE:
            self.core.add_raw_event(raw, session.id, project.id)
        events = self.repository.list_events(session.id)
        self.assertEqual([event.kind for event in events], ["development_activity", "testing_activity", "test_failure", "research_activity", "documentation_viewed", "development_activity"])
        context = reconstruct_context(events)
        self.assertEqual(context.activity, "debugging")
        self.assertEqual(context.active_application, "VS Code")
        episodes = self.core.build_session_episodes(session.id)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0].session_id, session.id)
        self.assertEqual(episodes[0].provenance_event_ids, [event.id for event in events])
        self.assertEqual(self.repository.list_episodes(session.id)[0].session_id, session.id)

    def test_invalid_event_and_ended_session_are_rejected(self):
        session = self.repository.start_session()
        with self.assertRaises(ValueError):
            normalize_event({"type": "application_changed"}, session.id)
        self.repository.end_session(session.id)
        with self.assertRaises(ValueError):
            self.core.add_raw_event(SESSION_FIXTURE[0], session.id)

    def test_capture_is_immediate_and_conversion_is_idempotent(self):
        session = self.repository.start_session()
        capture = self.core.capture("Remember the reconnect issue", session.id)
        self.assertEqual(capture.processing_state, CaptureState.CAPTURED)
        persisted = self.repository.get_capture(capture.id)
        self.assertEqual(persisted.raw_text, capture.raw_text)
        first = self.repository.convert_capture_to_note(capture.id)
        second = self.repository.convert_capture_to_note(capture.id)
        self.assertEqual(first.id, second.id)
        self.assertEqual(self.repository.get_capture(capture.id).processing_state, CaptureState.CONVERTED)

    def test_notes_exact_and_fts_retrieval(self):
        self.repository.create_note("Investigate streaming reconnect handling", None, None)
        self.repository.create_note("Use SQLite for the MVP", None, None)
        exact = self.repository.search_notes("Use SQLite for the MVP", exact=True)
        self.assertEqual(len(exact), 1)
        fts = self.repository.search_notes("streaming reconnect")
        self.assertEqual(len(fts), 1)

    def test_restart_persists_project_session_capture_note_and_events(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "ossi.db")
            first_db = Database(path)
            first_repo = Repository(first_db)
            first_core = OssiCore(first_repo)
            project = first_repo.create_project("OSSI")
            session = first_repo.start_session(project.id)
            first_core.capture("Persist this capture", session.id)
            first_core.note("Persist this note", session.id)
            first_core.add_raw_event(SESSION_FIXTURE[0], session.id, project.id)
            first_db.close()

            second_db = Database(path)
            second_repo = Repository(second_db)
            self.assertEqual(second_repo.get_project(project.id).name, "OSSI")
            self.assertEqual(second_repo.get_session(session.id).status, SessionStatus.ACTIVE)
            self.assertEqual(len(second_repo.list_events(session.id)), 1)
            self.assertEqual(len(second_repo.search_notes("Persist this note", exact=True)), 1)
            self.assertEqual(len(second_repo.list_captures(session.id)), 1)
            second_db.close()

    def test_provenance_and_forget_session(self):
        project = self.repository.create_project("OSSI")
        session = self.repository.start_session(project.id)
        capture = self.core.capture("A user-originated idea", session.id)
        note = self.core.note("A confirmed note", session.id)
        memory = self.repository.create_memory("A retained fact", "explicit", "explicit_user", project.id, session.id, [note.id])
        self.assertEqual(memory.source, "explicit_user")
        self.assertEqual(capture.source, "explicit_user")
        self.repository.forget_session(session.id)
        self.assertIsNone(self.repository.get_session(session.id))
        self.assertIsNone(self.repository.get_capture(capture.id))
        self.assertEqual(self.repository.search_notes("A confirmed note", exact=True), [])
        self.assertIsNone(self.repository.connection.execute("SELECT id FROM memories WHERE id = ?", (memory.id,)).fetchone())

    def test_privacy_state_is_local_and_mutable(self):
        self.assertFalse(self.repository.get_privacy().microphone)
        self.repository.set_privacy(microphone=True)
        self.assertTrue(self.repository.get_privacy().microphone)
        with self.assertRaises(ValueError):
            self.repository.set_privacy(unknown=True)

    def test_malformed_persisted_event_is_rejected(self):
        session = self.repository.start_session()
        self.database.connection.execute(
            "INSERT INTO events(id, kind, occurred_at, payload_json, source, retention_class, session_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("bad", "bad", "2026-10-02T09:00:00+00:00", "{bad", "test", "short", session.id),
        )
        with self.assertRaises(ValueError):
            self.repository.list_events(session.id)


if __name__ == "__main__":
    unittest.main()
