class BenchmarkFunction:
    def __init__(self, function: callable):
        self._name = function.__name__
        self._function = function

    @property
    def name(self):
        return self._name

    @property
    def function(self):
        return self._function

class Benchmark:
    def __init__(self):
        self._functions = {} 

    def add_function(self, function: BenchmarkFunction) -> 'Benchmark':
        self._functions[function.name] = function
        return self

    @property
    def functions(self):
        return self._functions.values()

    def get_function(self, name: str) -> BenchmarkFunction:
        return self._functions.get(name, None)