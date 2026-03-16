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
