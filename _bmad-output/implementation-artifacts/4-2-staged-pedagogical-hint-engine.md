# Story 4.2: Staged Pedagogical Hint Engine

Status: ready-for-dev

## Story

As a student,
I want to receive specific, actionable hints when my code fails on certain edge cases or large datasets,
so that I understand why my code failed, rather than just seeing a generic timeout or failure message.

## Acceptance Criteria

1. **Given** a `@challenge` with defined stages (e.g., "Small Data", "Large Data", "Edge Cases") and associated hints
2. **When** my code fails or times out during a specific stage
3. **Then** the output automatically displays the corresponding pedagogical hint from the challenge configuration (addressing UX-DR3)

## Tasks / Subtasks

- [x] Enhance `FailureType` and `Function` model (AC: #2)
  - [x] Add `_exceptions` map to `Function` to store execution errors.
  - [x] Update `record_exception` and `merge` to preserve exception data.
- [x] Implement Smart Hint Engine in `orchestrator.py` (AC: #1, #2)
  - [x] Implement multi-level lookup: `(stage, variant, status) -> (stage, status) -> (variant, status) -> (None, status) -> (stage, None)`.
  - [x] Add support for hint templates using `{actual}`, `{expected}`, `{variant}`, and `{exception}` placeholders.
- [x] Integrate Hints into `BenchmarkResult` (AC: #3)
  - [x] Update `BenchmarkResult.stats` to include variants that failed before any successful executions.
  - [x] Truncate long variant labels in feedback and tables for readability.
- [x] Validation (AC: #1, #2, #3)
  - [x] Create `tests/test_pedagogical_feedback.py` covering all ACs and new template features.

## Dev Notes

- **Model Layer**: `benchmark_my_code/model.py` now stores exceptions per variant.
- **Orchestration Layer**: `run_challenge` in `benchmark_my_code/orchestrator.py` is the primary engine for hint selection.
- **Presentation Layer**: `benchmark_my_code/result.py` handles truncation and display of hints.
- **Testing**: Use `uv run pytest tests/test_pedagogical_feedback.py` to verify.

### Project Structure Notes

- `Function` model extension is backward compatible.
- `BenchmarkResult` truncation improves CLI UX without breaking data exports.

### References

- [Source: docs/architecture.md#API Layer]
- [Source: plans/03c-pedagogical-feedback.md]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.2]

## Dev Agent Record

### Agent Model Used

Gemini 2.0 Flash (via Gemini CLI)

### Debug Log References

- Verified truncation of 100-element list variant labels.
- Verified hint template resolution for `CORRECTNESS` and `EXCEPTION` failures.

### Completion Notes List

- Implementation is complete and verified with 61/61 passing tests.

### File List

- `benchmark_my_code/model.py`
- `benchmark_my_code/orchestrator.py`
- `benchmark_my_code/result.py`
### Review Findings

- [x] [Review][Patch] Fragile correctness validation logic [benchmark_my_code/api.py, benchmark_my_code/orchestrator.py]
- [x] [Review][Patch] Hint template formatting fragility [benchmark_my_code/orchestrator.py:373-385]
- [x] [Review][Patch] Debug remnants in production code [benchmark_my_code/orchestrator.py]
- [x] [Review][Patch] Infinite generator hangs in `run_challenge` and `_to_args_kwargs` [benchmark_my_code/orchestrator.py]
- [x] [Review][Patch] Unreadable hints due to `repr()` on large objects [benchmark_my_code/orchestrator.py:382-384]
- [x] [Review][Patch] Order-dependent status merging in `model.py` [benchmark_my_code/model.py:167-171]
- [x] [Review][Patch] Fixed truncation limits for variant labels [benchmark_my_code/result.py]
