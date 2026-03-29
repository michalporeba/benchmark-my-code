from .model import Benchmark, Function
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time
from typing import Any, Callable
import logging

log = logging.getLogger(__name__)

import copy

def bench(functions: Any, variants: Any = None, max_executions: int = 100, warmup_executions: int = 10, batch_size: int = 10) -> Benchmark:
    benchmark = Benchmark()

    # Handle single callable vs iterable of callables
    if callable(functions):
        functions = [functions]

    for func in functions:
        benchmark.add_function(Function(func))

    for f in benchmark.functions:
        log.info(f"Benchmarking function {f.name}")
        for (args, kwargs, name) in normalised_variants(variants):
            variant_label = name or format_parameters(args, kwargs)
            log.info(f"testing {f.name}({variant_label})")

            # Warmup
            if warmup_executions > 0:
                log.info(f"Warmup: running {warmup_executions} times")
                for _ in range(warmup_executions):
                    try:
                        measure_time(f, copy.deepcopy(args), copy.deepcopy(kwargs))
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
                        (result, run_time) = measure_time(f, copy.deepcopy(args), copy.deepcopy(kwargs))
                        f.record_execution_time(variant_label, run_time)
                        total_executions += 1
                    except TimeoutError:
                        f.record_timeout()
                        batch_aborted = True
                        break
                    except Exception as e:
                        f.record_exception(e)
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

    return benchmark

def format_parameters(args, kwargs):
    args_string = ", ".join(repr(arg) for arg in args)
    kwargs_string = ", ".join(f"{key}={repr(value)}" for key, value in kwargs.items())
    if args_string and kwargs_string:
        return f"{args_string}, {kwargs_string}"
    return args_string or kwargs_string


def measure_time(function: Callable, args=(), kwargs={}):
    def test():
        start_time = time.perf_counter_ns()
        result = function(*args, **kwargs)
        end_time = time.perf_counter_ns()
        # Convert nanoseconds to seconds for the final tracked time
        return (result, (end_time - start_time) / 1_000_000_000.0)

    with ThreadPoolExecutor(max_workers=1) as executor: 
        future = executor.submit(test)
        return future.result(timeout=100)


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