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

def test_check_convergence_uses_median():
    func = Function(dummy_func)
    
    # Establish previous median
    previous_median = 0.05
    
    # Run a batch with outliers
    func.record_execution_time('var1', 0.05)
    func.record_execution_time('var1', 5.0)
    func.record_execution_time('var1', 0.05)
    func.record_execution_time('var1', 5.0)
    func.record_execution_time('var1', 0.05)
    
    is_stable, current_median = func.check_convergence('var1', previous_median)
    
    # With a median-based stability check, the median of the last 5 
    # [0.05, 5.0, 0.05, 5.0, 0.05] is still 0.05, so it remains stable.
    # An arithmetic mean would see a huge spike.
    assert current_median == 0.05
    assert is_stable is True

def test_check_convergence_first_batch():
    func = Function(dummy_func)
    func.record_execution_time('var1', 0.05)
    
    is_stable, current_median = func.check_convergence('var1', 0.0)
    assert current_median == 0.05
    assert is_stable is False # First batch should not be considered stable
