# OSSI Architecture

## Proposed system

```text
macOS menu bar / floating presence
        SwiftUI + AppKit
        permissions, collectors, UI state
                |
                | localhost HTTP over loopback
                v
        Python OSSI Core
        context, episodes, memory, secretary, policy
                |
                | selected semantic context only
                v
        InferenceProvider
        AMDProvider -> AMD Developer Cloud / ROCm / vLLM
        LocalProvider -> optional local model or deterministic fallback
```

The hackathon implementation is a modular monolith, not a set of services. SQLite and the Python process are local. The native client is a separate process because it owns macOS permissions and the native interaction surface.

## macOS client

Use Swift 6, SwiftUI, and AppKit. The app is an `LSUIElement` menu-bar application with a borderless, transparent, movable `NSPanel` for the OSSI presence. Use public APIs only. Keep the panel compact by default and expand it for user-requested conversation, context inspection, privacy controls, and diagnostics.

Responsibilities:

- Observe the active application and permitted window metadata.
- Receive explicit user commands and optional voice input.
- Render the fixed UI state machine: `idle`, `observing`, `listening`, `thinking`, `suggestionAvailable`, `assisting`, `expanded`.
- Display microphone, perception, and inference status.
- Call the Core over loopback HTTP and never decide policy from model output.

The first client can use a manual refresh or a short polling interval. A global shortcut is useful but not a prerequisite for the first vertical slice.

## Python OSSI Core

Suggested modules:

```text
core/
  domain.py          # typed entities and enums
  storage.py         # SQLite repositories and migrations
  context.py         # normalization and current-context queries
  episodes.py        # grouping and summarization
        secretary.py       # capture, note, recall, today, and unfinished workflows
  policy.py          # consent, retention, and suggestion rules
  providers/
    base.py          # InferenceProvider protocol
    amd.py           # OpenAI-compatible AMD endpoint adapter
    local.py         # optional local adapter
  api.py             # localhost HTTP routes
  cli.py             # ossi context/note/recall/today
```

The core is the owner of domain state. The client is a presentation and OS integration layer. All model output is treated as untrusted data and validated against typed response schemas before storage or display.

## Domain model

All timestamps are UTC ISO 8601 values. IDs are UUIDs. `project_id` may be null when the user has not selected a project.

| Entity | Required meaning and fields |
| --- | --- |
| `Event` | A raw or normalized signal: `id`, `kind`, `occurred_at`, `application`, `window_title` after sanitization, `project_id`, `payload`, `source`, and `retention_class`. |
| `Context` | The current semantic view: `project_id`, `activity`, `goal`, `active_application`, `signals`, `confidence`, `observed_from`, and `observed_until`. It is derived and replaceable, not authoritative memory. |
| `Episode` | A meaningful work period: `id`, `start_at`, `end_at`, `project_id`, `activity`, `goal`, `summary`, `problems`, `decisions`, `resources`, `unfinished`, `confidence`, and `provenance_event_ids`. |
| `Session` | A continuity boundary for observation and assistance: `id`, `started_at`, `ended_at`, `project_id`, `status`, and `summary`. Episodes point to their session; the relationship is not duplicated on Session. |
| `Capture` | An immediately persisted inbox item: `id`, `raw_text`, `created_at`, `project_id`, `session_id`, `source`, `processing_state`, and optional `converted_entity_id`. Context remains ephemeral in Phase 1. |
| `Note` | User-recorded information: `id`, `content`, `created_at`, `project_id`, `episode_id`, `tags`, `source=explicit_user`, and `deleted_at`. |
| `Task` | An intended action: `id`, `title`, `status`, `created_at`, `due_at`, `project_id`, `episode_id`, and `source`. |
| `Memory` | Retained information, explicit or derived: `id`, `content`, `kind`, `source`, `confidence`, `created_at`, `project_id`, `episode_id`, `source_ids`, and `deleted_at`. |
| `Decision` | A user-confirmed choice: `id`, `statement`, `confirmed_at`, `project_id`, `episode_id`, `source=explicit_user`, and `supersedes_id`. |

