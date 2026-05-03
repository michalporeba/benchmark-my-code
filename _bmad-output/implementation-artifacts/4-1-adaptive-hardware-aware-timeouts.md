# Story 4.1: Adaptive Hardware-Aware Timeouts

Status: review

## Story

As an educator,
I want the engine to secretly run a reference implementation to establish a hardware-specific baseline time,
so that my student timeouts are fair and adaptive, regardless of whether they run on a slow laptop or a fast server.

## Acceptance Criteria

1. **Given** a `@challenge` that defines a `reference` function and a `timeout_multiplier`
   **When** the challenge is executed
   **Then** the engine securely executes the reference function first for each variant.
2. **And** it sets the absolute timeout for the student's code to `(reference_median * timeout_multiplier)`.
3. **And** it handles reference implementation failures (timeouts/exceptions) by providing a specific "Baseline Failure" error instead of continuing with arbitrary timeouts.
4. **And** the orchestration logic for challenges is decoupled from `api.py` and moved into a dedicated `Orchestrator` service or utility.

## Tasks / Subtasks

- [x] **Architectural Refactoring** (AC: 4)
  - [x] Move the challenge execution loop from `api.py:run_benchmarks` to a new `orchestrator.py:run_challenge` or similar method.
  - [x] Ensure `api.py` remains focused only on registration and high-level result presentation.
- [x] **Hardened Baseline Calculation** (AC: 1, 2, 3)
  - [x] Implement robust error triage for reference executions: distinguish between student failures and reference failures.
  - [x] Ensure the reference implementation itself has a reasonable "meta-timeout" to prevent the baseline establishment from hanging.
  - [x] Validate that the calculated `adaptive_timeout` has a sane floor (e.g., 1ms) but is strictly hardware-proportional.
- [x] **Correctness-by-Default Integration** (AC: 1)
  - [x] Ensure the reference implementation output is automatically used as the ground-truth for student output validation.
- [x] **Verification & Testing**
  - [x] Add a test case for "Malformed Reference" (one that crashes) to ensure the engine fails gracefully.
  - [x] Add a test case for "Extremely Fast Reference" to verify the safety floor.
  - [x] Verify that multipliers < 1.0 correctly fail even perfect implementations (to test limit-enforcement).

## Dev Notes

### Architecture Patterns and Constraints
- **Separation of Layers**: Keep `api.py` thin. All timing and execution logic belongs in `orchestrator.py`.
- **Statelessness**: Challenge state should not persist across `run_benchmarks` calls unless explicitly intended.
- **Mutation Safety**: Always `deepcopy` variants for both reference and student code.

### Source Tree Components to Touch
- `benchmark_my_code/api.py`: Remove heavy loop logic, call orchestrator instead.
- `benchmark_my_code/orchestrator.py`: Implement `run_challenge` or equivalent logic.
- `benchmark_my_code/model.py`: Ensure `FailureType` supports "BASELINE_FAILURE" or similar if needed.

### References
- [Source: benchmark_my_code/api.py#L290] (Current fragile challenge loop)
- [Source: benchmark_my_code/orchestrator.py] (Core engine)
- [Source: ADR-007-Scenario-Discovery.md] (Naming as contract and reference marking)

## Dev Agent Record

### Agent Model Used
Gemini 2.0 Flash

### Debug Log References
- Fixed `bench()` call in `run_challenge` to filter out `print_results` and other unsupported kwargs.
- Fixed `student_variants` format to be compatible with `normalised_variants`.
- Discovered and fixed a bad test case where student output accidentally matched the reference.

### Completion Notes List
- Refactored challenge orchestration from `api.py` to `orchestrator.py:run_challenge`.
- Introduced `FailureType.BASELINE_FAILURE` for explicit reporting of reference crashes.
- Implemented `BASELINE_FLOOR` (1ms) and `REFERENCE_META_TIMEOUT` (5s) for robust baseline establishment.
- Integrated automatic ground-truth extraction from reference implementations.

### File List
- `benchmark_my_code/api.py` (Update)
- `benchmark_my_code/orchestrator.py` (Update)
- `benchmark_my_code/model.py` (Update)
- `tests/test_adaptive_timeouts_hardened.py` (New)
