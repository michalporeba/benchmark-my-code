# ADR 7: Scenario-Based Discovery and "Pytest-Feel" Ergonomics

## Context
The goal of `benchmark-my-code` is to provide a "zero-config algorithmic playground" for educational use. Users should be able to write an algorithm and its data provider in a single file and have them link automatically. Additionally, the engine must support structured challenges from the `Through The Coding Glass` (T2CG) library.

## Decision: Naming as Contract
We will implement a robust "Naming as Contract" discovery mechanism that links function parameters to data providers.

### 1. Robust Frame Discovery
Replace hardcoded `sys._getframe(2)` with a `find_user_frame()` utility. This utility walks the stack backwards until it finds the first frame that does **not** belong to the `benchmark_my_code` package. This ensures the engine finds user variables even when called through wrappers (CLI, T2CG, etc.).

### 2. Scenario Generators
Providers should be implemented as generators where each `yield` represents one benchmarking scenario. 
To support validation and multi-parameter functions, we adopt a tuple-based yielding convention:

*   **Single Parameter**: `yield (input, expected_output)`
*   **Multiple Parameters**: `yield ((arg1, arg2, ...), expected_output)`
*   **Keyword Parameters**: `yield ({"a": 1, "b": 2}, expected_output)` (Supported in a later phase)

The engine will automatically detect if the yielded value is a tuple of length 2. If so, it treats the first element as the input(s) and the second as the "Ground Truth" for correctness validation.

### 3. Polymorphic `@benchit` Decorator
The `@benchit` decorator is the primary entry point. It will support:
*   **Ad-hoc Magic**: `@benchit` (no params) looks for a provider matching the parameter name in the user's scope.
*   **Explicit Provider**: `@benchit(using=my_custom_generator)` explicitly links to a specific generator.
*   **Curriculum Integration**: `@benchit(using=Sorting.LEVEL_1)` where `LEVEL_1` is a `Challenge` object from T2CG.
*   **Reference Marking**: `@benchit(is_reference=True)` marks a function as the baseline for timing and correctness for other functions in the same session.

### 4. Correctness by Default
Correctness validation is no longer an "optional flag" for `run_benchmarks`. If a provider yields `(input, expected)`, or if an `is_reference` function exists, the engine **always** validates the student's output against the ground truth.

## Rational
This design maximizes developer ergonomics (the "fun" factor) while providing a professional-grade bridge to structured learning content. It avoids the "hostage situation" of complex configurations while ensuring that " Maya" (our student persona) gets immediate, high-signal feedback on both speed and correctness.

## Status
Approved for implementation.
