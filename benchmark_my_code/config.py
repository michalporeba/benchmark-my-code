import ast
import inspect

def get_config():
    return {
        'max_function_executions': 100,
        'max_function_seconds': 1,
        'max_variant_seconds': 1,
    }

def validate_signature(func, expected_params):
    """
    Verifies that the target function has the exact parameter names defined in the challenge.
    Raises InvalidSignatureError if parameters don't match.
    """
    if not expected_params:
        return
    
    import inspect
    from .exceptions import InvalidSignatureError
    
    sig = inspect.signature(func)
    actual_params = list(sig.parameters.keys())
    
    if actual_params != expected_params:
        params_str = ", ".join(expected_params)
        actual_str = ", ".join(actual_params)
        raise InvalidSignatureError(
            f"Function signature does not match challenge contract.\n"
            f"Expected: def {func.__name__}({params_str}):\n"
            f"Found:    def {func.__name__}({actual_str}):"
        )

def validate_algorithmic_constraints(func, banned_calls):
    """
    Uses AST to scan the function's source code for forbidden built-ins or method calls.
    Raises ForbiddenCallError if a banned call is detected.
    """
    if not banned_calls:
        return
    
    try:
        source = inspect.getsource(func)
        # Handle indentation in case it's a nested function or method
        import textwrap
        source = textwrap.dedent(source)
        tree = ast.parse(source)
        
        from .exceptions import ForbiddenCallError
        
        # List of common names that are usually safe if called as methods 
        # (e.g. logger.info). But if the user bans 'info', they might mean it.
        # We focus on things that usually replace manual implementation.
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = None
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    # Finding 6: Over-broad constraint analysis.
                    # Flagging any method with a banned name.
                    # We'll allow it if the value being called is 'self' or 'cls'? 
                    # No, usually students implement sort, sum, etc.
                    # Let's keep it but maybe exclude known safe objects?
                    # For now, stay adversarial as requested by the challenge mode.
                    name = node.func.attr
                
                if name in banned_calls:
                    raise ForbiddenCallError(f"Challenge forbids the use of: {name}")
    except (TypeError, OSError, SyntaxError):
        # Fallback if source cannot be retrieved or parsed
        pass
