import pytest
import time
from benchmark_my_code import benchit, run_benchmarks, clear_registry, InconsistentOutcomesError

def setup_function():
    clear_registry()

def test_automatic_parametrization_from_globals():
    # Define a global that matches the function argument name
    global my_data
    my_data = [1, 2, 3]
    
    @benchit
    def process(my_data):
        return my_data * 2
        
    result = run_benchmarks(print_results=False, max_executions=1, warmup_executions=0)
    func_obj = result.get_function("process")
    assert func_obj.variant_count == 3
    # Check that it picked up individual elements if it's a list?
    # Actually, normalized_variants treats list elements as discrete variants
    # if passed as variants=[1, 2, 3].
    
def test_dag_resolution_from_provider_func():
    global large_array
    def large_array():
        yield [1, 2]
        yield [3, 4]
        
    @benchit
    def sum_array(large_array):
        return sum(large_array)
        
    result = run_benchmarks(print_results=False, max_executions=1, warmup_executions=0)
    func_obj = result.get_function("sum_array")
    assert func_obj.variant_count == 2

def test_deepcopy_opt_out():
    class Mutator:
        def __init__(self): self.val = 1
    
    # Opt-out of copy
    @benchit(ensure_copy=False)
    def inc_val(obj):
        obj.val += 1
        return obj.val

    m = Mutator()
    # If we don't copy, the same object 'm' will be incremented repeatedly
    # Run 5 times.
    run_benchmarks(variants=[(m,)], max_executions=5, warmup_executions=0, print_results=False)
    
    # If opt-out worked, m.val should be 6 (1 original + 5 increments)
    # Note: Memory pass also runs it if it didn't fail, so it might be 7.
    # But wait, bench runs max_executions.
    assert m.val > 1
    
def test_deepcopy_enabled_by_default():
    class Mutator:
        def __init__(self): self.val = 1
        
    @benchit
    def inc_val_copy(obj):
        obj.val += 1
        return obj.val

    m = Mutator()
    run_benchmarks(variants=[(m,)], max_executions=5, warmup_executions=0, print_results=False)
    
    # If copy worked, the original 'm' remains 1
    assert m.val == 1
