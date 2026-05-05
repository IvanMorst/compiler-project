from enum import Enum, auto
from typing import Dict, Optional, List

class TypeKind(Enum):
    INT = auto()
    FLOAT = auto()
    BOOL = auto()
    VOID = auto()
    STRING = auto()
    STRUCT = auto()
    FUNCTION = auto()

class Type:
    """Base class for all types."""
    def __init__(self, kind: TypeKind):
        self.kind = kind

    def is_compatible(self, other: 'Type') -> bool:
        """Check if self can be assigned from other (widening allowed)."""
        if self.kind == other.kind:
            if self.kind == TypeKind.STRUCT:
                return self.name == other.name   # nominal struct typing
            return True
        # int -> float widening
        if self.kind == TypeKind.FLOAT and other.kind == TypeKind.INT:
            return True
        return False

    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        if self.kind != other.kind:
            return False
        if self.kind == TypeKind.STRUCT:
            return self.name == other.name
        return True

    def __repr__(self):
        return str(self.kind.name).lower()

class IntType(Type):
    def __init__(self):
        super().__init__(TypeKind.INT)

class FloatType(Type):
    def __init__(self):
        super().__init__(TypeKind.FLOAT)

class BoolType(Type):
    def __init__(self):
        super().__init__(TypeKind.BOOL)

class VoidType(Type):
    def __init__(self):
        super().__init__(TypeKind.VOID)

class StringType(Type):
    def __init__(self):
        super().__init__(TypeKind.STRING)

class StructType(Type):
    def __init__(self, name: str, fields: Dict[str, 'Type'] = None):
        super().__init__(TypeKind.STRUCT)
        self.name = name
        self.fields = fields or {}  # field_name -> Type

class FunctionType(Type):
    def __init__(self, param_types: List['Type'], return_type: 'Type'):
        super().__init__(TypeKind.FUNCTION)
        self.param_types = param_types
        self.return_type = return_type

# Convenience constants
INT = IntType()
FLOAT = FloatType()
BOOL = BoolType()
VOID = VoidType()
STRING = StringType()