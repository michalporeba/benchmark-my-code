from benchmark_my_code import *
import time


def test_parameterless_function_with_defaults():
    def parameterless_function():
        time.sleep(0.001)
    
    benchmark = benchit(parameterless_function)
    
    assert type(benchmark) is Benchmark
    assert len(benchmark.functions) == 1

    func = benchmark.get_function('parameterless_function')

    assert func.name == 'parameterless_function'
    assert func.executions == 100
    assert func.total_time >= 0.1 
    assert func.min_time < func.max_time
