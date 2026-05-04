import argparse
import importlib.util
import os
import sys
import ast
import hashlib
import contextlib
from typing import List, Optional
from .api import run_benchmarks, clear_registry

def is_safe_value(node):
    """
    Checks if an AST node is a 'safe' value (no side-effect calls).
    Recursive check for collections.
    """
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return all(is_safe_value(el) for el in node.elts)
    if isinstance(node, ast.Dict):
        return all(is_safe_value(k) for k in node.keys if k is not None) and \
               all(is_safe_value(v) for v in node.values)
    if isinstance(node, ast.Name):
        # We allow names (variables) but not calls to them in Assignments
        return True
    return False

@contextlib.contextmanager
def sys_path_context(path: str):
    """Temporarily adds a path to sys.path."""
    added = False
    if path not in sys.path:
        sys.path.insert(0, path)
        added = True
    try:
        yield
    finally:
        if added:
            try:
                sys.path.remove(path)
            except ValueError:
                pass

def has_benchmarks(file_path: str) -> bool:
    """Uses AST to check if a file contains @benchit or @challenge decorators."""
    try:
        with open(file_path, "r") as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    # Handle @dec, @dec(), @mod.dec, @mod.dec()
                    d_node = decorator
                    if isinstance(d_node, ast.Call):
                        d_node = d_node.func
                    
                    if isinstance(d_node, ast.Name):
                        if d_node.id in ("benchit", "challenge"):
                            return True
                    elif isinstance(d_node, ast.Attribute) and d_node.attr in ("benchit", "challenge"):
                        return True
    except Exception:
        return False
    return False

def find_benchmarks(path: str) -> List[str]:
    """Recursively finds all .py files with benchmarks in a directory, or returns the file itself."""
    if os.path.isfile(path):
        return [path] if path.endswith(".py") and has_benchmarks(path) else []
    
    benchmarks = []
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py") and not file.startswith("_"):
                    file_path = os.path.join(root, file)
                    if has_benchmarks(file_path):
                        benchmarks.append(file_path)
    return benchmarks

def load_benchmarks_safely(file_path: str):
    """
    Parses the file with AST, removes top-level script statements, 
    and executes the result to populate the registry without side effects.
    """
    with open(file_path, "r") as f:
        source = f.read()
    
    tree = ast.parse(source)
    
    # Filter top-level nodes: keep only imports, classes, and functions.
    # We also keep assignments to standard parametrization names like 'data', 'scenarios'
    safe_nodes = []
    allowed_params = {"data", "scenarios"}
    
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef)):
            safe_nodes.append(node)
        elif isinstance(node, ast.ClassDef):
            # Class bodies can have side effects too (e.g. prints), 
            # but we need them for method benchmarks if we ever support them.
            # For now, keep them but consider hardening later.
            safe_nodes.append(node)
        elif isinstance(node, ast.Assign):
            # Handle both simple assignments and unpacking
            targets = []
            for t in node.targets:
                if isinstance(t, ast.Name):
                    targets.append(t.id)
                elif isinstance(t, (ast.Tuple, ast.List)):
                    for elt in t.elts:
                        if isinstance(elt, ast.Name):
                            targets.append(elt.id)
            
            if any(name in allowed_params for name in targets):
                if is_safe_value(node.value):
                    safe_nodes.append(node)

    tree.body = safe_nodes
    
    # Create a unique module name to avoid collisions
    abs_path = os.path.abspath(file_path)
    file_hash = hashlib.md5(abs_path.encode()).hexdigest()[:12]
    module_name = f"bench_module_{file_hash}"
    
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        return None
    module = importlib.util.module_from_spec(spec)
    
    # Properly set up for relative imports
    module.__package__ = "" # Default to top-level if not in a package
    # Inject into sys.modules so imports in the module can find it
    sys.modules[module_name] = module
    
    # Add the file's directory to sys.path temporarily
    file_dir = os.path.dirname(abs_path)
    with sys_path_context(file_dir):
        try:
            # Execute the transformed AST in the module's namespace
            code = compile(tree, filename=file_path, mode="exec")
            exec(code, module.__dict__)
        except Exception:
            # Clean up sys.modules if execution fails
            sys.modules.pop(module_name, None)
            raise
    
    return module

def main():
    parser = argparse.ArgumentParser(prog="benchit", description="Benchmark My Code CLI runner.")
    parser.add_argument("path", help="The Python file or directory to benchmark.")
    parser.add_argument("--max-executions", type=int, default=100)
    parser.add_argument("--warmup-executions", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=100.0)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' not found.")
        sys.exit(1)

    benchmark_files = find_benchmarks(args.path)
    if not benchmark_files:
        print(f"No benchmark files found in '{args.path}'.")
        sys.exit(0)

    # 1. Clear registry to ensure a clean start
    clear_registry()

    for file in benchmark_files:
        try:
            load_benchmarks_safely(file)
        except Exception as e:
            print(f"Error loading benchmarks from '{file}': {e}")
            continue

    # 3. Run benchmarks
    try:
        run_benchmarks(
            max_executions=args.max_executions,
            warmup_executions=args.warmup_executions,
            batch_size=args.batch_size,
            timeout=args.timeout
        )
    except Exception as e:
        print(f"Error during benchmarking: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
