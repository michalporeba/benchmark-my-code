from .model import Benchmark, Function, FailureType
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time
import threading
import random
from typing import Any, Callable, List
import logging

log = logging.getLogger(__name__)

JOIN_TIMEOUT = 0.5  # Theory: allow a small window for clean thread exit
BASELINE_FLOOR = 0.001 # 1ms floor for adaptive timeouts
REFERENCE_META_TIMEOUT = 5.0 # Max time to spend on establishing a baseline per variant

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
                        f.record_execution_time(variant_label, run_time, result=last_result)
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

import inspect

def run_challenge(challenge_obj: Any, student_functions: List[Callable], total_benchmark: Benchmark, **kwargs) -> List[str]:
    """
    Orchestrates the execution of a Challenge.
    Returns a list of hints if any failures occurred.
    """
    hints = []
    print_results = kwargs.get('print_results', True)

    if print_results:
        print(f"\n🏆 Running Challenge: {challenge_obj.name}")

    # Handle stages vs variants
    run_stages = getattr(challenge_obj, 'stages', {}) or {"Default": getattr(challenge_obj, 'variants', None)}

    ref_name = None
    if challenge_obj.reference:
        ref_func = challenge_obj.reference
        ref_name = getattr(ref_func, '__name__', None)
        if not ref_name or ref_name == '<lambda>':
             ref_name = f"Reference_{challenge_obj.name.replace(' ', '_')}"
             # We don't mutate ref_func.__name__ as it's cleaner to handle in Function model

    # Discover valid bench args dynamically
    bench_sig = inspect.signature(bench)
    valid_bench_keys = {p.name for p in bench_sig.parameters.values() if p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)}

    stop_challenge = False
    for stage_name, stage_variants in run_stages.items():
        if stop_challenge: break

        if print_results:
            print(f"  Stage: {stage_name}")

        # Handle generator in stage variants
        actual_variants = stage_variants
        if callable(actual_variants):
            # Note: We can't easily isolate global random without monkeypatching or 
            # requiring the generator to accept a Random instance. 
            # For now, we just call it.
            actual_variants = actual_variants()

        for (args, kwargs_variant, name, expected) in normalised_variants(actual_variants):
            if stop_challenge: break

            variant_label = name or format_parameters(args, kwargs_variant)
            if print_results:
                print(f"    - Variant '{variant_label}'...", end="", flush=True)

            # Preserve both args and kwargs for variants
            current_variant_data = {variant_label: {'args': args, 'kwargs': kwargs_variant}}
            adaptive_timeout = kwargs.get('timeout', 100.0)

            # 2a. Run reference first to establish hardware-specific baseline
            if challenge_obj.reference:
                try:
                    # Establish baseline with a meta-timeout to prevent hanging
                    bench_args = {k: v for k, v in kwargs.items() if k in valid_bench_keys}
                    ref_bench = bench(challenge_obj.reference, variants=current_variant_data, timeout=REFERENCE_META_TIMEOUT, **bench_args)
                    for f in ref_bench.functions:
                        total_benchmark.add_function(f)

                    ref_func_obj = ref_bench.get_function(ref_name)
                    if not ref_func_obj:
                        # Fallback if name identification was complex
                        ref_func_obj = list(ref_bench.functions)[0] if ref_bench.functions else None

                    # Check if reference actually succeeded
                    if not ref_func_obj or ref_func_obj.get_status(variant_label) != FailureType.NONE:
                        status_name = ref_func_obj.get_status(variant_label).name if ref_func_obj else "NOT_FOUND"
                        if print_results:
                            print(f" BASELINE FAILURE ({status_name})")
                        # Mark all student functions as baseline failed for this variant
                        for s_func in student_functions:
                            s_name = getattr(s_func, '__name__', str(s_func))
                            f_model = total_benchmark.get_function(s_name)
                            if not f_model:
                                f_model = Function(s_func)
                                total_benchmark.add_function(f_model)
                            f_model.record_status(variant_label, FailureType.BASELINE_FAILURE)
                        continue

                    ref_median = ref_func_obj.median_time(variant_label)
                    # Set absolute timeout to (reference * multiplier) with a floor
                    multiplier = getattr(challenge_obj, 'timeout_multiplier', 10.0)
                    adaptive_timeout = max(ref_median * multiplier, BASELINE_FLOOR)

                    # Use reference output as ground-truth if none provided (Reuse captured result)
                    if expected is None:
                        expected = ref_func_obj.get_sample_result(variant_label)

                except Exception as e:
                    log.error(f"Critical error establishing baseline: {e}")
                    if print_results:
                        print(" BASELINE ERROR")
                    continue

            # 2b. Run student functions
            # Re-normalise variants to include the 'expected' value from reference if found
            # Use explicit format to preserve kwargs
            student_variants = {variant_label: ({'args': args, 'kwargs': kwargs_variant}, expected)}
            bench_args = {k: v for k, v in kwargs.items() if k in valid_bench_keys}
            chall_bench = bench(student_functions, variants=student_variants, timeout=adaptive_timeout, **bench_args)

            if print_results:
                print(" DONE")

            for f in chall_bench.functions:
                total_benchmark.add_function(f)

                status = f.get_status(variant_label)
                # Hint Lookup
                hint = (challenge_obj.hints or {}).get((stage_name, status))
                if hint:
                    hints.append(hint)
                    stop_challenge = True # Stop on first hintable failure

    return hints

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
        if 'args' in val or 'kwargs' in val:
            return val.get('args', ()), val.get('kwargs', {})
        return (), val
    if isinstance(val, tuple):
        return val, {}
    return (val,), {}