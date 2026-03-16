# Plan: 02B - Batch Execution & Convergence

## Objective
Implement the execution loop that chunks benchmark runs into batches, drops warmups, and stops early when results converge.

## Context
Running 1000 times straight is inefficient. We want to run a "warmup" batch (and discard results), then run subsequent batches. After each batch, we compare the rolling median to the previous median. If the change is < 1%, we stop early.

## Steps
1. **Implement Warmups (`orchestrator.py`)**:
   - Add a configurable warmup phase (e.g., run N times without recording data) to account for JIT and CPU caching.
2. **Batch Chunking**:
   - Modify the main loop to execute in batches (e.g., 10 runs per batch) rather than one-by-one.
3. **Convergence Logic**:
   - After each batch, calculate the new overall median.
   - If `abs((new_median - old_median) / old_median) < 0.01`, mark the variant as stable and break the loop.
4. **Tests**:
   - Create mock functions that simulate stable execution and verify the orchestrator stops early instead of running the max allowed executions.
