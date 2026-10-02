# OSSI Roadmap

## Must Have: first demonstrable slice

1. Python package and typed domain models.
2. SQLite migrations and repositories.
3. Session lifecycle: start, end, status, project association, and session-scoped queries.
4. CLI commands: `context`, `note`, `capture`, `recall`, `today`, and `session`.
5. Capture inbox with immediate local persistence and no synchronous inference dependency.
6. Event normalization for a manually generated or macOS application event.
7. Current context and simple episode grouping within a session.
8. `InferenceProvider` and a real `AMDProvider` request.
9. Provider diagnostics: provider, model, request ID, timestamp, tokens, latency, and failures.
10. Privacy state and forget-session operation.
11. Automated tests for models, storage, session continuity, capture latency, normalization, recall, and provider error handling.

## Should Have: hackathon experience

- Native SwiftUI/AppKit floating presence.
- Localhost HTTP bridge with authentication.
- Active application observation.
- Window title observation where permitted.
- Context-aware assistance and secretary responses.
- Explicit note association with project and episode.
- A privacy panel showing enabled signals and selected outbound context.
- A scripted end-to-end demo fixture and clean setup instructions.

## Nice to Have: only after the demo is reliable

- Global shortcut.
- Voice activation and local speech-to-text.
- Push suggestions with a strict interruption policy.
- Approved-directory filesystem events.
- Work-log export.
- Creative-work activity adapters.

## Post-Hackathon

- XPC or Unix socket hardening after threat-model review.
- Better episode segmentation and user correction flows.
- Local embedding or full-text retrieval only when SQLite search is insufficient.
- Multi-provider routing and model evaluation.
- Native notifications, calendar/task integrations, and richer retention controls.
- Sandboxed plugin APIs for applications.
- Cross-device synchronization designed around user-owned encrypted data.

## Dependency-ordered implementation plan

## Dependency list

### macOS

- macOS 14 or newer for the initial target; verify the exact deployment target against the selected Swift toolchain.
- Xcode and Swift 6.
- SwiftUI and AppKit from the public SDK.
- `NSWorkspace` and `NSRunningApplication` for active-application observation.
- Accessibility APIs for focused window metadata, only after user permission.
- App Sandbox and security-scoped bookmarks for approved directories if sandboxing is enabled.
- Screen Recording permission only for explicit screenshot capture.
- AVFoundation and Speech permission only for activated voice input.

### Python Core

- Python 3.11 or newer.
- SQLite, including FTS5 where available.
- A typed validation library such as Pydantic, or equivalent standard-library dataclasses plus validation.
- A small HTTP server framework such as FastAPI and an ASGI server, or a standard-library HTTP implementation if dependency minimization wins.
- An HTTP client with timeout support for the AMD endpoint.
- Pytest for unit and integration tests.

Pin versions in a lockfile or reproducible environment file. Keep the Core dependency graph small and do not add an agent framework, vector database, or browser automation library for the first slice.

### Phase 0: verify constraints

Confirm official AMD rules, model license, cloud access, macOS deployment target, and available credits. Record decisions in the repository.

### Phase 1: prove domain behavior locally

Implement typed entities for projects, sessions, events, contexts, episodes, captures, notes, tasks, memories, and decisions. Add SQLite migrations and repositories, deterministic event normalization, session-scoped episode grouping and queries, immediate capture persistence, exact retrieval, secretary commands, and tests using deterministic fixtures. This proves Observe -> Understand -> Remember -> Recall without cloud, UI, or synchronous inference uncertainty. AMD integration is not required to save or recall a capture; it is added in Phase 2 for semantic interpretation and assistance.

### Phase 2: connect AMD

Implement the provider protocol, AMD endpoint configuration, structured generation, timeouts, bounded prompts, metrics, and a deterministic fallback. Run one real semantic episode request and record diagnostics.

### Phase 3: add macOS observation

Build the menu-bar app, permission prompts, active-application collector, and localhost client. Keep the core usable from the CLI while the UI is developed.

### Phase 4: add the native presence

Implement the state machine and compact/expanded panel. Connect context, note, recall, and assist flows. Add privacy and diagnostics views.

### Phase 5: rehearse and harden

Run the complete 60-120 second demo from a clean setup, test provider failure and permission denial, verify no secrets or raw private data are logged, and prepare a fallback recording.

## Technical risks

- macOS Accessibility and Screen Recording permissions may make observation unavailable on a demo machine.
- AMD endpoint, ROCm, vLLM, model compatibility, or credits may fail near the event.
- Episode quality can be poor with sparse or noisy signals.
- Window titles and URLs can leak sensitive information.
- A transparent native panel can become visually distracting or fragile across macOS versions.
- Cloud latency can undermine the interaction loop.
- Session boundaries may be ambiguous when the app quits, sleeps, or the user returns after a long gap.
- Captures can remain unclassified or be converted twice without idempotent processing state and provenance.
- Session-linked queries can become inconsistent if associations are copied rather than modeled as foreign keys.

Mitigations are explicit start/end lifecycle rules, inactivity timeouts with user correction, idempotent capture conversion, foreign-key constraints, deterministic fixtures, explicit graceful degradation, bounded prompts, local storage, and a rehearsed provider fallback.
