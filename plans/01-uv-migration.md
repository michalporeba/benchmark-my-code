# Plan: Migrate to uv and Pytest

## Objective
Replace Poetry with `uv` for significantly faster dependency management and set up a solid `pytest` foundation.

## Context
Currently, the project uses `poetry` which is defined in `pyproject.toml` and `poetry.lock`. We want to transition to `uv` as the primary package manager and build frontend, while establishing `pytest` as the testing framework.

## Steps

### 1. Remove Poetry
- Delete `poetry.lock`.
- Remove poetry-specific configuration from `pyproject.toml`.

### 2. Initialize uv
- Update `pyproject.toml` to use a standard build backend supported by `uv` (e.g., `hatchling` or `flit_core`).
- Initialize `uv` workspace (if necessary) or simply generate a `uv.lock` by running `uv sync`.

### 3. Setup Dependencies
- Add required standard dependencies.
- Add `pytest` as a development dependency: `uv add --dev pytest`.

### 4. Validate Tests
- Run existing tests (e.g., `tests/test_simple_execution.py`) using `uv run pytest`.
- Verify tests pass or identify what needs fixing due to the new environment.
