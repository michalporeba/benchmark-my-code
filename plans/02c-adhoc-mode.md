# Plan: 02C - Ad-Hoc Mode API

## Objective
Create the user-facing API for frictionless exploration: the `@benchit` decorator and the `run_benchmarks()` entry point. The primary focus is maximum simplicity and Developer Experience (DX) for single-file scripts and notebooks.

## Architecture & Design Decisions
Based on product discussions, the API will adhere to the following principles:
1. **Global Registry**: We will use a hidden global registry (e.g., inside `__init__.py` or an `api.py` module). Users shouldn't need to instantiate classes to start benchmarking. The scope is assumed to be a single file/execution.
2. **Variant Naming**: For now, we rely on automatic string representations of the input variants. Custom naming is deferred to a future feature.
3. **Consistency vs. Correctness**: When `validate=True` is used without a known "reference" implementation or explicit expected results, the system will only check for **consistency**. If two functions return different results for the same input, the framework will report an "Inconsistent Outcomes" error, rather than guessing which one is "wrong."

## Target Developer Experience (DX)
```python
from benchmark_my_code import benchit, run_benchmarks

@benchit
def option_a(x, y):
   return x * y

@benchit
def option_b(x, y):
   result = 0
   for _ in range(y):
       result += x
   return result

if __name__ == '__main__':
    # Compares all functions registered via @benchit
    # validate=True ensures option_a and option_b return the exact same value for (1, 2) and (123, 43)
    run_benchmarks(variants=[(1, 2), (123, 43)], validate=True)
```

## Implementation Steps
1. **The Global Registry & Decorator (`api.py` or `__init__.py`)**:
   - Define a global list/set of registered functions.
   - Implement the `@benchit` decorator to append the wrapped function to this registry and return the original function unmodified.
   - Implement `run_benchmarks(variants, validate=False, **kwargs)` which iterates over the registry, runs the core engine logic (from `orchestrator.py`), and prints/returns the result.
2. **Deep Copying Inputs**:
   - Inside the execution loop (in `orchestrator.py`), use `copy.deepcopy()` on `args` and `kwargs` before passing them to the user's function. This ensures that if one function mutates a list or dictionary, it doesn't corrupt the variant for the next function.
3. **Consistency Validation**:
   - Implement logic in `run_benchmarks` (or within the orchestrator) to capture the return value of each function for the first non-warmup execution of a variant.
   - If `validate=True`, compare the return values of all registered functions for a given variant.
   - If they do not match, raise an `InconsistentOutcomesError` detailing which functions produced which differing outputs.
4. **Update Examples & Tests**:
   - Rewrite `examples/03_compare_implementations.py` to use the new `@benchit` and `run_benchmarks` API, proving the DX is improved.
   - Add unit tests proving that mutating inputs doesn't leak between functions.
   - Add unit tests proving that `validate=True` catches inconsistent return values.
