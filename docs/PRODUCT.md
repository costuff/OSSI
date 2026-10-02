# OSSI Product

## Thesis

OSSI is a user-controlled intelligence layer for the computer. It observes permitted context, turns signals into useful understanding, remembers information with provenance, and assists when asked.

> Your computer has an operating system. OSSI gives it an intelligence.

OSSI augments human thinking. It does not replace the user's responsibility to think, create, decide, explore, learn, or work.

## The first user promise

The user should not need to repeatedly explain what they are doing. When they ask for help, OSSI should already understand the current project, recent activity, relevant problem, and useful prior notes within the scope the user has approved.

## Target users

- Developers moving between an editor, terminal, browser, and documentation.
- Creatives iterating across tools and versions.
- Knowledge workers who need continuity across work sessions.

## Core loop

1. **Observe** permitted application, window, project, and explicit user events.
2. **Understand** those events as semantic activity and work episodes.
3. **Remember** explicit notes, tasks, decisions, and selected useful episodes.
4. **Assist** concisely, with suggestions before actions and human confirmation where appropriate.

## Continuity and capture

A `Session` represents one period in which OSSI is observing or assisting. It connects related episodes and user records without duplicating their content. A frictionless `Capture` is the local inbox for raw user text such as "remember this idea"; it is persisted immediately and can later become a note, task, or memory.

This makes continuity explicit: OSSI can answer where the user left off, what happened during the last session, and which captures remain unprocessed without requiring inference for the initial save.

## Product boundaries

OSSI is not primarily a chat application, autonomous computer operator, covert monitor, keylogger, unrestricted file indexer, or replacement for the user's judgment. Raw context remains local by default. The user can inspect and forget what OSSI knows.

## Hackathon proof

The primary demo is a developer work episode: the user edits OSSI, runs a failing test, opens AMD documentation, returns to the editor, asks what is missing, and receives context-aware help without restating the situation. The user then records a note and recalls it in a later session.

The same interface should be able to describe a creative workflow without assuming it is software debugging. Context changes the assistance; the product identity does not.

## Success criteria

- Context is useful without requiring repeated explanation.
- Notes and episodes remain available across sessions.
- Explicit memory is distinguishable from inference.
- The user can see and control perception and retention.
- A real inference request runs through AMD infrastructure and is visible in the demo.
- OSSI assists rather than silently acting for the user.
