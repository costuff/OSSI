# Hackathon Requirements

## Verified official requirements

No official hackathon brief, judging rubric, credentials, or deployment configuration is present in this repository. There are currently no repository-verified official requirements.

The following must be confirmed against the official AMD Developer Hackathon ACT III source before submission:

- official track name and eligibility;
- deadline, deliverables, judging criteria, and required disclosures;
- permitted AMD services, models, licenses, and deployment configurations;
- rules governing credits, data handling, and third-party services.

## Project assumptions / design targets

The supplied OSSI product brief identifies the target as **Track 4 - Create a New Kind of Experience**. That is a project target, not a verified official requirement until a source is added.

## Must demonstrate

- A user-visible experience beyond a conventional chat window.
- Meaningful AMD inference, not merely AMD-hosted development.
- A real context-to-assistance workflow.
- Contextual memory across sessions.
- Human agency: suggestions and confirmations precede consequential actions.
- Visible privacy controls and a clear account of what leaves the machine.
- Reproducible setup without committed credentials.

## AMD integration

Deploy an open-weight model behind an OpenAI-compatible server such as vLLM on AMD Developer Cloud using ROCm and an AMD Instinct GPU, subject to current platform support. `AMDProvider` sends semantic context for at least one meaningful workload: episode interpretation, contextual assistance, or work-summary generation.

The demo must show the provider and model being used, for example through a diagnostics panel containing provider, model, request count, token counts, latency, and failures. Never fabricate dollar cost. If the platform exposes actual usage, record it separately.

## Credit discipline

- Use a small model and bounded prompts.
- Cache or reuse summaries where appropriate.
- Do not send raw screenshots or full files by default.
- Add request timeouts, retries with a limit, and a disabled-provider fallback.
- Provide a CLI diagnostics command before the demo.

## Compliance checks before submission

1. Confirm the official track name, deadline, deliverables, and AMD service rules.
2. Confirm that the chosen model and license are permitted.
3. Confirm cloud, API, and data handling terms.
4. Confirm the demo clearly identifies AMD inference.
5. Confirm all secrets are environment variables or hosted secret configuration.
6. Capture a reproducible deployment and a short fallback demo recording.

## Demo acceptance test

From a clean machine, a reviewer can start Core, configure a provider, generate a semantic episode from a small event sequence, create a note, recall it, inspect privacy state, and see inference diagnostics. The UI then demonstrates the same flow through the native presence.
