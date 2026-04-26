# Development Guide

This guide provides instructions for setting up the development environment, running tests, and following the project workflow.

## Prerequisites
- **Python**: 3.12 or higher
- **Package Manager**: [uv](https://github.com/astral-sh/uv) (Strict mandate)

## Setup
To install dependencies and set up the virtual environment:
```bash
uv sync
```

## Running Tests
We use `pytest` for all testing. Tests are located in the `tests/` directory.

### Run all tests
```bash
uv run pytest
```

### Run with coverage (if configured)
```bash
uv run pytest --cov=benchmark_my_code
```

## Code Quality & Style
We use `ruff` and `mypy` to enforce code standards.

### Linting and Formatting
```bash
uv run ruff check .
uv run ruff format .
```

### Type Checking
```bash
uv run mypy .
```

## Development Workflow
All feature development must follow the **Planner -> Implementer -> Reviewer** cycle as defined in `AGENTS.md`.

1.  **Planner**: Review `PLANS.md`, research existing code, and update a feature plan in `plans/`.
2.  **Implementer**: Write failing tests (`pytest`) first, then implement the minimal code to pass.
3.  **Reviewer**: Verify the implementation against `ADR.md` and project standards.

### Working with AI Agents
When using Gemini CLI, activate the relevant skills (e.g., `bmad-quick-dev` for small fixes, or the full BMM workflow for larger features). Always refer to `project-context.md` for critical implementation rules.