`Session` owns continuity and lifecycle. `Episode` owns the semantic account of one meaningful activity period. `episodes.session_id` is the single source of truth for Session -> Episode relationships. Notes, tasks, decisions, and captures are queryable by `session_id`; they do not copy the session summary. A session can contain multiple episodes, and an episode belongs to at most one session in the first slice.

`Capture` is the synchronous secretary inbox. Storing its raw user text is local and deterministic, requires no inference, and returns immediately. A later worker may classify it and convert it into a `Note`, `Task`, or `Memory`, preserving the capture as provenance. Inferences are never promoted to `Note` or `Decision` without user confirmation. `Memory.source` and `source_ids` make provenance inspectable.

## SQLite schema

The initial schema is intentionally relational and searchable without a vector database:

```sql
projects(id TEXT PRIMARY KEY, name TEXT NOT NULL, root_path TEXT, created_at TEXT NOT NULL);
sessions(id TEXT PRIMARY KEY, started_at TEXT NOT NULL, ended_at TEXT, project_id TEXT,
         status TEXT NOT NULL, summary TEXT);
events(id TEXT PRIMARY KEY, kind TEXT NOT NULL, occurred_at TEXT NOT NULL,
         application TEXT, window_title TEXT, project_id TEXT, payload_json TEXT NOT NULL,
         source TEXT NOT NULL, retention_class TEXT NOT NULL, session_id TEXT,
         FOREIGN KEY(project_id) REFERENCES projects(id), FOREIGN KEY(session_id) REFERENCES sessions(id));
episodes(id TEXT PRIMARY KEY, start_at TEXT NOT NULL, end_at TEXT, project_id TEXT,
           activity TEXT, goal TEXT, summary TEXT, problems_json TEXT, decisions_json TEXT,
           resources_json TEXT, unfinished_json TEXT, confidence REAL, provenance_json TEXT NOT NULL,
           session_id TEXT, FOREIGN KEY(session_id) REFERENCES sessions(id));
captures(id TEXT PRIMARY KEY, raw_text TEXT NOT NULL, created_at TEXT NOT NULL, project_id TEXT,
         session_id TEXT, source TEXT NOT NULL, processing_state TEXT NOT NULL,
         converted_entity_id TEXT, FOREIGN KEY(project_id) REFERENCES projects(id),
         FOREIGN KEY(session_id) REFERENCES sessions(id));
notes(id TEXT PRIMARY KEY, content TEXT NOT NULL, created_at TEXT NOT NULL, project_id TEXT,
        episode_id TEXT, session_id TEXT, tags_json TEXT NOT NULL, source TEXT NOT NULL, deleted_at TEXT);
tasks(id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
        due_at TEXT, project_id TEXT, episode_id TEXT, session_id TEXT, source TEXT NOT NULL);
memories(id TEXT PRIMARY KEY, content TEXT NOT NULL, kind TEXT NOT NULL, source TEXT NOT NULL,
           confidence REAL, created_at TEXT NOT NULL, project_id TEXT, episode_id TEXT,
           session_id TEXT, source_ids_json TEXT NOT NULL, deleted_at TEXT);
decisions(id TEXT PRIMARY KEY, statement TEXT NOT NULL, confirmed_at TEXT NOT NULL,
            project_id TEXT, episode_id TEXT, session_id TEXT, source TEXT NOT NULL, supersedes_id TEXT);
inference_runs(id TEXT PRIMARY KEY, provider TEXT NOT NULL, model TEXT NOT NULL,
                   request_id TEXT NOT NULL, started_at TEXT NOT NULL, completed_at TEXT,
                   latency_ms INTEGER, input_tokens INTEGER, output_tokens INTEGER,
                   success INTEGER NOT NULL, error_class TEXT);
```

