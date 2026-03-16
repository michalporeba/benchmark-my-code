# Plan: 02A - Core Statistics & Timers

## Objective
Establish a reliable mathematical foundation for the benchmarking engine using robust statistics (Medians) and high-resolution timers.

## Context
Currently, the codebase uses simple arithmetic means which are easily skewed by OS background noise. We need to upgrade the `Function` and `Benchmark` models to store execution times efficiently and calculate medians, minimums, maximums, and variances.

## Steps
1. **Update Data Models (`model.py`)**: 
   - Replace arithmetic mean calculations with `statistics.median`.
   - Ensure the internal storage of execution times for variants can efficiently handle large arrays of floats.
2. **Timer Accuracy**:
   - Verify `time.perf_counter_ns()` or `time.perf_counter()` is used correctly for high-resolution timing.
3. **Tests**:
   - Write `pytest` unit tests simulating arrays of execution times (with injected outliers) to prove the median is correctly calculated and ignores the outliers.
