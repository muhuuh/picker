# Agent Memory Item Template

Use this template for new operational memory entries in `agents/memory/`.

```text
- id:
- date: YYYY-MM-DD
- type: semantic | episodic | procedural | source_quality | evaluation
- scope: orchestrator | provider | financial | news | sentiment | writer | global
- status: active | superseded | deprecated | needs_review
- confidence: low | medium | high
- trigger/source:
- lesson:
- use_when:
- do_not_use_when:
- evidence:
- owner:
- next_review: YYYY-MM-DD
```

Rules:

- Keep the lesson short and actionable.
- Link to evidence packets, traces, docs, tests, or a user correction.
- Do not store raw provider output.
- Do not store secrets.
- Do not store company facts unless the lesson is about source quality or workflow behavior.
- Prefer updating an existing entry over adding a duplicate.
