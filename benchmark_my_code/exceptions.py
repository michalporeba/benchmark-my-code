class InconsistentOutcomesError(Exception):
    """Raised when different functions return different results for the same variant."""
    pass

class InvalidSignatureError(Exception):
    """Raised when a function signature does not match the expected challenge contract."""
    pass

class ForbiddenCallError(Exception):
    """Raised when a forbidden function call is detected via AST analysis."""
    pass
