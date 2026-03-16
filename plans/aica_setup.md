# Project Setup for AI Coding Agent (AICA)

## Objective
Set up the workspace for success using Gemini CLI. This involves establishing standard conventions for AI collaboration (rules, workflows, memory, and task planning), transitioning the project to use `uv` instead of Poetry, and ensuring `pytest` is properly configured.

## Key Concepts for Gemini CLI
1. **`GEMINI.md`**: The supreme system prompt for the workspace. It instructs the agent on project-wide mandates (like using `uv` instead of `pip`).
2. **`AGENTS.md`**: Defines specific agent roles (e.g., Planner vs. Implementer) to keep tasks focused.
3. **`PLANS.md` & `plans/`**: A structured directory for roadmap and feature planning, allowing the agent to break down tasks before coding.
4. **`MEMORY.md`**: A local, git-ignored scratchpad that helps the agent persist context and intermediate findings across sessions or crashes.

## Implementation Steps

### 1. Update `.gitignore`
Add the AI memory files to the end of `.gitignore` so they aren't accidentally committed:
```text

# AI Agent Memory
MEMORY.md
memory.json
plans/
```
*(Note: Whether to commit `plans/` is optional, but often teams exclude them or keep them. We will keep `plans/` tracked as documentation, but ignore `MEMORY.md`).*

### 2. Create `GEMINI.md`
Create this file in the root to instruct future Gemini CLI sessions:
```markdown
# Gemini CLI Workspace Instructions

## Core Mandates
- **Package Manager**: We strictly use `uv`. Do NOT use `poetry` or `pip` directly.
- **Testing**: We use `pytest`. Maintain high test coverage. Always write tests for new features.
- **Architecture**: Consult `ADR.md` for technical decisions regarding the benchmarking engine.
- **Task Management**: Always read `PLANS.md` before starting a task. Follow the workflows in `AGENTS.md`.
- **Memory**: Use `MEMORY.md` as a persistent scratchpad for context between sessions.
```

### 3. Create `AGENTS.md`
Create a guide on how to interact with the project:
```markdown
# AI Coding Agent (AICA) Workflow

We use Gemini CLI for AI-assisted development. Use the following roles to keep the agent focused.

## 1. The Planner
**Prompt:** "Act as the Planner and plan the feature defined in X."
**Workflow:**
1. Review `PLANS.md` and any existing feature specs in `plans/`.
2. Do NOT write source code. Propose an implementation plan and update the relevant `plans/<feature>.md` file.
3. Ask for human approval before proceeding.

## 2. The Implementer
**Prompt:** "Act as the Implementer and execute the plan in `plans/<feature>.md`."
**Workflow:**
1. Read the approved plan.
2. Write tests (`pytest`) first.
3. Write the implementation, adhering strictly to `GEMINI.md` (e.g., using `uv`).
4. Run tests and ensure they pass. Provide a clear summary.

## 3. The Reviewer
**Prompt:** "Act as the Reviewer and check the recent changes."
**Workflow:**
1. Review changes against `ADR.md` and `GEMINI.md`.
2. Verify test coverage and suggest edge cases.
```

### 4. Create `PLANS.md` (The Roadmap)
```markdown
# Product Delivery Plan

## Phase 1: Foundation & Tooling (Current)
- [ ] Migrate from Poetry to `uv`.
- [ ] Set up `pytest` framework and baseline coverage.
- *See: `plans/01-uv-migration.md`*

## Phase 2: The Core Engine
- [ ] Implement robust statistical engine (medians, batches, convergence).
- [ ] Implement Ad-Hoc mode decorators (`@benchit`).
- [ ] Implement pluggable output (CLI tables, basic objects).
- *See: `plans/02-core-engine.md`*

## Phase 3: Educational Features
- [ ] Implement Challenge mode decorators and signature validation.
- [ ] Implement safety bounds (deep copy, adaptive relative timeouts).
- [ ] Implement adaptive memory profiling.
- *See: `plans/03-educational-features.md`*
```

### 5. Create First Feature Plan: `plans/01-uv-migration.md`
```markdown
# Plan: Migrate to uv and Pytest

## Objective
Replace Poetry with `uv` for significantly faster dependency management and set up a solid `pytest` foundation.

## Steps
1. Delete `poetry.lock`.
2. Use `uv init` or update `pyproject.toml` to use the `uv` build backend (like `hatchling` or `flit_core`).
3. Define `pytest` as a dev dependency via `uv add --dev pytest`.
4. Ensure `tests/test_simple_execution.py` can be executed cleanly via `uv run pytest`.
```

### 6. Initialize `MEMORY.md`
```markdown
# AI Agent Memory Scratchpad

*This file is ignored by Git. Use it to store temporary context, CLI commands, or pending thoughts between sessions.*

- **Current Status**: Project is being migrated to `uv`. 
- **Next Step**: Execute the plan in `plans/01-uv-migration.md`.
```

## Verification
- Verify `.gitignore` excludes memory.
- Verify all foundational markdown files are created.