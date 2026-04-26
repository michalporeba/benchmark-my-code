import pytest
import statistics
import array
import random
from benchmark_my_code.model import Function

def dummy(): pass

def test_median_odd_elements():
    f = Function(dummy)
    data = [1.0, 3.0, 2.0]
    for x in data:
        f.record_execution_time('v', x)
    assert f.median_time('v') == 2.0

def test_median_even_elements():
    f = Function(dummy)
    data = [1.0, 3.0, 2.0, 4.0]
    for x in data:
        f.record_execution_time('v', x)
    # sorted: 1.0, 2.0, 3.0, 4.0. Median: (2.0 + 3.0) / 2 = 2.5
    assert f.median_time('v') == 2.5

def test_median_large_array():
    f = Function(dummy)
    data = [float(i) for i in range(1001)]
    random.shuffle(data)
    for x in data:
        f.record_execution_time('v', x)
    assert f.median_time('v') == 500.0

def test_median_large_array_even():
    f = Function(dummy)
    data = [float(i) for i in range(1000)]
    random.shuffle(data)
    for x in data:
        f.record_execution_time('v', x)
    # sorted: 0...999. Mid indices 499 and 500. Median (499 + 500) / 2 = 499.5
    assert f.median_time('v') == 499.5

def test_median_no_variant():
    f = Function(dummy)
    f.record_execution_time('v1', 1.0)
    f.record_execution_time('v1', 3.0)
    f.record_execution_time('v2', 2.0)
    f.record_execution_time('v2', 4.0)
    # All: 1, 2, 3, 4. Median: 2.5
    assert f.median_time() == 2.5

def test_median_stability_convergence():
    f = Function(dummy)
    # Initial median 10.0
    f.record_execution_time('v', 10.0)
    f.record_execution_time('v', 10.0)
    f.record_execution_time('v', 10.0)
    
    # Check convergence against 10.1 (within 1%)
    is_stable, current_median = f.check_convergence('v', 10.1)
    assert current_median == 10.0
    assert is_stable is True
    
    # Check convergence against 11.0 (outside 1%)
    is_stable, current_median = f.check_convergence('v', 11.0)
    assert is_stable is False

def test_median_empty():
    f = Function(dummy)
    assert f.median_time('v') == 0
    assert f.median_time() == 0
