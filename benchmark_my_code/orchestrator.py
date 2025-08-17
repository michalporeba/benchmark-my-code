from .model import Benchmark, Function


def benchit(func: callable) -> Benchmark:
    benchmark = Benchmark()
    benchmark.add_function(Function(func))
    benchmark.benchit()
    return benchmark