# Documentation Update: Product Vision and Architecture

## Objective
Revamp the project's documentation to clearly communicate the "Educational Benchmarking Framework" product vision. This involves updating `README.md` to act as an inviting "Front Door" (highlighting the USP, Ad-Hoc, and Challenge modes) and creating a new `ADR.md` (Architecture Decision Records) file to document the robust technical engine ensuring reliable, fair, and safe benchmarks.

## Key Files & Context
- `README.md`: Will be rewritten to focus on the product pitch, usage examples, and value proposition for educators and learners.
- `ADR.md`: A new file that will house the detailed technical decisions originally sketched out in the old README, expanded to cover our new architectural discussions.

## Implementation Steps

### 1. Rewrite `README.md`
Replace the current `README.md` content with the following:

```markdown
# benchmark-my-code

A robust, student-proof benchmarking framework designed for education. It bridges the gap between raw execution timing (like `timeit`) and complex profiling tools, providing a safe, statistically sound environment for comparing algorithmic approaches.

The module's objective is to support learning Python by making it easier to understand both the performance and correctness of code.

## Core Workflows

`benchmark-my-code` supports two main usage patterns:

### 1. Ad-Hoc Mode (Exploration & Comparison)
Designed for rapid iteration, comparing ideas, or demonstrating a concept with zero friction. You can easily compare multiple implementations using decorators.

```python
from benchmark_my_code import benchit, run_benchmarks

@benchit
def sum_using_string(number):
    return sum(int(digit) for digit in str(number))

@benchit
def sum_using_modulo(number):
    total = 0
    while number > 0:
        total += number % 10
        number //= 10
    return total

if __name__ == '__main__':
    # Run all registered functions against varying inputs.
    # validate=True ensures all implementations return the exact same result.
    run_benchmarks(
        variants=[(123,), (456789,), (1234567890,)], 
        validate=True 
    )
```

### 2. Challenge Mode (Structured Learning)
Designed for university settings or self-guided learning. A "Challenge" is provided by an external learning package and includes hidden reference implementations, test cases, and staged guidance.

```python
from benchmark_my_code import challenge
from bmc_cs101 import SortingChallenges

@challenge(SortingChallenges.sort_level_1)
def my_sort(input_list):
    return sorted(input_list)
```
In this mode, the framework acts as a mentor: it validates the function signature, prevents accidental cheating (e.g., modifying inputs in place), provides staged feedback, and scales absolute timeouts based on the reference implementation's performance to ensure fairness across different hardware.

## Features & Pluggable Output

* **Correctness Validation**: Benchmarks are useless if the code is wrong. The framework supports validating the output of functions, either against each other (consensus) or against a hidden reference.
* **Intelligent Profiling**: Memory analysis is slower than time profiling. The framework uses adaptive profiling: establishing time stability first, then strategically sampling memory to sketch Big-O trends.
* **Pluggable Output**: Outputs adapt to the environment: an object for programmatic use, a clean terminal table for CLI, data-frame ready structures for notebooks (matplotlib/seaborn) without forcing heavy dependencies, and JSON for automated grading systems.

*For details on how the engine achieves reliable results and handles safety, see [ADR.md](ADR.md).*
```

### 2. Create `ADR.md`
Create a new file named `ADR.md` in the repository root with the following content:

```markdown
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
```

## Verification & Testing
- Run `git status` to verify `ADR.md` is created and `README.md` is modified.
- Verify formatting and rendering of the markdown files.