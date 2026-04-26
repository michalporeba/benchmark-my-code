# Source Tree Analysis

This document provides a breakdown of the `benchmark-my-code` directory structure and the purpose of its key components.

## Project Structure

```
benchmark-my-code/
├── benchmark_my_code/   # Core engine logic (Part: Core Library)
│   ├── api.py           # Public entry points (@benchit, @challenge, run_benchmarks)
│   ├── orchestrator.py  # Execution engine (timing, convergence, batches)
│   ├── model.py         # Data models (Benchmark, Function, Challenge)
│   ├── result.py        # Presentation logic (CLI tables, Notebook HTML)
│   └── config.py        # Default engine configurations
├── tests/               # Test suite (pytest)
│   ├── test_api_adhoc.py
│   ├── test_challenge_api.py
│   ├── test_model_statistics.py
│   └── ...
├── examples/            # Usage examples for various scenarios
│   ├── 01_single_function.py
│   ├── 04_challenge_mode.py
│   └── ...
├── demos/               # Simple standalone demo scripts
├── docs/                # Project documentation (this folder)
├── plans/               # Feature implementation plans
├── ADR.md               # Architecture Decision Records
├── AGENTS.md            # AI Agent workflow definitions
├── GEMINI.md            # Workspace-specific instructions
└── pyproject.toml       # Build system and dependency configuration
```

## Key Directory Descriptions

### `benchmark_my_code/`
The heart of the benchmarking engine.
- **`api.py`**: Provides the decorators and high-level functions that users interact with.
- **`orchestrator.py`**: Handles the actual execution of functions, including warmup, batching, and early convergence logic.
- **`model.py`**: Defines the classes used to store benchmark data and challenge metadata.
- **`result.py`**: Manages how benchmark results are displayed to the user in the terminal or Jupyter notebooks.

### `tests/`
Contains comprehensive `pytest` cases. Tests are organized by the specific feature or module they verify (e.g., `test_memory_profiling.py`).

### `examples/` & `demos/`
Educational resources showing how to use the library for ad-hoc benchmarking and pedagogical challenges.

### `plans/`
Detailed blueprints for both implemented and upcoming features. This is the source of truth for the project's roadmap.

## Integration & Entry Points

- **Primary Library Entry Point**: `benchmark_my_code.api.run_benchmarks`
- **Configuration**: `benchmark_my_code.config.get_config`
- **Build System**: Managed by `hatchling` via `pyproject.toml`.
- **Package Management**: Strictly managed using `uv`.
