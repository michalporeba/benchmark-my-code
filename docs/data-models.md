# Data Models

This document describes the internal data structures used by `benchmark-my-code`.

## Core Models

### `Function`
Represents a single function being benchmarked.
- **`name`**: The function's `__name__`.
- **`executions`**: A mapping of variant labels to lists of execution times (seconds).
- **`peak_memory`**: A mapping of variant labels to peak memory usage (bytes).
- **`status`**: A mapping of variant labels to `FailureType` enums.
- **Methods**:
    - `median_time(variant)`: Calculates the median time for a specific variant.
    - `check_convergence(variant, previous_median)`: Determines if the 1% stability threshold has been reached.

### `Benchmark`
A container for multiple `Function` objects, facilitating aggregate results.
- **`add_function(func)`**: Integrates execution data, merging it if the function already exists.

### `Challenge`
A pedagogical contract defining the constraints for a benchmarking exercise.
- **`name`**: Display name of the challenge.
- **`parameters`**: List of expected function parameter names.
- **`variants`**: Input data for the challenge.
- **`reference`**: A hidden reference implementation for correctness and adaptive timeout calculation.
- **`banned_calls`**: List of strings (e.g., `"sorted"`) that are forbidden via AST analysis.
- **`stages`**: A dictionary of staged variants for progressive difficulty.

## Enums

### `FailureType`
Indicates the result of a benchmark execution.
- **`NONE`**: Success.
- **`CORRECTNESS`**: Result did not match reference implementation.
- **`TIMEOUT`**: Execution exceeded the adaptive or absolute timeout.
- **`EXCEPTION`**: User code raised an unhandled exception.
- **`CONSTRAINT`**: User code used a forbidden algorithmic call.
