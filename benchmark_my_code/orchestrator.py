from .model import Benchmark, Function
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time


def benchit(func: callable) -> Benchmark:
    benchmark = Benchmark()
    benchmark.add_function(Function(func))

    for f in benchmark.functions:
        for i in range(100):
            f.record_execution(measure_time(f))

    return benchmark


def measure_time(function: callable, args=(), kwargs={}) -> float:
    with ThreadPoolExecutor(max_workers=1) as executor: 
        try:
            start_time = time.perf_counter()
            function(*args, **kwargs)
            future = executor.submit(function)
            print(future.result(timeout=100))
        except TimeoutError:
            print("timed out")
        except Exception as e:
            pass
        finally:    
            end_time = time.perf_counter()
    
    return end_time - start_time