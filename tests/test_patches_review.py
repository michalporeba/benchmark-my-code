import pytest
import logging
from benchmark_my_code.api import run_benchmarks, benchit, clear_registry
from benchmark_my_code.orchestrator import bench, normalised_variants, VARIANT_LIMIT, FailureType
from benchmark_my_code.model import Benchmark

def test_infinite_variants_safety(caplog):
    def infinite_gen():
        i = 0
        while True:
            yield i
            i += 1
    
    def my_func(x):
        return x
    
    # bench should limit the variants
    with caplog.at_level(logging.WARNING):
        b = bench(my_func, variants=infinite_gen(), max_executions=1, warmup_executions=0)
    
    assert len(b.get_function("my_func")._status) == VARIANT_LIMIT
    assert "Benchmark truncated" in caplog.text

def test_numpy_style_comparison():
    class MockArray:
        def __init__(self, val):
            self.val = val
        def __eq__(self, other):
            return MockArray(self.val == other.val)
        def all(self):
            return self.val
        def __iter__(self):
            yield self.val

    def student(x):
        return MockArray(True)
    
    # If we use expected=MockArray(True), standard == would return MockArray(True) which is truthy
    # but we want to be sure it works.
    b = bench(student, variants=[(1, MockArray(True))], max_executions=1, warmup_executions=0)
    assert b.get_function("student").get_status('1') == FailureType.NONE

    def student_fail(x):
        return MockArray(False)
    
    b = bench(student_fail, variants=[(1, MockArray(True))], max_executions=1, warmup_executions=0)
    assert b.get_function("student_fail").get_status('1') == FailureType.CORRECTNESS

def test_auto_discovery_truncation(caplog):
    clear_registry()
    
    # Create a large data set in locals
    data = (i for i in range(VARIANT_LIMIT + 10))
    
    @benchit
    def my_bench(data):
        return data
        
    with caplog.at_level(logging.WARNING):
        run_benchmarks(print_results=False)
        
    assert "truncated to 1000 items" in caplog.text
    clear_registry()

def test_multi_param_discovery():
    clear_registry()
    
    # Two variables in scope
    x = [1, 2]
    y = [3, 4]
    
    @benchit
    def func_x(x): return x
    
    @benchit
    def func_y(y): return y
    
    res = run_benchmarks(print_results=False)
    
    assert "1" in res.benchmark.get_function("func_x")._status
    assert "3" in res.benchmark.get_function("func_y")._status
    clear_registry()
