import pytest
from benchmark_my_code import Benchmark, Function
from benchmark_my_code.result import BenchmarkResult

def dummy_func():
    pass

def test_benchmark_result_str():
    bench = Benchmark()
    func = Function(dummy_func)
    func.record_execution_time("()", 0.1)
    func.record_execution_time("()", 0.2)
    bench.add_function(func)
    
    result = BenchmarkResult(bench)
    output = str(result)
    
    # Depending on whether rich is installed, output might vary, 
    # but the function name and variant should be present.
    assert "dummy_func" in output
    assert "()" in output
    
def test_benchmark_result_repr_html():
    bench = Benchmark()
    func = Function(dummy_func)
    func.record_execution_time("()", 0.1)
    bench.add_function(func)
    
    result = BenchmarkResult(bench)
    html = result._repr_html_()
    
    assert "<table>" in html or "<table " in html
    assert "dummy_func" in html
    assert "()" in html

def test_named_variants_output():
    from benchmark_my_code import clear_registry, benchit, run_benchmarks
    clear_registry()
    
    @benchit
    def my_func(x):
        return x
        
    # Test with named variants
    result = run_benchmarks(variants={"Label A": (1,), "Label B": (2,)}, print_results=False, max_executions=1, warmup_executions=0)
    output = str(result)
    assert "Label A" in output
    assert "Label B" in output
    
    # Test with unnamed variants (fallback to repr)
    result = run_benchmarks(variants=[(999,)], print_results=False, max_executions=1, warmup_executions=0)
    output = str(result)
    assert "999" in output

def test_benchmark_result_to_dict():
    bench = Benchmark()
    func = Function(dummy_func)
    func.record_execution_time("()", 0.1)
    bench.add_function(func)
    
    result = BenchmarkResult(bench)
    data = result.to_dict()
    
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["function"] == "dummy_func"
    assert data[0]["median_time"] == 0.1

def test_benchmark_result_to_dataframe():
    bench = Benchmark()
    func = Function(dummy_func)
    func.record_execution_time("()", 0.1)
    bench.add_function(func)
    
    result = BenchmarkResult(bench)
    
    # Try to import pandas to see if we should expect it to work or fail
    try:
        import pandas as pd
        df = result.to_dataframe()
        assert isinstance(df, pd.DataFrame)
    except ImportError:
        with pytest.raises(ImportError) as excinfo:
            result.to_dataframe()
        assert "Pandas is not installed" in str(excinfo.value)
