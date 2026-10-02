"""Deterministic fixture for the first OSSI development session."""

SESSION_FIXTURE = [
    {"type": "application_changed", "application": "VS Code", "timestamp": "2026-10-02T09:00:00+00:00"},
    {"type": "application_changed", "application": "Terminal", "timestamp": "2026-10-02T09:03:00+00:00"},
    {"type": "test_failure", "application": "Terminal", "timestamp": "2026-10-02T09:04:00+00:00", "payload": {"error": "authentication failed"}},
    {"type": "application_changed", "application": "Browser", "timestamp": "2026-10-02T09:06:00+00:00"},
    {"type": "documentation_opened", "application": "Browser", "timestamp": "2026-10-02T09:08:00+00:00", "payload": {"topic": "AMD endpoint authentication"}},
    {"type": "application_changed", "application": "VS Code", "timestamp": "2026-10-02T09:12:00+00:00"},
]
