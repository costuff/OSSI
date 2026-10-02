# OSSI Privacy

## Default posture

OSSI is local-first and permission-gated. It must never use covert monitoring, keylogging, password capture, hidden microphone recording, unrestricted filesystem ingestion, silent destructive actions, or hidden uploads.

The user can pause observation, inspect current knowledge, delete a session, and change individual permissions.

## Initial perception matrix

| Signal | Default | Permission/API | Retention |
| --- | --- | --- | --- |
| Active application | On after consent | NSWorkspace / NSRunningApplication | Semantic event only |
| Active window title | Ask | Accessibility / focused UI element | Short-lived, sanitized |
| Approved project directory | Ask | User-selected security-scoped bookmark | File metadata only initially |
| Explicit screenshots | Off | Screen Recording permission, user action | Do not retain by default |
| Terminal events | Off initially | Explicit integration or user command | Selected semantic event |
| Browser history | Off | No access in MVP | None |
| Clipboard | Off | No access in MVP | None |
| Keyboard content | Off | Never collect | None |
| Microphone | Off | AVAudioSession / speech permission | Audio is transient; transcript only after activation |

Window titles and event text are potentially sensitive. Sanitize secrets, tokens, URLs containing credentials, and common credential-shaped strings before persistence or inference. Do not claim sanitization is perfect; show the user what is selected for upload.

## Knowledge and provenance

Every retained item has a source such as `explicit_user`, `observed_context`, `assistant_inference`, `imported_document`, or `system_event`. Explicit notes and confirmed decisions must not be silently merged with model inferences. Inferences require confidence and supporting source IDs.

## Data leaving the computer

By default, raw events, screenshots, clipboard contents, keyboard content, and full files stay local. The AMD provider receives only the selected semantic context needed for the requested operation, plus bounded metadata such as project name and time range. The UI must expose the outgoing fields before a user-requested upload when practical.

## Retention

- Raw events: short retention, configurable, and deleted after episode extraction.
- Semantic events: medium retention within the active session or project.
- Episodes: retained only when useful or explicitly saved.
- Notes, tasks, and confirmed decisions: persistent until deleted or completed.
- Inferences: retained with provenance only when they produce useful, user-visible memory.

## Permission implementation

Use `NSWorkspace` for application activation notifications. Use Accessibility APIs only after the user grants Accessibility permission and only for the selected window metadata. Use App Sandbox entitlements and security-scoped bookmarks for approved directories if the app is sandboxed. Use Screen Recording and microphone permissions only for explicit features, with visible status and activation affordances.
