# Plan: 03C - Staged Feedback & Guidance

## Objective
Define "stages" within a Challenge (Small, Large, Edge Cases). Implement the feedback engine that maps specific failure types (e.g., "Timed out on large variant") to pedagogical hints.

## Context
A key USP is the framework acting as a mentor. Instead of just a "fail", we want to tell the student *why* it failed in a way that helps them learn (e.g., hinting at nested loops if they time out on large inputs).

## Steps
1. **Challenge Stages**:
   - Organize variants into stages (e.g., Stage 1: Basic correctness, Stage 2: Scaling/Efficiency, Stage 3: Edge cases).
2. **Failure Analysis**:
   - Track failure types: `CorrectnessFailure`, `TimeoutFailure`, `ExceptionFailure`.
3. **Hint Mapping**:
   - Create a mapping in the `Challenge` object that links a stage + failure type to a pre-authored string hint.
4. **Output Integration**:
   - Ensure the `BenchmarkResult` and terminal output display these hints prominently.
5. **Tests**:
   - Verify that failing a "Large Input" stage correctly displays the "Efficiency" hint.
   - Verify that failing on an empty list displays the "Edge Case" hint.
