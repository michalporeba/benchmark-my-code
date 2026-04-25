# Gemini CLI Workspace Instructions

## Core Mandates
- **Package Manager**: We strictly use `uv`. Do NOT use `poetry` or `pip` directly.
- **Testing**: We use `pytest`. Maintain high test coverage. Always write tests for new features.
- **Architecture**: Consult `ADR.md` for technical decisions regarding the benchmarking engine.
- **Task Management**: Always read `PLANS.md` before starting a task. Follow the workflows in `AGENTS.md`.
- **Memory**: Use `MEMORY.md` as a persistent scratchpad for context between sessions.

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
