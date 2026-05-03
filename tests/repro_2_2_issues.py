
import pytest
from benchmark_my_code.api import benchit, run_benchmarks, clear_registry
from benchmark_my_code.orchestrator import reset

def test_multi_parameter_failure():
    clear_registry()
    reset()
    
    # Global 'a' provides values
    global a
    a = [1, 2, 3]
    
    @benchit
    def multi_param(a, b):
        return a + b
    
    # It records the exception instead of raising it
    res = run_benchmarks(print_results=False)
    f = res._benchmark.get_function("multi_param")
    # It should have failed for variant '1' (first element of a)
    assert f.get_status('1') == FailureType.EXCEPTION
    assert "missing 1 required positional argument" in str(f._results['1'].exception)

def test_generator_exhaustion():
    clear_registry()
    reset()
    
    global data
    data = (i for i in range(3)) # Generator object
    
    @benchit
    def func1(data):
        return data
        
    @benchit
    def func2(data):
        return data

    res = run_benchmarks(print_results=False)
    
    f1 = res._benchmark.get_function("func1")
    f2 = res._benchmark.get_function("func2")
    
    # One of them should have 3 variants, the other 0 (or error)
    # Actually, normalised_variants(data) will exhaust it for the first one.
    assert len(f1._status) + len(f2._status) == 3
    # If both got it, they should have 3 each. But they share the generator.
    assert len(f1._status) == 0 or len(f2._status) == 0
