# Plan: 02D - Pluggable Output

## Objective
Design the output layer to be flexible, supporting programmatic use, CLI tables, and future data-science exports without forcing heavy dependencies.

## Context
Currently, the codebase returns a bare `Benchmark` object or relies on raw `print()` statements in the example files to show results. We need a rich, unified `BenchmarkResult` object returned by `run_benchmarks()` that knows how to format itself beautifully for the terminal, and can be exported cleanly.

## Proposed Design Decisions
1. **The `BenchmarkResult` Object**:
   - `run_benchmarks` currently returns the `Benchmark` object from `model.py`. We will leave `Benchmark` as the internal data model, but wrap it in or convert it to a `BenchmarkResult` object that is tailored for presentation.
2. **Terminal Formatting (`__str__` or `.show()`)**:
   - We want a clean ASCII table.
   - *Constraint*: We do not want to add external dependencies like `rich` or `tabulate` to the core project if we can avoid it, to keep the package lightweight. We will implement a simple text-alignment formatter using standard Python f-strings.
3. **Data Export Hooks**:
   - Add `.to_dict()`: Converts the stats into a simple dictionary for JSON serialization.
   - Add `.to_dataframe()`: A method that attempts to `import pandas`. If Pandas is installed in the user's environment, it returns a DataFrame. If not, it raises an `ImportError` instructing them to `pip install pandas`.

## Implementation Steps
1. **Create `benchmark_my_code/result.py`**:
   - Define `BenchmarkResult`. It should take the raw `Benchmark` model and extract the necessary stats (function names, variants, executions, medians, mins, maxes).
2. **Implement CLI Formatting**:
   - Add a method to `BenchmarkResult` that dynamically calculates column widths based on the function names and variant names to draw a neat ASCII table.
3. **Implement Export Methods**:
   - `to_dict()`
   - `to_dataframe()` (with lazy import).
4. **Update `orchestrator.py` / `api.py`**:
   - Make `run_benchmarks` return `BenchmarkResult` instead of the raw `Benchmark` object.
5. **Update Examples & Tests**:
   - Remove the manual `print()` loops in `examples/01_single_function.py` and `examples/03_compare_implementations.py` and replace them with `print(result)`.
   - Write tests in `tests/test_output.py` verifying the JSON structure and the pandas lazy-import behavior.

## Questions for the User
Before I implement this, please let me know:
1. Are you happy with a custom, zero-dependency ASCII table, or would you prefer I add a library like `rich` to `pyproject.toml` to make the output colorful and fancy?
2. Should `run_benchmarks()` automatically print the table to the terminal, or should it only return the object (requiring the user to `print(result)`)?
