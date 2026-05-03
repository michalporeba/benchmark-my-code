# Story 2.1: The benchit CLI runner & Discovery

Status: review

## Story

As a developer,
I want to execute benchmarks via a command-line tool (e.g., `benchit my_file.py`) without writing `run_benchmarks()` in my code,
so that my source files remain clean and focused solely on the implementations.

## Acceptance Criteria

1. **Given** a Python file containing functions decorated with `@benchit`
   **When** the `benchit` CLI command is run against the file
   **Then** the engine automatically discovers all decorated functions using AST or module introspection.
2. **And** it executes them without executing top-level scripts or requiring explicit entry-point boilerplate.
3. **And** it provides explicit status reporting, clearly differentiating "PENDING" from "PASS".

## Tasks / Subtasks

- [x] Enhance `benchit` CLI to support file and directory discovery (AC: 1)
  - [x] Implement `find_benchmarks(path)` that recursively finds `.py` files if a directory is provided.
- [x] Implement AST-based discovery to find decorated functions (AC: 1, 2)
  - [x] Parse target files with `ast` to identify functions with `@benchit` or `@challenge`.
  - [x] Ensure discovery does NOT trigger top-level side effects (AC: 2).
- [x] Improve Status Reporting in `run_benchmarks` and `BenchmarkResult` (AC: 3)
  - [x] Add a "PENDING" state to `FailureType` or a separate execution state.
  - [x] Update CLI output to show progress (e.g., "Running [function]...") before final results.
- [x] Refactor `cli.py` to use the new discovery mechanism (AC: 1, 2)
  - [x] Replace `exec_module` with a safer approach that only imports if needed or uses the AST findings to guide execution.

## Dev Notes

### Architecture Patterns and Constraints
- **Zero-Dependency Core**: The CLI should still work without `rich`, falling back to plain ASCII.
- **Statelessness**: The CLI should clear the registry between files or sessions.
- **Safety**: Ensure `sys.path` is handled correctly so local imports in the benchmarked file work.

### Source Tree Components
- `benchmark_my_code/cli.py`: Main CLI entry point.
- `benchmark_my_code/api.py`: `run_benchmarks` and registry management.
- `benchmark_my_code/model.py`: `FailureType` and `Function` status.
- `benchmark_my_code/result.py`: Reporting logic.

### Testing Standards
- Test with files that have side effects (e.g., `print("Hello")` at top level) to ensure they are NOT executed.
- Test with directory discovery.
- Test with both `@benchit` and `@challenge`.

### References
- [Source: benchmark_my_code/cli.py]
- [Source: benchmark_my_code/api.py]
- [Source: ADR-007-Scenario-Discovery.md]

## Dev Agent Record

### Agent Model Used
Gemini 2.0 Flash

### Debug Log References
- Fixed regression in `test_cli_file_not_found` due to error message change ("File" -> "Path").
- Verified side-effect suppression using a temporary file check in `tests/test_cli_side_effects.py`.

### Completion Notes List
- Implemented `find_benchmarks` with recursion and `ast` filtering to skip files without benchmarks.
- Implemented `load_benchmarks_safely` using `ast.parse` and `compile` to strip top-level script statements, ensuring zero side-effects on import.
- Added real-time progress indicators to `run_benchmarks` (e.g., "Benchmarking 'func'... DONE").
- Added `PENDING` status to `FailureType` and updated `BenchmarkResult` (terminal/rich/HTML) to support it.

### File List
- `benchmark_my_code/cli.py`
- `benchmark_my_code/api.py`
- `benchmark_my_code/model.py`
- `benchmark_my_code/result.py`
- `tests/test_cli.py`
- `tests/test_cli_discovery_internal.py`
- `tests/test_cli_side_effects.py`
