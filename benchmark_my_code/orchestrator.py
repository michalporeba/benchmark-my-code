from .model import Benchmark, BenchmarkFunction


def benchit(func: callable) -> Benchmark:
    benchmark = Benchmark()
    benchmark.add_function(BenchmarkFunction(func))
    benchmark.benchit()
    return benchmark