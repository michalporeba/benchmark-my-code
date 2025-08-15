from benchmark_my_code import *


def test_parameterless_function_with_defaults():
    def parameterless_function():
        return sum(range(100))   
    
    benchmark = benchit(parameterless_function)
    
    assert type(benchmark) is Benchmark