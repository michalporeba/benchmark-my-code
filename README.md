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
