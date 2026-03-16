from benchmark_my_code import *
import time

def test_parameterless_function_with_defaults():
    def parameterless_function():
        time.sleep(0.001)
    
    benchmark = bench(parameterless_function)
    
    assert type(benchmark) is Benchmark
    assert len(benchmark.functions) == 1

    func = benchmark.get_function('parameterless_function')

    assert func.name == 'parameterless_function'
    assert func.executions <= 100
    assert func.total_time() >= 0.01 
    assert func.min_time() < func.max_time()

def test_execution_stops_at_batch_boundary():
    def fast_function():
        time.sleep(0.001)
    
    benchmark = bench(fast_function, max_executions=100, batch_size=15)
    func = benchmark.get_function('fast_function')
    
    # Since it evaluates convergence at batch boundaries, the total executions
    # must be a multiple of the batch_size (unless it hit max_executions and max_executions is not a multiple).
    # Since max_executions is 100 and batch_size is 15, if it stops early it'll be a multiple of 15.
    assert func.executions % 15 == 0
    assert func.executions >= 30 # At least 2 batches are needed to check convergence

