# Plan: 03D - Adaptive Memory Profiling

## Objective
Integrate `tracemalloc`. Implement the logic to decouple memory and time profiling, sampling memory at strategic boundaries (start, end, and specific intervals) to sketch a Big-O memory trend without significant time overhead.

## Context
Memory profiling is slow and can skew timing results. We should run it separately and sparingly.

## Steps
1. **`tracemalloc` Integration**:
   - Add utility to measure peak memory usage during a single function call.
2. **Sampling Strategy**:
   - Do NOT run memory profiling for every repetition in a batch.
   - Run it once per variant (after time stability is established).
   - If there are many variants (scaling inputs), intelligently sample (e.g., first, last, and $log(N)$ intervals) to sketch the memory curve.
3. **Data Storage**:
   - Update `model.py` to store these peak memory measurements alongside timing data.
4. **Tests**:
   - Test that memory profiling is correctly isolated from time profiling.
   - Verify that memory usage is correctly reported in the final result object.
