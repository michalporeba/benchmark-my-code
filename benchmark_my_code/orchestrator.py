from .model import Benchmark, Function
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time
from typing import Any, Callable
import logging

log = logging.getLogger(__name__)

import copy
import tracemalloc

class BenchmarkingWorker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BenchmarkingWorker, cls).__new__(cls)
            cls._instance._executor = ThreadPoolExecutor(max_workers=1)
            cls._instance._stalled = False
        return cls._instance

    def _reset(self):
        """Internal method to reset the worker state for tests."""
        self._executor.shutdown(wait=False)
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._stalled = False

    def run(self, function: Callable, args=(), kwargs={}, timeout=100.0):
        if self._stalled:
            raise RuntimeError(
                "Benchmarking engine is STALLED due to a previous timeout. "
                "The background worker is likely stuck in an infinite loop. "
                "Please restart your Python process or Jupyter kernel to continue."
            )

        def test_wrapper():
            start_time = time.perf_counter_ns()
            result = function(*args, **kwargs)
            end_time = time.perf_counter_ns()
            return (result, (end_time - start_time) / 1_000_000_000.0)

        future = self._executor.submit(test_wrapper)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            self._stalled = True
            log.error("Execution timed out. Worker thread is now STALLED.")
            raise

def bench(functions: Any, variants: Any = None, max_executions: int = 100, warmup_executions: int = 10, batch_size: int = 10, timeout: float = 100.0) -> Benchmark:
    benchmark = Benchmark()
    worker = BenchmarkingWorker()

    # Handle single callable vs iterable of callables
    if callable(functions):
        functions = [functions]

    for func in functions:
        benchmark.add_function(Function(func))

    for f in benchmark.functions:
        ensure_copy = getattr(f._function, '_bmc_ensure_copy', True)
        
        log.info(f"Benchmarking function {f.name}")
        for (args, kwargs, name) in normalised_variants(variants):
            variant_label = name or format_parameters(args, kwargs)
            log.info(f"testing {f.name}({variant_label})")

            # Warmup
            if warmup_executions > 0:
                log.info(f"Warmup: running {warmup_executions} times")
                for _ in range(warmup_executions):
                    try:
                        # Use individual function's ensure_copy flag
                        w_args = copy.deepcopy(args) if ensure_copy else args
                        w_kwargs = copy.deepcopy(kwargs) if ensure_copy else kwargs
                        worker.run(f._function, w_args, w_kwargs, timeout=timeout)
                    except TimeoutError:
                        break
                    except RuntimeError:
                        raise
                    except Exception:
                        break

            total_executions = 0
            previous_median = 0.0

            while total_executions < max_executions:
                current_batch_size = min(batch_size, max_executions - total_executions)
                batch_aborted = False

                # Run the batch
                for _ in range(current_batch_size):
                    try:
                        w_args = copy.deepcopy(args) if ensure_copy else args
                        w_kwargs = copy.deepcopy(kwargs) if ensure_copy else kwargs
                        (result, run_time) = worker.run(f._function, w_args, w_kwargs, timeout=timeout)
                        f.record_execution_time(variant_label, run_time)
                        total_executions += 1
                    except TimeoutError:
                        f.record_timeout(variant_label)
                        batch_aborted = True
                        break
                    except RuntimeError:
                        raise
                    except Exception as e:
                        f.record_exception(variant_label, e)
                        batch_aborted = True
                        break

                if batch_aborted:
                    break

                # Evaluate stability at batch boundary
                is_stable, current_median = f.check_convergence(variant_label, previous_median)

                # Don't consider it stable if previous_median was 0 (first batch)
                if is_stable and previous_median > 0:
                    log.info(f"Results for {f.name}({variant_label}) are stable after {total_executions} executions.")
                    break

                previous_median = current_median

            # 3. Perform a separate Memory Pass once timing is stable
            # ONLY if the timing pass succeeded (no timeout/exception)
            if not batch_aborted:
                try:
                    w_args = copy.deepcopy(args) if ensure_copy else args
                    w_kwargs = copy.deepcopy(kwargs) if ensure_copy else kwargs
                    peak_bytes = measure_memory(f._function, w_args, w_kwargs)
                    f.record_memory(variant_label, peak_bytes)
                except Exception:
                    # Memory profiling errors shouldn't crash the whole benchmark
                    pass

    return benchmark

def format_parameters(args, kwargs):
    args_string = ", ".join(repr(arg) for arg in args)
    kwargs_string = ", ".join(f"{key}={repr(value)}" for key, value in kwargs.items())
    if args_string and kwargs_string:
        return f"{args_string}, {kwargs_string}"
    return args_string or kwargs_string


import gc

def measure_memory(function: Callable, args=(), kwargs={}) -> float:
    """
    Measures the peak memory usage of a single function call in a hygienic way.
    Story 1.3: Decoupled pass with explicit lifecycle management.
    """
    # Force collection of any leftovers before starting
    gc.collect()
    
    tracemalloc.start()
    tracemalloc.clear_traces()
    try:
        function(*args, **kwargs)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
        # Clean up after ourselves
        gc.collect()
        
    return float(peak)


def normalised_variants(variants: Any):
    if variants is None:
        yield ((), {}, None)
    elif isinstance(variants, dict):
        for name, args in variants.items():
            if isinstance(args, tuple):
                yield (args, {}, name)
            else:
                yield ((args,), {}, name)
    else: 
        for v in variants:
            # If the user passed a tuple, treat it as the args tuple
            if isinstance(v, tuple):
                yield (v, {}, None)
            else:
                # Otherwise, wrap the single value in a tuple
                yield ((v,), {}, None)