# API Contracts

This document describes the public API for the `benchmark-my-code` library.

## Entry Points

### `run_benchmarks(variants=None, validate=False, print_results=True, **kwargs)`
Executes all functions registered via `@benchit` or `@challenge`.

- **`variants`**: (Optional) A dictionary of variants `{ "Name": (args,) }` or a list of argument tuples.
- **`validate`**: (bool) If `True`, ensures all registered functions return the same result for each variant.
- **`print_results`**: (bool) If `True`, prints the result table to stdout.
- **`**kwargs`**: Passed to the underlying `bench` orchestrator (e.g., `max_executions`, `warmup_executions`).
- **Returns**: `BenchmarkResult` object.

---

## Decorators

### `@benchit`
Registers a function for ad-hoc benchmarking.
- **Usage**:
  ```python
  @benchit
  def my_function(x, y):
      return x + y
  ```

### `@challenge(challenge_obj)`
Registers a function for a specific `Challenge`.
- **`challenge_obj`**: A `Challenge` instance defining the contract (parameters, variants, reference implementation).
- **Validation**: Performs signature and algorithmic constraint checks at registration time.
- **Usage**:
  ```python
  fib_challenge = Challenge(name="Fibonacci", parameters=["n"])
  
  @challenge(fib_challenge)
  def my_fib(n):
      ...
  ```

---

## Static Validation

### `validate_signature(func, expected_params)`
Verifies that the target function has the exact parameter names defined in the challenge.
- **Raises**: `InvalidSignatureError` if parameters don't match.

### `validate_algorithmic_constraints(func, banned_calls)`
Uses `ast` to scan the function's source code for forbidden built-ins or method calls.
- **Raises**: `ForbiddenCallError` if a banned call is detected.

---

## Utility Functions

### `clear_registry()`
Clears all currently registered ad-hoc and challenge functions. Useful for test isolation.