Add indexes on event time, project, session, note content, memory content, task status, and capture processing state. Use SQLite FTS5 for note and memory search before considering embeddings. Schema changes must use numbered migrations.

## Inference provider contract

The core depends on a provider protocol, never on an AMD SDK or endpoint shape:

```python
class InferenceProvider(Protocol):
    def generate(self, request: GenerationRequest) -> GenerationResult: ...
    def structured_generate(self, request: StructuredRequest) -> StructuredResult: ...
    def embed(self, request: EmbeddingRequest) -> EmbeddingResult: ...
```

`generate` is for concise assistance, `structured_generate` validates model output against a named schema for context or episode extraction, and `embed` is reserved for a future retrieval need. Each inference-backed result includes provider, model, request ID, timestamp, input and output token counts, latency, and failure metadata. These fields are persisted in `inference_runs` and exposed through the diagnostics API/UI. A deterministic fallback has no AMD provenance and must be labeled as local fallback, never as AMD output. The first slice may leave `embed` unsupported and must report that explicitly.

`AMDProvider` reads `OSSI_INFERENCE_ENDPOINT`, `OSSI_MODEL`, and `OSSI_API_KEY` from the environment, uses bounded timeouts, sends semantic context only, validates structured output, and records an `inference_runs` row. It targets an OpenAI-compatible vLLM endpoint on AMD Developer Cloud. `LocalProvider` implements the same contract for offline development and deterministic fallback responses, but its results are explicitly marked `provider=local`.

## Deterministic and inference-backed behavior

| Feature | Local deterministic | AMD inference | Optional |
| --- | --- | --- | --- |
| Store explicit note or capture | Yes | No | No |
| Exact note retrieval | Yes | No | No |
| Start/end session | Yes | No | No |
| Inspect privacy settings | Yes | No | No |
| Forget session | Yes | No | No |
| Display current application | Yes | No | No |
| Display provider diagnostics | Yes | No | No |
| Normalize events and group a basic episode | Yes | No | No |
| Interpret semantic context | No | Yes | No |
| Summarize an episode or session | No | Yes | No |
| Ambiguous natural-language retrieval | No | Yes | Yes, exact/FTS retrieval remains available |
| Contextual assistance | No | Yes | No |
| Work summary | No | Yes | No |
| Relationship discovery between current and previous context | No | Yes | Yes |
| Classify or convert a Capture | No | Yes | Yes, user can classify manually |

## IPC choice

Use an HTTP JSON API bound only to `127.0.0.1` for the hackathon. It is easy to inspect with curl, easy to test independently of Swift, and sufficient for low-frequency context and assistant requests. Add a per-session bearer token generated by Core and passed to the native client; reject non-loopback requests and bind to an ephemeral port recorded in the app session.

Move to a Unix domain socket or XPC only if threat modeling or packaging demonstrates a concrete need. WebSockets are unnecessary until live streaming or push suggestions are required.

Initial routes:

- `GET /health`
- `GET /context`
- `POST /events`
- `POST /sessions`
- `POST /sessions/{id}/end`
- `POST /captures`
- `POST /notes`
- `GET /recall?q=...`
- `GET /today`
- `GET /privacy`
- `POST /forget/session`
- `POST /assist`
- `GET /diagnostics/inference`

## Data flow

Collectors emit raw events inside an active session. Normalization adds a stable event type and project when available. The context engine creates semantic events and an ephemeral current context. The episode builder groups related events using time, project, application, and activity continuity. Only selected semantic context is sent to an inference provider for interpretation or summarization. Explicit notes and captures are stored directly without requiring model inference; a capture can be classified asynchronously later.

## Operational principles

- Local-first storage and processing.
- Explicit provenance on every retained item.
- Short retention for raw events; durable retention for explicit notes.
- Structured logs with request ID, provider, model, tokens, latency, and failure state, never secrets or raw sensitive content.
- Deterministic behavior must remain usable when AMD is unavailable.
