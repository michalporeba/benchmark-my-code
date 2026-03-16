# Gemini CLI Workspace Instructions

## Core Mandates
- **Package Manager**: We strictly use `uv`. Do NOT use `poetry` or `pip` directly.
- **Testing**: We use `pytest`. Maintain high test coverage. Always write tests for new features.
- **Architecture**: Consult `ADR.md` for technical decisions regarding the benchmarking engine.
- **Task Management**: Always read `PLANS.md` before starting a task. Follow the workflows in `AGENTS.md`.
- **Memory**: Use `MEMORY.md` as a persistent scratchpad for context between sessions.
