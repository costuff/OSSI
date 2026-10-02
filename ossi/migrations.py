"""Numbered SQLite migrations for the local OSSI store."""

MIGRATIONS = (
    (
        1,
        "initial_domain",
        """
        CREATE TABLE projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            root_path TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            project_id TEXT,
            status TEXT NOT NULL CHECK(status IN ('active', 'ended')),
            summary TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );
        CREATE TABLE events (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            occurred_at TEXT NOT NULL,
            application TEXT,
            window_title TEXT,
            project_id TEXT,
            payload_json TEXT NOT NULL,
            source TEXT NOT NULL,
            retention_class TEXT NOT NULL,
            session_id TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        );
        CREATE TABLE episodes (
            id TEXT PRIMARY KEY,
            start_at TEXT NOT NULL,
            end_at TEXT,
            project_id TEXT,
            session_id TEXT,
            activity TEXT,
            goal TEXT,
            summary TEXT,
            problems_json TEXT NOT NULL,
            decisions_json TEXT NOT NULL,
            resources_json TEXT NOT NULL,
            unfinished_json TEXT NOT NULL,
            confidence REAL,
            provenance_json TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        );
        CREATE TABLE captures (
            id TEXT PRIMARY KEY,
            raw_text TEXT NOT NULL CHECK(length(trim(raw_text)) > 0),
            created_at TEXT NOT NULL,
            project_id TEXT,
            session_id TEXT,
            source TEXT NOT NULL,
            processing_state TEXT NOT NULL CHECK(processing_state IN ('captured', 'classified', 'converted', 'archived')),
            converted_entity_id TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        );
        CREATE TABLE notes (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL CHECK(length(trim(content)) > 0),
            created_at TEXT NOT NULL,
            project_id TEXT,
            episode_id TEXT,
            session_id TEXT,
            tags_json TEXT NOT NULL,
            source TEXT NOT NULL,
            deleted_at TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(episode_id) REFERENCES episodes(id),
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        );
        CREATE TABLE tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL CHECK(length(trim(title)) > 0),
            status TEXT NOT NULL CHECK(status IN ('open', 'completed', 'deleted')),
            created_at TEXT NOT NULL,
            due_at TEXT,
            project_id TEXT,
            episode_id TEXT,
            session_id TEXT,
            source TEXT NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(episode_id) REFERENCES episodes(id),
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        );
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL CHECK(length(trim(content)) > 0),
            kind TEXT NOT NULL,
            source TEXT NOT NULL,
            confidence REAL,
            created_at TEXT NOT NULL,
            project_id TEXT,
            episode_id TEXT,
            session_id TEXT,
            source_ids_json TEXT NOT NULL,
            deleted_at TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(episode_id) REFERENCES episodes(id),
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        );
        CREATE TABLE decisions (
            id TEXT PRIMARY KEY,
            statement TEXT NOT NULL CHECK(length(trim(statement)) > 0),
            confirmed_at TEXT NOT NULL,
            project_id TEXT,
            episode_id TEXT,
            session_id TEXT,
            source TEXT NOT NULL,
            supersedes_id TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(episode_id) REFERENCES episodes(id),
            FOREIGN KEY(session_id) REFERENCES sessions(id),
            FOREIGN KEY(supersedes_id) REFERENCES decisions(id)
        );
        CREATE TABLE privacy_state (
            id INTEGER PRIMARY KEY CHECK(id = 1),
            active_application INTEGER NOT NULL,
            window_title INTEGER NOT NULL,
            project_directory INTEGER NOT NULL,
            screenshots INTEGER NOT NULL,
            clipboard INTEGER NOT NULL,
            browser_history INTEGER NOT NULL,
            keyboard_content INTEGER NOT NULL,
            microphone INTEGER NOT NULL
        );
        INSERT INTO privacy_state VALUES (1, 1, 0, 0, 0, 0, 0, 0, 0);
        CREATE TABLE inference_runs (
            id TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            request_id TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            latency_ms INTEGER,
            input_tokens INTEGER,
            output_tokens INTEGER,
            success INTEGER NOT NULL,
            error_class TEXT
        );
        CREATE INDEX events_time_idx ON events(occurred_at);
        CREATE INDEX events_session_idx ON events(session_id);
        CREATE INDEX episodes_session_idx ON episodes(session_id);
        CREATE INDEX notes_session_idx ON notes(session_id);
        CREATE INDEX tasks_status_idx ON tasks(status);
        CREATE INDEX captures_state_idx ON captures(processing_state);
        """,
    ),
    (
        2,
        "full_text_search",
        """
        CREATE VIRTUAL TABLE notes_fts USING fts5(id UNINDEXED, content);
        CREATE VIRTUAL TABLE memories_fts USING fts5(id UNINDEXED, content);
        INSERT INTO notes_fts SELECT id, content FROM notes WHERE deleted_at IS NULL;
        INSERT INTO memories_fts SELECT id, content FROM memories WHERE deleted_at IS NULL;
        """,
    ),
)
