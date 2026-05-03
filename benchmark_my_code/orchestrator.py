from .model import Benchmark, Function, FailureType
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time
import threading
from typing import Any, Callable
import logging

log = logging.getLogger(__name__)

JOIN_TIMEOUT = 0.5  # Theory: allow a small window for clean thread exit

import copy
import tracemalloc

class BenchmarkingWorker:
    _instance = None
    ORPHAN_THRESHOLD = 5

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BenchmarkingWorker, cls).__new__(cls)
            cls._instance._executor = ThreadPoolExecutor(max_workers=1)
            cls._instance._stalled = False
            cls._instance._stop_event = threading.Event()
            cls._instance._orphan_count = 0
        return cls._instance

    def reset(self):
        """
        Public method to reset the worker state. 
        Attempts to clean up background threads, but may leave orphans if they are in infinite loops.
        """
        self._stop_event.set()
        # Ref: ADR-004 - non-blocking shutdown with cancel_futures=True
        self._executor.shutdown(wait=False, cancel_futures=True)
        
        # JOIN_TIMEOUT theory: Join internal threads to avoid orphans if possible
        for t in list(getattr(self._executor, "_threads", [])):
            t.join(timeout=JOIN_TIMEOUT)
            if t.is_alive():
                self._orphan_count += 1
                log.warning(f"Thread {t.name} failed to join and is now an orphan. Total orphans: {self._orphan_count}")

        self._executor = ThreadPoolExecutor(max_workers=1)
        self._stalled = False
        self._stop_event.clear()

    def run(self, function: Callable, args=(), kwargs={}, timeout=100.0):
        if self._stalled:
            if self._orphan_count >= self.ORPHAN_THRESHOLD:
                raise RuntimeError(
                    f"Benchmarking engine is TERMINATED. {self._orphan_count} orphaned threads are consuming resources. "
                    "A full process/kernel restart is now required to ensure system stability."
                )
            raise RuntimeError(
                "Benchmarking engine is TERMINATED due to a previous timeout. "
                "You can attempt to recover by calling `reset()`, but beware that "
                "the stuck thread will continue to run in the background."
            )

        def test_wrapper():
            # Stop-flag pattern within the worker loop
            if self._stop_event.is_set():
                return None
                
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
            
            # Initiate transition to TERMINATED state
            self._stop_event.set()
            self._executor.shutdown(wait=False, cancel_futures=True)
            for t in list(getattr(self._executor, "_threads", [])):
                t.join(timeout=JOIN_TIMEOUT)
                
            raise

def reset():
    """Reset the global BenchmarkingWorker."""
    BenchmarkingWorker().reset()

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
        for (args, kwargs, variant_label, expected) in normalised_variants(variants):
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
            last_result = None

            while total_executions < max_executions:
                current_batch_size = min(batch_size, max_executions - total_executions)
                batch_aborted = False

                # Run the batch
                for _ in range(current_batch_size):
                    try:
                        w_args = copy.deepcopy(args) if ensure_copy else args
                        w_kwargs = copy.deepcopy(kwargs) if ensure_copy else kwargs
                        (last_result, run_time) = worker.run(f._function, w_args, w_kwargs, timeout=timeout)
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

                # Ground Truth Validation (if expected value is provided in variant)
                if expected is not None:
                    if last_result != expected:
                        f.record_status(variant_label, FailureType.CORRECTNESS)
                        batch_aborted = True
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
    """
    Normalises variants into a standard format: (args, kwargs, label, expected_result)

    Supports:
    - [1, 2, 3] -> ((1,), {}, '1', None), ...
    - {'v1': 1, 'v2': 2} -> ((1,), {}, 'v1', None), ...
    - [( (1,2), 3 ), ( (3,4), 7 )] -> ((1,2), {}, '(1, 2)', 3), ... (Scenarios)
    """
    if variants is None:
        yield ((), {}, None, None)
        return

    if isinstance(variants, dict):
        for name, val in variants.items():
            # Check if val is a scenario tuple (input, expected)
            if isinstance(val, tuple) and len(val) == 2:
                inputs, expected = val
                args, kwargs = _to_args_kwargs(inputs)
                yield (args, kwargs, name, expected)
            else:
                args, kwargs = _to_args_kwargs(val)
                yield (args, kwargs, name, None)
    else:
        for v in variants:
            # Check for (input, expected) tuple
            if isinstance(v, tuple) and len(v) == 2:
                inputs, expected = v
                args, kwargs = _to_args_kwargs(inputs)
                label = format_parameters(args, kwargs)
                yield (args, kwargs, label, expected)
            else:
                args, kwargs = _to_args_kwargs(v)
                label = format_parameters(args, kwargs)
                yield (args, kwargs, label, None)

def _to_args_kwargs(val: Any) -> tuple[tuple, dict]:
    """Helper to convert a value into (args, kwargs)."""
    if isinstance(val, dict):
        return (), val
    if isinstance(val, tuple):
        return val, {}
    return (val,), {}