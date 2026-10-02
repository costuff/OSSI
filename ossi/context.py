"""Deterministic event normalization and context reconstruction."""

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from .domain import Context, Episode, Event
from .repository import new_id


APPLICATION_ACTIVITY = {
    "Visual Studio Code": "development",
    "VS Code": "development",
    "Terminal": "testing",
    "Google Chrome": "research",
    "Safari": "research",
    "Browser": "research",
}


def _timestamp(value: Optional[str]) -> str:
    if value is None:
        raise ValueError("event timestamp is required")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("event timestamp is malformed") from exc
    return value


def normalize_event(raw: Dict[str, Any], session_id: Optional[str], project_id: Optional[str] = None) -> Event:
    raw_type = raw.get("type")
    if not isinstance(raw_type, str) or not raw_type.strip():
        raise ValueError("event type is required")
    occurred_at = _timestamp(raw.get("timestamp"))
    application = raw.get("application")
    if application is not None and not isinstance(application, str):
        raise ValueError("application must be a string")
    payload = raw.get("payload", {})
    if not isinstance(payload, dict):
        raise ValueError("event payload must be an object")
    activity = APPLICATION_ACTIVITY.get(application or "")
    kind = raw_type.strip().lower()
    if kind == "application_changed" and activity:
        kind = "%s_activity" % activity
    elif kind in ("test_failed", "pytest_failure", "test_failure"):
        kind = "test_failure"
    elif kind in ("documentation_opened", "documentation_viewed"):
        kind = "documentation_viewed"
    return Event(
        id=str(raw.get("id") or new_id()),
        kind=kind,
        occurred_at=occurred_at,
        application=application,
        window_title=raw.get("window_title"),
        project_id=project_id,
        payload=payload,
        source=str(raw.get("source") or "observed_context"),
        retention_class=str(raw.get("retention_class") or "short"),
        session_id=session_id,
    )


def reconstruct_context(events: Iterable[Event]) -> Context:
    ordered = sorted(events, key=lambda event: (event.occurred_at, event.id))
    if not ordered:
        return Context(None, None, None, None, None, [], None, None, 0.0)
    applications = [event.application for event in ordered if event.application]
    latest = ordered[-1]
    activities = [APPLICATION_ACTIVITY[app] for app in applications if app in APPLICATION_ACTIVITY]
    if "test_failure" in [event.kind for event in ordered]:
        activity = "debugging"
        goal = "resolve the failing test"
    elif activities:
        activity = activities[-1]
        goal = None
    else:
        activity = latest.kind
        goal = None
    signals = []
    if applications:
        signals.append("application path: %s" % " -> ".join(applications))
    for event in ordered:
        if event.kind == "test_failure":
            signals.append("test failure observed")
        elif event.kind == "documentation_viewed":
            signals.append("documentation viewed")
    return Context(
        project_id=latest.project_id,
        session_id=latest.session_id,
        activity=activity,
        goal=goal,
        active_application=latest.application,
        signals=signals,
        observed_from=ordered[0].occurred_at,
        observed_until=latest.occurred_at,
        confidence=0.9 if len(ordered) >= 3 else 0.6,
    )


def group_events_into_episodes(events: Iterable[Event], gap_minutes: int = 30) -> List[Episode]:
    ordered = sorted(events, key=lambda event: (event.occurred_at, event.id))
    if not ordered:
        return []
    groups: List[List[Event]] = [[]]
    for event in ordered:
        if groups[-1] and _gap_minutes(groups[-1][-1].occurred_at, event.occurred_at) > gap_minutes:
            groups.append([])
        groups[-1].append(event)
    episodes = []
    for group in groups:
        context = reconstruct_context(group)
        problems = ["test failure"] if any(event.kind == "test_failure" for event in group) else []
        resources = [event.application for event in group if event.kind == "documentation_viewed" and event.application]
        unfinished = ["resolve the failing test"] if problems else []
        episodes.append(Episode(
            id=new_id(),
            start_at=group[0].occurred_at,
            end_at=group[-1].occurred_at,
            project_id=group[0].project_id,
            session_id=group[0].session_id,
            activity=context.activity,
            goal=context.goal,
            summary=_summary(context, problems, resources),
            problems=problems,
            decisions=[],
            resources=resources,
            unfinished=unfinished,
            confidence=context.confidence,
            provenance_event_ids=[event.id for event in group],
        ))
    return episodes


def _gap_minutes(left: str, right: str) -> float:
    start = datetime.fromisoformat(left.replace("Z", "+00:00"))
    end = datetime.fromisoformat(right.replace("Z", "+00:00"))
    return (end - start).total_seconds() / 60.0


def _summary(context: Context, problems: List[str], resources: List[str]) -> str:
    summary = "Activity: %s." % (context.activity or "unknown")
    if problems:
        summary += " Problem: %s." % ", ".join(problems)
    if resources:
        summary += " Resources: %s." % ", ".join(resources)
    return summary
