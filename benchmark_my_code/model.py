from typing import Any


class Variant:
    def __init__(self, definition: Any):
        self._name = str(definition)

    @property
    def name(self):
        return self._name

    @property
    def args(self):
        return None

    


class Function:
    def __init__(self, function: callable):
        self._name = function.__name__
        self._function = function
        self._executions = 0
        self._total_time = 0
        self._max_time = 0
        self._min_time = 0xffffffff


    def __call__(self, args=(), kwargs={}):
        return self._function(*args, **kwargs)

    @property
    def name(self):
        return self._name

    @property
    def executions(self):
        return self._executions

    @property 
    def total_time(self):
        return self._total_time

    @property
    def min_time(self):
        return self._min_time
    
    @property
    def max_time(self):
        return self._max_time

    def record_execution(self, result: any, time: float) -> None:
        self._executions += 1
        self._total_time += time 
        self._min_time = min(self._min_time, time)
        self._max_time = max(self._max_time, time)
        print(f"function {self._name} finished in {time} ms and returned {result}")

    def record_timeout(self) -> None:
        pass 

    def record_exception(self, exception: Exception) -> None: 
        pass


class Benchmark:
    def __init__(self):
        self._functions = {} 

    def add_function(self, function: Function) -> 'Benchmark':
        self._functions[function.name] = function
        return self

    @property
    def functions(self):
        return self._functions.values()

    def get_function(self, name: str) -> Function:
        return self._functions.get(name, None)
