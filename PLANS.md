# Product Delivery Plan

## Phase 1: Foundation & Tooling (Completed)
- [x] Migrate from Poetry to `uv`.
- [x] Set up `pytest` framework and baseline coverage.
- *See: `plans/01-uv-migration.md`*

## Phase 2: The Core Engine (Completed)
- [x] **2A: Core Statistics & Timers**: Implement robust measurement (medians over means, tracking min/max).
- [x] **2B: Batch Execution & Convergence**: Implement warmups, batch chunking, and 1% stability convergence.
- [x] **2C: Ad-Hoc Mode API**: Create `@benchit` decorators, handle multiple functions, and deep-copy inputs.
- [x] **2D: Pluggable Output**: Build `BenchmarkResult` object, terminal CLI tables, and JSON export.

## Phase 3: Educational Features (Completed)
- [x] **3A: Challenge API & Validation**: `@challenge` decorator, registry, and `inspect`-based signature checking.
- [x] **3B: Reference Baselines & Adaptive Timeouts**: Executing hidden reference functions to set a performance ceiling.
- [x] **3C: Staged Feedback & Guidance**: Mapping failures (timeout, correctness, Big-O) to specific student-friendly messages.
- [x] **3D: Adaptive Memory Profiling**: `tracemalloc` integration that only samples at key intervals.

## Phase 4: Hardening & DX (Completed)
- [x] **Story 1.1**: Efficient Median Selection (Quickselect) & Stat Hygiene.
- [x] **Story 1.2**: Single-Worker Executor with Stall Detection.
- [x] **Story 1.3**: Hygienic & Decoupled Memory Pass.
- [x] **Story 2.1**: `benchit` CLI Runner & Auto-Discovery.
- [x] **Story 2.2**: Pytest-Style Parametrization via Name Matching.
- [x] **Story 2.3**: Directed Acyclic Graph (DAG) Parameter Resolution.
- [x] **Story 3.1**: Lazy-Loaded Statistics for BenchmarkResult.
- [x] **Story 3.2**: Overhead-Free Optional Dependencies.
- [x] **Story 4.1**: Adaptive Hardware-Aware Timeouts.
- [x] **Story 4.2**: Staged Pedagogical Hint Engine.
