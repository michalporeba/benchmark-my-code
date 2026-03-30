# Architecture Decision Records (ADR)

This document outlines the technical decisions, internal algorithms, and design philosophy behind `benchmark-my-code`.

## ADR 1: Achieving Reliable Timing Results
* **Context**: Operating systems are noisy. A single execution or a simple mean average is heavily skewed by background tasks and JIT compilation.
* **Decision**: Implement a batch-based execution engine with statistical convergence.
    * **Warmups**: Discard the first batch of executions to account for runtime optimizations (like JIT or CPU caching).
    * **Medians over Means**: Use medians for statistical calculations to drop extreme environmental outliers.
    * **Convergence**: Calculate the median of rolling batches. If the median changes by `< 1%`, consider the results stable and stop early to save time; otherwise, continue up to a maximum limit.

## ADR 2: Adaptive Memory Profiling
* **Context**: Memory analysis (`tracemalloc`) adds significant overhead, slowing down time profiling and skewing results if run simultaneously.
* **Decision**: Decouple memory and time profiling. Establish time stability first. For single inputs, run memory profiling a limited number of times (1-3). For scaling inputs ($O(n)$ curves), intelligently sample memory only at the start, end, and specific intervals to sketch trends without massive overhead.

## ADR 3: Educational Safety & Fairness
* **Context**: In learning environments, users often write inefficient code (e.g., $O(n^3)$ infinite loops) or accidentally mutate data, which can crash systems or corrupt subsequent tests.
* **Decision (Mutation)**: Always deep-copy input variants before passing them to test functions. This prevents an in-place sort from pre-sorting the array for the next function being benchmarked.
* **Decision (Timeouts)**: Implement strict, absolute timeouts to prevent system hangs. In Challenge Mode, calculate these timeouts relatively as a multiple of the hidden reference implementation's execution time, ensuring fairness for students on slower hardware.

## ADR 4: Pluggable Output & Dependency Management
* **Context**: We want rich visualizations (graphs) in Jupyter notebooks, but we do not want to force CLI users or CI pipelines to install heavy dependencies like `matplotlib` or `pandas`.
* **Decision**: The core engine returns a standard Python object (`BenchmarkResult`). It includes helper methods (e.g., `.to_dataframe()`) that dynamically import heavy data-science libraries only at runtime if they are available and requested.

## ADR 5: Separation of Engine and Pedagogical Framework (T2CG)
* **Context**: We want to support structured learning tracks, persistence (unlocking levels), and curriculum management. However, adding stateful persistence and lesson-path logic to the core benchmarking utility would make it heavy, opinionated, and less versatile for ad-hoc use.
* **Decision**: Draw a clear line of responsibility.
    * **`benchmark-my-code` (The Engine)**: Will remain a stateless, lightweight benchmarking utility. It handles timing, medians, safety, and contract enforcement.
    * **`Through The Coding Glass` (T2CG)**: A separate package will be built on top of the engine. It will handle persistence (`.bmc_history.json`), curriculum tracks, gamification (levels), and rich pedagogical content.
* **Consequence**: `benchmark-my-code` provides raw data and metadata (e.g., `FailureType`) that T2CG can use to manage the student's journey.
