# OSSI Demo

## Primary 60-120 second story

1. Start on the normal macOS desktop with the small OSSI presence visible but untouched.
2. Work normally in VS Code on the OSSI AMD provider.
3. Run a test and show an authentication failure.
4. Open AMD documentation, return to VS Code, inspect a configuration file, and run the test again.
5. Activate OSSI and ask: "What am I doing?"
6. OSSI reconstructs the current activity from permitted context: the project, recent application changes, test failure, and documentation investigation.
7. Ask: "What do you think I'm stuck on?"
8. AMD-backed semantic reasoning identifies the likely authentication configuration issue and shows provider, model, request ID, latency, and token diagnostics.
9. Ask: "Remember this for tomorrow."
10. OSSI stores the raw capture locally and immediately confirms it without waiting for AMD.
11. Begin a later session and ask: "Where did I leave off?"
12. OSSI reconstructs the previous session, unresolved issue, and explicit user capture.
13. Briefly show the privacy view, then stop. The user remains responsible for making the fix.

## What the audience must understand

The user worked normally before interacting with OSSI. OSSI reconstructed the situation from permitted context, used AMD inference for meaningful interpretation, captured the user's words locally without cloud inference, and kept the human responsible for action.

## Demo data contract

Use a seeded fixture or real session containing:

- project: `OSSI`
- activity: editing and testing the AMD provider
- problem: authentication failure
- resource: AMD documentation
- explicit capture: remember to investigate streaming reconnect handling tomorrow
- next step: verify the endpoint configuration

The fixture must be clearly labeled if used. Do not present simulated events as live observation.

## Failure choreography

- If AMD is unreachable, show the provider status and use a deterministic local response; explain that the live AMD call was rehearsed separately.
- If permissions are denied, show the privacy state and use explicit CLI or fixture events.
- If the model returns malformed JSON, reject it, log the validation failure, and display a concise fallback.
- If context is ambiguous, OSSI should say it is uncertain and ask the user rather than inventing a work episode.
- If the capture path is slow, treat it as a product failure: local persistence must complete before any optional classification.

## Judging evidence

Show, in order:

- the user-facing context-aware result;
- the AMD provider, model, and request metrics;
- the permission matrix and outbound-context boundary;
- the stored note with provenance;
- the same system adapting to a different activity.

## Smallest end-to-end slice

The smallest reliable slice is a Python CLI with SQLite and one provider call:

1. Insert a handful of normalized events for an OSSI debugging session.
2. Build a current context and episode locally.
3. Send only the semantic context to `AMDProvider.structured_generate`.
4. Store the returned episode summary with provenance and metrics.
5. Run `ossi note ...`.
6. Run `ossi recall ...` and return the note plus episode context.

This slice proves the product thesis before macOS UI, voice, screenshots, or autonomous actions are introduced.
