from enum import Enum, auto
from typing import Dict, List, Optional
from .type_system import Type, VOID
from .errors import SemanticError

class SymbolKind(Enum):
    VARIABLE = auto()
    FUNCTION = auto()
    PARAMETER = auto()
    STRUCT = auto()

class Symbol:
    def __init__(self, name: str, type_: Type, kind: SymbolKind,
                 line: int, column: int, params: List[Type] = None,
                 return_type: Type = None, struct_fields: Dict[str, Type] = None):
        self.name = name
        self.type = type_
        self.kind = kind
        self.line = line
        self.column = column
        self.params = params or []          # for functions
        self.return_type = return_type or VOID
        self.struct_fields = struct_fields or {}  # for struct

    def __repr__(self):
        return f"<{self.kind.name} {self.name}:{self.type}>"

class Scope:
    def __init__(self, parent: Optional['Scope'] = None):
        self.symbols: Dict[str, Symbol] = {}
        self.parent = parent
        self.children: List['Scope'] = []

    def insert(self, name: str, symbol: Symbol):
        if name in self.symbols:
            existing = self.symbols[name]
            raise SemanticError(
                f"Duplicate declaration of '{name}' (first declared at line {existing.line})",
                symbol.line, symbol.column
            )
        self.symbols[name] = symbol

    def lookup_local(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)

    def lookup(self, name: str) -> Optional[Symbol]:
        scope = self
        while scope:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None

class SymbolTable:
    def __init__(self):
        self.root = Scope()
        self.current_scope = self.root

    def enter_scope(self):
        new_scope = Scope(self.current_scope)
        self.current_scope.children.append(new_scope)
        self.current_scope = new_scope

    def exit_scope(self):
        if self.current_scope.parent is None:
            raise Exception("Cannot exit global scope")
        self.current_scope = self.current_scope.parent

    def insert(self, name: str, symbol: Symbol):
        self.current_scope.insert(name, symbol)

    def lookup(self, name: str) -> Optional[Symbol]:
        return self.current_scope.lookup(name)

    def lookup_local(self, name: str) -> Optional[Symbol]:
        return self.current_scope.lookup_local(name)

    def get_all_symbols(self) -> Dict[str, List[Symbol]]:
        """Collect all symbols per scope for debugging."""
        result = {}
        def traverse(scope, depth):
            prefix = f"depth_{depth}"
            for name, sym in scope.symbols.items():
                result.setdefault(prefix, []).append(sym)
            for child in scope.children:
                traverse(child, depth + 1)
        traverse(self.root, 0)
        return result