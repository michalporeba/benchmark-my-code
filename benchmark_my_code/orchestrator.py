from .model import Benchmark, Function
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time
from typing import Any, Callable
import logging

log = logging.getLogger(__name__)

def bench(function: Callable, variants: Any = None, max_executions: int = 100, warmup_executions: int = 10) -> Benchmark:
    benchmark = Benchmark()
    benchmark.add_function(Function(function))

    for f in benchmark.functions:
        log.info(f"Benchmarking function {f.name}")
        for (args, kwargs, expected_result) in normalised_variants(variants):
            variant = format_parameters(args, kwargs)
            log.info(f"testing {f.name}({variant})")
            
            # Warmup
            if warmup_executions > 0:
                log.info(f"Warmup: running {warmup_executions} times")
                for _ in range(warmup_executions):
                    try:
                        measure_time(f, args, kwargs)
                    except Exception:
                        break

            for i in range(max_executions):
                try:
                    (result, run_time) = measure_time(f, args, kwargs)
                    f.record_execution_time(variant, run_time)
                    if f.executions_stable(variant):
                        log.info(f"Results for {f.name}({variant}) are stable after {len(f.get_executions(variant))} executions.")
                        break
                    # TODO: check if the results are converging and if so, stop early. 
                except TimeoutError:
                    f.record_timeout()
                    # TODO: timeouts at this level should be retried a set number of times.
                    break
                except Exception as e:
                    f.record_exception(e)
                    # TODO: unless the expected result is an exception of the same type. 
                    break

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
    else: 
        for v in variants:
            # If the user passed a tuple, treat it as the args tuple
            if isinstance(v, tuple):
                yield (v, {}, None)
            else:
                # Otherwise, wrap the single value in a tuple
                yield ((v,), {}, None)