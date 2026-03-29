import statistics
from typing import Any
from enum import Enum, auto

class FailureType(Enum):
    NONE = auto()
    CORRECTNESS = auto()
    TIMEOUT = auto()
    EXCEPTION = auto()
    CONSTRAINT = auto()


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
        self._status = {} # Map variant -> FailureType

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

    def median_time(self, variant=None):
        if variant:
            executions = self._executions.get(variant, [])
            if not executions:
                return 0
            return statistics.median(executions)
        
        # If no variant specified, get median across all executions of all variants
        all_executions = []
        for exs in self._executions.values():
            all_executions.extend(exs)
        if not all_executions:
            return 0
        return statistics.median(all_executions)

    def record_execution_time(self, variant: str, time: float) -> None:
        if variant not in self._executions:
            self._executions[variant] = []
            self._total_time[variant] = 0
            self._min_time[variant] = time
            self._max_time[variant] = time
            self._status[variant] = FailureType.NONE

        self._executions[variant].append(time)        
        self._total_time[variant] += time 
        self._min_time[variant] = min(self._min_time[variant], time)
        self._max_time[variant] = max(self._max_time[variant], time)

    def merge(self, other: 'Function') -> None:
        """Merges execution data from another Function object into this one."""
        for variant, times in other._executions.items():
            if variant not in self._executions:
                self._executions[variant] = []
                self._total_time[variant] = 0
                self._min_time[variant] = other._min_time[variant]
                self._max_time[variant] = other._max_time[variant]
                self._status[variant] = other._status.get(variant, FailureType.NONE)
            
            self._executions[variant].extend(times)
            self._total_time[variant] += other._total_time[variant]
            self._min_time[variant] = min(self._min_time[variant], other._min_time[variant])
            self._max_time[variant] = max(self._max_time[variant], other._max_time[variant])

    def record_status(self, variant: str, status: FailureType) -> None:
        self._status[variant] = status

    def get_status(self, variant: str) -> FailureType:
        return self._status.get(variant, FailureType.NONE)

    def check_convergence(self, variant: str, previous_median: float) -> tuple[bool, float]:
        """
        Evaluates if the current median has converged relative to a previous median.
        Returns a tuple: (has_converged: bool, current_median: float)
        """
        current_median = self.median_time(variant)
        
        if previous_median == 0 and current_median == 0:
            return True, current_median
        elif previous_median == 0:
            return False, current_median
            
        change_rate = abs((current_median - previous_median) / previous_median)
        return change_rate < 0.01, current_median

    def get_executions(self, variant: str):
        return self._executions.get(variant, [])

    def record_timeout(self, variant: str) -> None:
        self._status[variant] = FailureType.TIMEOUT

    def record_exception(self, variant: str, exception: Exception) -> None: 
        self._status[variant] = FailureType.EXCEPTION


class Challenge:
    """Defines a benchmarking challenge with a specific contract."""
    def __init__(self, name: str, parameters: list[str], variants: Any = None, reference: callable = None, banned_calls: list[str] = None, timeout_multiplier: float = 10.0, stages: dict = None, hints: dict = None):
        self.name = name
        self.parameters = parameters
        self.variants = variants
        self.reference = reference
        self.banned_calls = banned_calls or []
        self.timeout_multiplier = timeout_multiplier
        self.stages = stages or {}
        self.hints = hints or {}


class Benchmark:
    def __init__(self):
        self._functions = {} 

    def add_function(self, function: Function) -> 'Benchmark':
        if function.name in self._functions:
            self._functions[function.name].merge(function)
        else:
            self._functions[function.name] = function
        return self

    @property
    def functions(self):
        return self._functions.values()

    def get_function(self, name: str) -> Function:
        return self._functions.get(name, None)
