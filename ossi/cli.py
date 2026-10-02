"""Command-line interface for OSSI Phase 1."""

import argparse
import json
import sys
from typing import Any, Dict, Optional

from .context import reconstruct_context
from .core import OssiCore
from .db import Database
from .fixtures import SESSION_FIXTURE
from .repository import Repository


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ossi", description="Local-first OSSI secretary core")
    parser.add_argument("--db", default="~/.ossi/ossi.db", help="SQLite database path")
    commands = parser.add_subparsers(dest="command", required=True)

    session = commands.add_parser("session")
    session_commands = session.add_subparsers(dest="session_command", required=True)
    start = session_commands.add_parser("start")
    start.add_argument("--project")
    start.add_argument("--root")
    status = session_commands.add_parser("status")
    status.add_argument("session_id", nargs="?")
    end = session_commands.add_parser("end")
    end.add_argument("session_id", nargs="?")
    end.add_argument("--summary")

    capture = commands.add_parser("capture")
    capture.add_argument("text")
    note = commands.add_parser("note")
    note.add_argument("text")
    recall = commands.add_parser("recall")
    recall.add_argument("query")
    commands.add_parser("context")
    commands.add_parser("today")
    commands.add_parser("privacy")
    forget = commands.add_parser("forget-session")
    forget.add_argument("session_id")
    fixture = commands.add_parser("fixture")
    fixture_commands = fixture.add_subparsers(dest="fixture_command", required=True)
    load = fixture_commands.add_parser("load")
    load.add_argument("--project", default="OSSI")
    return parser


def _json_default(value: Any) -> Any:
    if hasattr(value, "value"):
        return value.value
    if hasattr(value, "__dict__"):
        return value.__dict__
    raise TypeError("cannot serialize %r" % (value,))


def _print(value: Any) -> None:
    if isinstance(value, str):
        print(value)
    else:
        print(json.dumps(value, default=_json_default, indent=2, sort_keys=True))


def main(argv: Optional[list] = None) -> int:
    args = _parser().parse_args(argv)
    database = Database(args.db)
    repository = Repository(database)
    core = OssiCore(repository)
    try:
        if args.command == "session":
            if args.session_command == "start":
                _print(core.start_session(args.project, args.root))
            elif args.session_command == "status":
                session = repository.get_session(args.session_id) if args.session_id else repository.active_session()
                if session is None:
                    raise ValueError("no matching session")
                _print(session)
            elif args.session_command == "end":
                session_id = args.session_id or (repository.active_session().id if repository.active_session() else None)
                if session_id is None:
                    raise ValueError("no active session")
                _print(repository.end_session(session_id, args.summary))
        elif args.command == "capture":
            session = repository.active_session()
            _print(core.capture(args.text, session.id if session else None))
        elif args.command == "note":
            session = repository.active_session()
            _print(core.note(args.text, session.id if session else None))
        elif args.command == "recall":
            _print(core.recall(args.query))
        elif args.command == "context":
            session = repository.active_session()
            if session is None:
                raise ValueError("no active session")
            core.build_session_episodes(session.id)
            _print(core.current_context(session.id))
        elif args.command == "today":
            _print(core.today())
        elif args.command == "privacy":
            _print(repository.get_privacy())
        elif args.command == "forget-session":
            repository.forget_session(args.session_id)
            print("forgot %s" % args.session_id)
        elif args.command == "fixture" and args.fixture_command == "load":
            session = core.start_session(args.project)
            for raw in SESSION_FIXTURE:
                core.add_raw_event(raw, session.id, session.project_id)
            episodes = core.build_session_episodes(session.id)
            _print({"session": session, "episodes": episodes})
        return 0
    except (ValueError, KeyError) as exc:
        print("ossi: %s" % exc, file=sys.stderr)
        return 2
    finally:
        database.close()


if __name__ == "__main__":
    raise SystemExit(main())
