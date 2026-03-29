from typing import Any, Callable, List, Union, Iterable, Dict
from .orchestrator import bench, measure_time, normalised_variants, format_parameters
from .model import Challenge, Benchmark, FailureType
import logging
import inspect
import ast
import copy
import random
import textwrap

_GLOBAL_REGISTRY: List[Callable] = []
_CHALLENGE_REGISTRY: List[tuple[Callable, Challenge]] = []

class InconsistentOutcomesError(Exception):
    pass

class InvalidSignatureError(Exception):
    pass

class ForbiddenCallError(Exception):
    pass

def benchit(func: Callable) -> Callable:
    """Decorator to register a function for ad-hoc benchmarking."""
    _GLOBAL_REGISTRY.append(func)
    return func

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
            for (args, kwargs_variant, name) in normalised_variants(variants):
                results = {}
                for func in _GLOBAL_REGISTRY:
                    safe_args = copy.deepcopy(args)
                    safe_kwargs = copy.deepcopy(kwargs_variant)
                    try:
                        result, _ = measure_time(func, safe_args, safe_kwargs)
                        results[func.__name__] = result
                    except Exception as e:
                        results[func.__name__] = f"<Exception: {e}>"

                unique_results = list(results.values())
                if not all(res == unique_results[0] for res in unique_results):
                    variant_label = name or f"args={args}, kwargs={kwargs_variant}"
                    error_msg = f"Inconsistent outcomes for variant ({variant_label}):\n"
                    for name, res in results.items():
                        error_msg += f"  {name} -> {res}\n"
                    raise InconsistentOutcomesError(error_msg)

        adhoc_bench = bench(_GLOBAL_REGISTRY, variants=variants, **kwargs)
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
                
                # 2a. Run reference first
                if chall.reference:
                    ref_bench = bench(chall.reference, variants=current_variant_data, **kwargs)
                    for f in ref_bench.functions:
                        total_benchmark.add_function(f)
                    
                    ref_func_obj = ref_bench.get_function(ref_name)
                    ref_median = ref_func_obj.median_time(variant_label)
                    adaptive_timeout = max(ref_median * chall.timeout_multiplier, 0.001)

                # 2b. Run student functions
                chall_bench = bench(funcs, variants=current_variant_data, timeout=adaptive_timeout, **kwargs)
                
                for f in chall_bench.functions:
                    total_benchmark.add_function(f)
                    
                    # Correctness Check against Reference
                    status = f.get_status(variant_label)
                    if status == FailureType.NONE and chall.reference:
                        # Only check correctness if it didn't timeout or crash
                        try:
                            ref_res, _ = measure_time(chall.reference, copy.deepcopy(args), copy.deepcopy(kwargs_variant))
                            student_res, _ = measure_time(f._function, copy.deepcopy(args), copy.deepcopy(kwargs_variant))
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
