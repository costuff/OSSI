"""Typed Phase 1 domain entities."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SessionStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"


class CaptureState(str, Enum):
    CAPTURED = "captured"
    CLASSIFIED = "classified"
    CONVERTED = "converted"
    ARCHIVED = "archived"


class TaskStatus(str, Enum):
    OPEN = "open"
    COMPLETED = "completed"
    DELETED = "deleted"


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    root_path: Optional[str]
    created_at: str


@dataclass(frozen=True)
class Session:
    id: str
    started_at: str
    ended_at: Optional[str]
    project_id: Optional[str]
    status: SessionStatus
    summary: Optional[str]


@dataclass(frozen=True)
class Event:
    id: str
    kind: str
    occurred_at: str
    application: Optional[str]
    window_title: Optional[str]
    project_id: Optional[str]
    payload: Dict[str, Any]
    source: str
    retention_class: str
    session_id: Optional[str]


@dataclass(frozen=True)
class Context:
    project_id: Optional[str]
    session_id: Optional[str]
    activity: Optional[str]
    goal: Optional[str]
    active_application: Optional[str]
    signals: List[str]
    observed_from: Optional[str]
    observed_until: Optional[str]
    confidence: float


@dataclass(frozen=True)
class Episode:
    id: str
    start_at: str
    end_at: Optional[str]
    project_id: Optional[str]
    session_id: Optional[str]
    activity: Optional[str]
    goal: Optional[str]
    summary: Optional[str]
    problems: List[str]
    decisions: List[str]
    resources: List[str]
    unfinished: List[str]
    confidence: Optional[float]
    provenance_event_ids: List[str]


@dataclass(frozen=True)
class Capture:
    id: str
    raw_text: str
    created_at: str
    project_id: Optional[str]
    session_id: Optional[str]
    source: str
    processing_state: CaptureState
    converted_entity_id: Optional[str]


@dataclass(frozen=True)
class Note:
    id: str
    content: str
    created_at: str
    project_id: Optional[str]
    episode_id: Optional[str]
    session_id: Optional[str]
    tags: List[str]
    source: str
    deleted_at: Optional[str]


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    status: TaskStatus
    created_at: str
    due_at: Optional[str]
    project_id: Optional[str]
    episode_id: Optional[str]
    session_id: Optional[str]
    source: str


@dataclass(frozen=True)
class Memory:
    id: str
    content: str
    kind: str
    source: str
    confidence: Optional[float]
    created_at: str
    project_id: Optional[str]
    episode_id: Optional[str]
    session_id: Optional[str]
    source_ids: List[str]
    deleted_at: Optional[str]


@dataclass(frozen=True)
class Decision:
    id: str
    statement: str
    confirmed_at: str
    project_id: Optional[str]
    episode_id: Optional[str]
    session_id: Optional[str]
    source: str
    supersedes_id: Optional[str]


@dataclass(frozen=True)
class PrivacyState:
    active_application: bool = True
    window_title: bool = False
    project_directory: bool = False
    screenshots: bool = False
    clipboard: bool = False
    browser_history: bool = False
    keyboard_content: bool = False
    microphone: bool = False


@dataclass(frozen=True)
class InferenceRun:
    id: str
    provider: str
    model: str
    request_id: str
    started_at: str
    completed_at: Optional[str]
    latency_ms: Optional[int]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    success: bool
    error_class: Optional[str]
