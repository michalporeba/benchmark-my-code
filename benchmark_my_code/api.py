from typing import Any, Callable, List, Union, Iterable, Dict
from .orchestrator import bench, normalised_variants, format_parameters, BenchmarkingWorker
from .model import Challenge, Benchmark, FailureType
import logging
import inspect
import ast
import copy
import random
import textwrap
import sys

log = logging.getLogger(__name__)

_GLOBAL_REGISTRY: List[Callable] = []
_CHALLENGE_REGISTRY: List[tuple[Callable, Challenge]] = []

class InconsistentOutcomesError(Exception):
    pass

class InvalidSignatureError(Exception):
    pass

class ForbiddenCallError(Exception):
    pass

def benchit(arg: Union[Callable, bool] = True, **kwargs) -> Callable:
    """
    Decorator to register a function for ad-hoc benchmarking.
    Can be used as @benchit or @benchit(ensure_copy=False).
    """
    ensure_copy = kwargs.get('ensure_copy', arg if isinstance(arg, bool) else True)
    
    def decorator(func: Callable) -> Callable:
        func._bmc_ensure_copy = ensure_copy
        _GLOBAL_REGISTRY.append(func)
        return func

    if callable(arg):
        return decorator(arg)
    
    return decorator

def validate_signature(func: Callable, expected_params: List[str]):
    """Validates that a function signature matches the expected parameters."""
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    
    if params != expected_params:
        stub = f"def {func.__name__}({', '.join(expected_params)}):"
        raise InvalidSignatureError(
            f"Function '{func.__name__}' has an invalid signature.\n"
            f"Expected: {stub}\n"
            f"Found:    def {func.__name__}({', '.join(params)}):"
        )

class ForbiddenCallVisitor(ast.NodeVisitor):
    def __init__(self, banned_list):
        self.banned_list = banned_list
        self.found = []

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id in self.banned_list:
                self.found.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            full_name = f"{node.func.attr}" 
            if full_name in self.banned_list:
                self.found.append(full_name)
        self.generic_visit(node)

def validate_algorithmic_constraints(func: Callable, banned_calls: List[str]):
    """Checks if the function uses any forbidden built-ins or methods."""
    if not banned_calls:
        return

    try:
        source = textwrap.dedent(inspect.getsource(func))
        tree = ast.parse(source)
        visitor = ForbiddenCallVisitor(banned_calls)
        visitor.visit(tree)
        
        if visitor.found:
            forbidden = ", ".join(set(visitor.found))
            raise ForbiddenCallError(
                f"Challenge forbids the use of: {forbidden}.\n"
                f"Function '{func.__name__}' must be implemented from scratch."
            )
    except (OSError, TypeError):
        logging.warning(f"Could not retrieve source for '{func.__name__}'. Algorithmic constraints not verified.")

def challenge(challenge_obj: Challenge):
    """Decorator to register a function for a specific challenge."""
    def decorator(func: Callable) -> Callable:
        validate_signature(func, challenge_obj.parameters)
        validate_algorithmic_constraints(func, challenge_obj.banned_calls)
        _CHALLENGE_REGISTRY.append((func, challenge_obj))
        return func
    return decorator

def _resolve_variants_for_func(func: Callable, variants: Any) -> Any:
    """
    If variants is None, attempts to find a global iterable matching 
    the first parameter name of the function, OR a function matching
    the parameter name that yields data (DAG resolution).
    """
    if variants is not None:
        return variants
    
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    if not params:
        return None
        
    param_name = params[0]
    
    # Look for param_name in the caller's scope
    frame = sys._getframe(2)
    while frame:
        if param_name in frame.f_globals:
            val = frame.f_globals[param_name]
            
            # Story 2.3: If it's a function, it's a provider
            if callable(val):
                provider_result = val()
                if inspect.isgenerator(provider_result) or isinstance(provider_result, (list, tuple, range)):
                    return provider_result
            
            # Story 2.2: Simple iterable
            if isinstance(val, (list, tuple, range)) or inspect.isgenerator(val):
                return val
        frame = frame.f_back
            
    return None

