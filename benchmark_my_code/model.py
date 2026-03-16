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
        self._executions = {} 
        self._total_time = {}
        self._max_time = {}
        self._min_time = {}
        self._windows_size = 10

    def __call__(self, *args, **kwargs):
        return self._function(*args, **kwargs)

    @property
    def name(self):
        return self._name

    @property
    def executions(self):
        return sum(len(exs) for exs in self._executions.values())

    @property
    def variant_count(self):
        return len(self._executions)

    def total_time(self, variant=None):
        if variant:
            return self._total_time.get(variant, 0)
        return sum(self._total_time.values())

    def min_time(self, variant=None):
        if variant:
            return self._min_time.get(variant, 0)
        return min(self._min_time.values()) if self._min_time else 0
    
    def max_time(self, variant=None):
        if variant:
            return self._max_time.get(variant, 0)
        return max(self._max_time.values()) if self._max_time else 0

    def record_execution_time(self, variant: str, time: float) -> None:
        if variant not in self._executions:
            self._executions[variant] = []
            self._total_time[variant] = 0
            self._min_time[variant] = time
            self._max_time[variant] = time

        self._executions[variant].append(time)        
        self._total_time[variant] += time 
        self._min_time[variant] = min(self._min_time[variant], time)
        self._max_time[variant] = max(self._max_time[variant], time)

        
    def executions_stable(self, variant):
        executions = self._executions.get(variant, [])
        if len(executions) > self._windows_size:
            recent = executions[-self._windows_size:]
            recent_average = sum(recent) / self._windows_size
            average = sum(executions) / len(executions)
            change_rate = (average - recent_average) / ((average + recent_average) / 2)
            return abs(change_rate) < 0.01 

    def get_executions(self, variant: str):
        return self._executions.get(variant, [])

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
