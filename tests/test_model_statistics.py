import pytest
import statistics
from benchmark_my_code.model import Function

def dummy_func():
    pass

def test_function_median_time_ignores_outliers():
    func = Function(dummy_func)
    
    # 5 fast runs, 1 massive outlier
    times = [0.01, 0.01, 0.01, 0.01, 0.01, 1.0]
    for t in times:
        func.record_execution_time('var1', t)
        
    assert func.median_time('var1') == 0.01

def test_executions_stable_uses_median():
    func = Function(dummy_func)
    func._windows_size = 5
    
    # establish stable median of 0.05
    for _ in range(10):
        func.record_execution_time('var1', 0.05)
        
    # inject outliers into the recent window
    func.record_execution_time('var1', 0.05)
    func.record_execution_time('var1', 5.0)
    func.record_execution_time('var1', 0.05)
    func.record_execution_time('var1', 5.0)
    func.record_execution_time('var1', 0.05)
    
    # With a median-based stability check, the median of the last 5 
    # [0.05, 5.0, 0.05, 5.0, 0.05] is still 0.05, so it remains stable.
    # An arithmetic mean would see a huge spike.
    assert func.executions_stable('var1') is True
