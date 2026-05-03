
from benchmark_my_code import benchit, run_benchmarks, clear_registry
import pytest

def setup_function():
    clear_registry()

def test_dag_recursion():
    # test(a) -> a(b) -> b()
    def b():
        yield [1]
        
    def a(b):
        # a should yield something based on b
        for item in b:
            yield item + [2]
            
    @benchit
    def test_func(a):
        return a

    print("\n--- Testing DAG Recursion ---")
    try:
        from benchmark_my_code.api import _resolve_variants_for_func
        import sys
        
        # We need to simulate the environment where _resolve_variants_for_func is called
        # but since we are calling it from here, it should find local b and a.
        
        # Actually, run_benchmarks calls it.
        result = run_benchmarks(print_results=True, max_executions=1, warmup_executions=0)
        func_obj = result.get_function("test_func")
        print(f"Variant count: {func_obj.variant_count if func_obj else 0}")
    except Exception as e:
        print(f"Caught exception: {e}")
        import traceback
        traceback.print_exc()

def test_dag_multiple_dependencies():
    # test(a, b)
    def a():
        yield 1
    def b():
        yield 2
        
    @benchit
    def test_func(a, b):
        return a + b

    print("\n--- Testing Multiple Dependencies ---")
    result = run_benchmarks(print_results=True, max_executions=1, warmup_executions=0)
    func_obj = result.get_function("test_func")
    print(f"Variant count: {func_obj.variant_count if func_obj else 0}")
    if func_obj and func_obj.variant_count > 0:
        # Check if it actually ran with both a and b
        pass

def test_dag_cycle():
    # a(b) -> b(a)
    def a(b): yield b
    def b(a): yield a
    
    @benchit
    def test_func(a):
        return a
        
    print("\n--- Testing DAG Cycle ---")
    try:
        result = run_benchmarks(print_results=True, max_executions=1, warmup_executions=0)
        func_obj = result.get_function("test_func")
        print(f"Variant count: {func_obj.variant_count if func_obj else 0}")
    except Exception as e:
        print(f"Caught exception in cycle: {e}")

if __name__ == "__main__":
    setup_function()
    test_dag_recursion()
    setup_function()
    test_dag_multiple_dependencies()
    setup_function()
    test_dag_cycle()
