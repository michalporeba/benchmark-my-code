import pytest
import time
from benchmark_my_code import bench, clear_registry, run_benchmarks

def test_memory_profiling_captures_allocation():
    def memory_heavy_func(n):
        # Allocate a large list
        data = [i for i in range(n)]
        return len(data)
        
    def memory_light_func(n):
        return n
        
    # Run once to keep it fast
    result = bench(memory_heavy_func, variants=[(100000,)], max_executions=1, warmup_executions=0)
    func_heavy = result.get_function('memory_heavy_func')
    # Get the memory for the first (and only) variant
    heavy_mem = list(func_heavy._peak_memory.values())[0]
    
    result = bench(memory_light_func, variants=[(100000,)], max_executions=1, warmup_executions=0)
    func_light = result.get_function('memory_light_func')
    light_mem = list(func_light._peak_memory.values())[0]
    
    # Peak memory for heavy func should be significantly higher
    assert heavy_mem > light_mem
    assert heavy_mem > 0

def test_memory_is_recorded_even_if_zero():
    def dummy(x):
        return x
        
    result = bench(dummy, variants=[(1,)], max_executions=10, warmup_executions=0)
    func = result.get_function('dummy')
    
    # Check if the variant key exists in peak_memory
    # (Label will be "1")
    assert "1" in func._peak_memory
    
    # Timing should also be recorded
    assert func.executions == 10