def run_benchmarks(variants: Any = None, validate: bool = False, print_results: bool = True, **kwargs):
    """
    Runs benchmarks for all registered functions.
    If validate=True, ensures all functions return the same result for each variant.
    """
    if not _GLOBAL_REGISTRY and not _CHALLENGE_REGISTRY:
        logging.warning("No functions registered for benchmarking. Use @benchit or @challenge decorators.")
        return None

    total_benchmark = Benchmark()
    hints = []

    # 1. Run Ad-hoc benchmarks
    if _GLOBAL_REGISTRY:
        if validate:
            # For validation, we need a common variant set. 
            # If variants is None, we can only validate if ALL functions 
            # have matching param names. For simplicity, if validate=True,
            # we expect variants to be provided or we use the first function's resolution.
            common_variants = variants
            if common_variants is None and _GLOBAL_REGISTRY:
                common_variants = _resolve_variants_for_func(_GLOBAL_REGISTRY[0], None)
            
            for (args, kwargs_variant, name) in normalised_variants(common_variants):
                results = {}
                for func in _GLOBAL_REGISTRY:
                    safe_args = copy.deepcopy(args)
                    safe_kwargs = copy.deepcopy(kwargs_variant)
                    worker = BenchmarkingWorker()
                    try:
                        result, _ = worker.run(func, safe_args, safe_kwargs)
                        results[func.__name__] = result
                    except Exception as e:
                        results[func.__name__] = f"<Exception: {e}>"

                unique_results = list(results.values())
                if len(set(map(repr, unique_results))) > 1:
                    variant_label = name or f"args={args}, kwargs={kwargs_variant}"
                    error_msg = f"Inconsistent outcomes for variant ({variant_label}):\n"
                    for f_name, res in results.items():
                        error_msg += f"  {f_name} -> {res}\n"
                    raise InconsistentOutcomesError(error_msg)

        for func in _GLOBAL_REGISTRY:
            # Resolve variants for THIS function specifically if none provided globally
            func_variants = _resolve_variants_for_func(func, variants)
            adhoc_bench = bench(func, variants=func_variants, **kwargs)
            for f in adhoc_bench.functions:
                total_benchmark.add_function(f)

    # 2. Run Challenge benchmarks
    by_challenge = {}
    for func, chall in _CHALLENGE_REGISTRY:
        if chall not in by_challenge:
            by_challenge[chall] = []
        by_challenge[chall].append(func)

    for chall, funcs in by_challenge.items():
        # Handle stages vs variants
        run_stages = chall.stages if chall.stages else {"Default": chall.variants}
        
        ref_name = None
        if chall.reference:
            ref_func = chall.reference
            if not hasattr(ref_func, '__name__') or ref_func.__name__ == '<lambda>':
                ref_func.__name__ = f"Reference_{chall.name.replace(' ', '_')}"
            ref_name = ref_func.__name__

        stop_challenge = False
        for stage_name, stage_variants in run_stages.items():
            if stop_challenge: break
            
            # Handle generator in stage variants
            actual_variants = stage_variants
            if callable(actual_variants):
                random.seed(42)
                actual_variants = actual_variants()

            for (args, kwargs_variant, name) in normalised_variants(actual_variants):
                if stop_challenge: break
                
                variant_label = name or format_parameters(args, kwargs_variant)
                current_variant_data = {variant_label: args}
                
                adaptive_timeout = 100.0
                
                # 2a. Run reference first to establish hardware-specific baseline
                if chall.reference:
                    log.info(f"Establishing baseline for challenge '{chall.name}' using reference implementation...")
                    ref_bench = bench(chall.reference, variants=current_variant_data, **kwargs)
                    for f in ref_bench.functions:
                        total_benchmark.add_function(f)
                    
                    ref_func_obj = ref_bench.get_function(ref_name)
                    ref_median = ref_func_obj.median_time(variant_label)
                    # Set absolute timeout to (reference * multiplier)
                    adaptive_timeout = max(ref_median * chall.timeout_multiplier, 0.001)
                    log.info(f"Baseline median: {ref_median:.6f}s. Setting adaptive timeout to {adaptive_timeout:.6f}s")

                # 2b. Run student functions
                chall_bench = bench(funcs, variants=current_variant_data, timeout=adaptive_timeout, **kwargs)
                
                for f in chall_bench.functions:
                    total_benchmark.add_function(f)
                    
                    # Correctness Check against Reference
                    status = f.get_status(variant_label)
                    if status == FailureType.NONE and chall.reference:
                        # Only check correctness if it didn't timeout or crash
                        try:
                            worker = BenchmarkingWorker()
                            ref_res, _ = worker.run(chall.reference, copy.deepcopy(args), copy.deepcopy(kwargs_variant))
                            student_res, _ = worker.run(f._function, copy.deepcopy(args), copy.deepcopy(kwargs_variant))
                            if student_res != ref_res:
                                f.record_status(variant_label, FailureType.CORRECTNESS)
                                status = FailureType.CORRECTNESS
                        except Exception:
                            # If student code crashes during correctness check, it should have been caught by bench
                            pass

                    # Hint Lookup
                    if status != FailureType.NONE:
                        hint = chall.hints.get((stage_name, status))
                        if hint:
                            hints.append(hint)
                            stop_challenge = True # Stop on first hintable failure

    from .result import BenchmarkResult
    result = BenchmarkResult(total_benchmark)
    result.hints = hints
    
    if print_results:
        print(result)
        
    return result

def clear_registry():
    _GLOBAL_REGISTRY.clear()
    _CHALLENGE_REGISTRY.clear()
