from .model import Benchmark, Function
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time
from typing import Any, Callable

def benchit(function: Callable, variants: Any = [((), {}, Any)], max_executions: int = 100) -> Benchmark:
    benchmark = Benchmark()
    benchmark.add_function(Function(function))

    for f in benchmark.functions:
        for (args, kwargs, expected_result) in variants:
            for i in range(max_executions):
                try:
                    f.record_execution(*measure_time(f, *args, **kwargs))
                    # TODO: check if the results are converging and if so, stop early. 
                except TimeoutError:
                    f.record_timeout()
                    # TODO: timeouts at this level should be retried a set number of times.
                    break
                except Exception as e:
                    f.record_execption(e)
                    # TODO: unless the expected result is an exception of the same type. 
                    break

    return benchmark


def measure_time(function: Callable, args=(), kwargs={}) -> float:
    def sut():
        start_time = time.perf_counter()
        result = function(*args, **kwargs)
        end_time = time.perf_counter()
        return (result, end_time - start_time)

    with ThreadPoolExecutor(max_workers=1) as executor: 
        future = executor.submit(sut)
        return future.result(timeout=100)
    
    return run_time