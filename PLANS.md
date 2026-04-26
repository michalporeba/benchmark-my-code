# Product Delivery Plan

## Phase 1: Foundation & Tooling (Completed)
- [x] Migrate from Poetry to `uv`.
- [x] Set up `pytest` framework and baseline coverage.
- *See: `plans/01-uv-migration.md`*

## Phase 2: The Core Engine (Completed)
- [x] **2A: Core Statistics & Timers**: Implement robust measurement (medians over means, tracking min/max). *See: `plans/02a-core-statistics.md`*
- [x] **2B: Batch Execution & Convergence**: Implement warmups, batch chunking, and 1% stability convergence. *See: `plans/02b-batch-execution.md`*
- [x] **2C: Ad-Hoc Mode API**: Create `@benchit` decorators, handle multiple functions, and deep-copy inputs. *See: `plans/02c-adhoc-mode.md`*
- [x] **2D: Pluggable Output**: Build `BenchmarkResult` object, terminal CLI tables, and JSON export. *See: `plans/02d-pluggable-output.md`*

## Phase 3: Educational Features
- [x] **3A: Challenge API & Validation**: `@challenge` decorator, registry, and `inspect`-based signature checking. *See: `plans/03a-challenge-api.md`*
- [x] **3B: Reference Baselines & Adaptive Timeouts**: Executing hidden reference functions to set a performance ceiling. *See: `plans/03b-adaptive-timeouts.md`*
- [x] **3C: Staged Feedback & Guidance**: Mapping failures (timeout, correctness, Big-O) to specific student-friendly messages. *See: `plans/03c-pedagogical-feedback.md`*
- [x] **3D: Adaptive Memory Profiling**: `tracemalloc` integration that only samples at key intervals to sketch the curve. *See: `plans/03d-adaptive-memory.md`*
