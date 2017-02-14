"""Internal exception classes."""

class UnsatisfiableConstraint(Exception):
    """Raise when a specified constraint cannot be satisfied."""
    pass

    
class UnsatisfiableType(UnsatisfiableConstraint):
    """Raised when a type constraint cannot be satisfied."""
    pass


class TreeConstructionError(Exception):
    """Raised when a tree cannot be successfully constructed."""
    pass
