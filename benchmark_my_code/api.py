from typing import Any, Callable, List, Union, Iterable, Dict
from .orchestrator import bench, normalised_variants, format_parameters, BenchmarkingWorker, run_challenge
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
    Can be used as @benchit, @benchit(using=data), or @benchit(is_reference=True).
    """
    ensure_copy = kwargs.get('ensure_copy', arg if isinstance(arg, bool) else True)
    using = kwargs.get('using')
    is_reference = kwargs.get('is_reference', False)
    
    def decorator(func: Callable) -> Callable:
        func._bmc_ensure_copy = ensure_copy
        func._bmc_using = using
        func._bmc_is_reference = is_reference
        _GLOBAL_REGISTRY.append(func)
        return func

    if callable(arg):
        # We need to set default using/is_reference if used as bare @benchit
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

def find_user_frame():
    """
    Walks back the stack to find the first frame that is not in the benchmark_my_code package.
    This is robust against wrappers and different execution environments (Jupyter, etc.).
    """
    import os
    # Get the directory of the current file (api.py)
    package_dir = os.path.dirname(os.path.abspath(__file__))
    
    frame = sys._getframe(1)
    while frame:
        filename = frame.f_code.co_filename
        # Handle Jupyter/IPython pseudo-files
        if filename.startswith('<') and filename.endswith('>'):
            return frame
            
        frame_file = os.path.abspath(filename)
        if not frame_file.startswith(package_dir):
            return frame
        frame = frame.f_back
    return None

_VARIANT_CACHE: Dict[str, Any] = {}

def clear_registry():
    """Clears the global registries."""
    _GLOBAL_REGISTRY.clear()
    _CHALLENGE_REGISTRY.clear()
    _VARIANT_CACHE.clear()

from collections.abc import Iterable

def _resolve_variants_for_func(func: Callable, variants: Any) -> Any:
    """
    If variants is None, attempts to find a local/global iterable matching 
    the first parameter name of the function, OR a function matching
    the parameter name that yields data (DAG resolution).
    """
    if variants is not None:
        return variants
    
    # Story 2.2: Cache resolution by provider name to prevent generator exhaustion
    # and ensure multiple functions in the same run see the same data.
    
    # Check if the function has an explicit 'using' attribute from the decorator
    if hasattr(func, '_bmc_using') and func._bmc_using is not None:
        val = func._bmc_using
        if callable(val):
            cache_key = f"func:{id(val)}"
            if cache_key in _VARIANT_CACHE:
                return _VARIANT_CACHE[cache_key]
            try:
                provider_result = val()
                if isinstance(provider_result, Iterable) and not isinstance(provider_result, (str, bytes)):
                    res = list(provider_result)
                    _VARIANT_CACHE[cache_key] = res
                    return res
            except Exception:
                pass
        return val

    try:
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
    except (ValueError, TypeError):
        # Built-ins or functions without signatures
        params = []
    
    # Names to look for in order of priority:
    # 1. Each parameter name (e.g. 'data')
    # 2. 'scenarios' (global standard name)
    candidate_names = params + ['scenarios']
    
    # Use robust frame discovery
    frame = find_user_frame()
    while frame:
        # Search both locals and globals (prioritize locals)
        for name in candidate_names:
            # Check locals first
            val = frame.f_locals.get(name)
            if val is None:
                # Then check globals
                val = frame.f_globals.get(name)
            
            if val is not None:
                # Use id(val) for caching to handle generators/iterables
                cache_key = f"var:{id(val)}"
                if cache_key in _VARIANT_CACHE:
                    return _VARIANT_CACHE[cache_key]

                # If it's a function, it's a provider
                if callable(val):
                    # We don't want to call the function being benchmarked itself
                    if val == func:
                        continue
                    try:
                        provider_result = val()
                        if isinstance(provider_result, Iterable) and not isinstance(provider_result, (str, bytes)):
                            # Convert to list to prevent generator exhaustion
                            res = list(provider_result)
                            _VARIANT_CACHE[cache_key] = res
                            return res
                    except Exception:
                        continue
                
                # Simple iterable (exclude strings/bytes to avoid accidental character-by-character variants)
                if isinstance(val, Iterable) and not isinstance(val, (str, bytes)):
                    # Convert to list to prevent generator exhaustion
                    res = list(val)
                    _VARIANT_CACHE[cache_key] = res
                    return res
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
        if print_results:
            print("\n🚀 Running Ad-hoc Benchmarks...")

        if validate:
            if print_results:
                print("  Validating outcomes across all registered functions...")
            # For validation, we need a common variant set. 
            common_variants = variants
            if common_variants is None and _GLOBAL_REGISTRY:
                common_variants = _resolve_variants_for_func(_GLOBAL_REGISTRY[0], None)
            
            for (args, kwargs_variant, name, expected) in normalised_variants(common_variants):
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

        # Identify reference function if any
        ref_func = next((f for f in _GLOBAL_REGISTRY if getattr(f, '_bmc_is_reference', False)), None)
        
        for func in _GLOBAL_REGISTRY:
            if print_results:
                ref_tag = " [Reference]" if getattr(func, '_bmc_is_reference', False) else ""
                print(f"  - Benchmarking '{func.__name__}'{ref_tag}...", end="", flush=True)

            # Resolve variants for THIS function specifically if none provided globally
            func_variants = _resolve_variants_for_func(func, variants)
            
            # ...
            
            adhoc_bench = bench(func, variants=func_variants, **kwargs)
            
            if print_results:
                print(" DONE")
            
            # Correctness Check against Reference (if reference exists and is NOT this function)
            if ref_func and func != ref_func:
                for f_model in adhoc_bench.functions:
                    for variant_label in list(f_model._status.keys()):
                        if f_model.get_status(variant_label) == FailureType.NONE:
                            # Re-run both to compare (inefficient but safe for ad-hoc)
                            # Actual variants for this label:
                            for (args, kwargs_v, label, expected) in normalised_variants(func_variants):
                                if label == variant_label:
                                    worker = BenchmarkingWorker()
                                    ref_res, _ = worker.run(ref_func, copy.deepcopy(args), copy.deepcopy(kwargs_v))
                                    student_res, _ = worker.run(func, copy.deepcopy(args), copy.deepcopy(kwargs_v))
                                    if student_res != ref_res:
                                        f_model.record_status(variant_label, FailureType.CORRECTNESS)
                                    break

            for f in adhoc_bench.functions:
                total_benchmark.add_function(f)

    # 2. Run Challenge benchmarks
    by_challenge = {}
    for func, chall in _CHALLENGE_REGISTRY:
        if chall not in by_challenge:
            by_challenge[chall] = []
        by_challenge[chall].append(func)

    for chall, funcs in by_challenge.items():
        hints.extend(run_challenge(chall, funcs, total_benchmark, **kwargs))

    from .result import BenchmarkResult
    result = BenchmarkResult(total_benchmark)
    result.hints = hints
    
    if print_results:
        print(result)

    return result

