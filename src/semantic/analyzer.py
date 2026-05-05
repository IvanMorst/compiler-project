from typing import List, Optional, Dict
from src.parser.ast import *
from src.parser.visitor import ASTVisitor
from src.lexer.token import TokenType
from .symbol_table import SymbolTable, Symbol, SymbolKind
from .type_system import (
    Type, INT, FLOAT, BOOL, VOID, STRING, StructType, FunctionType
)
from .errors import SemanticError


class SemanticAnalyzer(ASTVisitor):
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors: List[SemanticError] = []
        self.current_function_return_type: Optional[Type] = None
        self.has_return_statement = False  # Track if function has return

    def analyze(self, program: ProgramNode) -> None:
        """Run all semantic checks."""
        try:
            program.accept(self)
        except SemanticError as e:
            self.errors.append(e)

    def get_decorated_ast(self) -> ProgramNode:
        # AST is already decorated in-place
        pass

    # ---------- Helper ----------
    def _error(self, msg: str, node: ASTNode):
        err = SemanticError(msg, node.line, node.column)
        self.errors.append(err)

    def _type_from_name(self, name: str, node: ASTNode = None) -> Type:
        if name == "int":
            return INT
        elif name == "float":
            return FLOAT
        elif name == "bool":
            return BOOL
        elif name == "void":
            return VOID
        elif name == "string":
            return STRING
        else:
            # Possibly a struct type
            sym = self.symbol_table.lookup(name)
            if sym and sym.kind == SymbolKind.STRUCT:
                return StructType(sym.name, sym.struct_fields)
            else:
                if node:
                    self._error(f"Unknown type '{name}'", node)
                return VOID  # dummy

    # ---------- Visitor methods ----------
    def visit_program(self, node: ProgramNode):
        # First pass: collect all struct and function declarations
        for decl in node.declarations:
            if isinstance(decl, StructDeclNode):
                self._declare_struct(decl)
            elif isinstance(decl, FunctionDeclNode):
                self._declare_function_header(decl)

        # Second pass: check bodies
        for decl in node.declarations:
            if isinstance(decl, FunctionDeclNode):
                decl.accept(self)
            elif isinstance(decl, VarDeclStmtNode):
                self.visit_var_decl_stmt(decl)
            elif isinstance(decl, ExprStmtNode):
                self.visit_expr_stmt(decl)
            elif isinstance(decl, EmptyStmtNode):
                pass

    def _declare_struct(self, node: StructDeclNode):
        fields = {}
        for field in node.fields:
            f_type = self._type_from_name(field.type_name, field)
            fields[field.name] = f_type
        sym = Symbol(
            name=node.name, type_=StructType(node.name, fields),
            kind=SymbolKind.STRUCT, line=node.line, column=node.column,
            struct_fields=fields
        )
        try:
            self.symbol_table.insert(node.name, sym)
        except SemanticError as e:
            self.errors.append(e)

    def _declare_function_header(self, node: FunctionDeclNode):
        param_types = [self._type_from_name(p.type_name, p) for p in node.parameters]
        return_type = self._type_from_name(node.return_type, node)
        func_type = FunctionType(param_types, return_type)
        sym = Symbol(
            name=node.name, type_=func_type, kind=SymbolKind.FUNCTION,
            line=node.line, column=node.column, params=param_types,
            return_type=return_type
        )
        try:
            self.symbol_table.insert(node.name, sym)
        except SemanticError as e:
            self.errors.append(e)

    def visit_function_decl(self, node: FunctionDeclNode):
        # Enter function scope
        self.symbol_table.enter_scope()
        self.current_function_return_type = self._type_from_name(node.return_type, node)
        self.has_return_statement = False

        # Register parameters
        for param in node.parameters:
            param_type = self._type_from_name(param.type_name, param)
            try:
                self.symbol_table.insert(param.name, Symbol(
                    name=param.name, type_=param_type, kind=SymbolKind.PARAMETER,
                    line=param.line, column=param.column
                ))
            except SemanticError as e:
                self.errors.append(e)

        # Analyze body
        if node.body:
            node.body.accept(self)

        # Check return type consistency (basic check)
        if self.current_function_return_type != VOID and not self.has_return_statement:
            # This is optional - some languages allow this
            pass

        self.symbol_table.exit_scope()

    def visit_param(self, node: ParamNode):
        pass  # handled in function_decl

    def visit_struct_decl(self, node: StructDeclNode):
        pass  # already declared

    # ---- Statements ----
    def visit_block_stmt(self, node: BlockStmtNode):
        self.symbol_table.enter_scope()
        for stmt in node.statements:
            stmt.accept(self)
        self.symbol_table.exit_scope()

    def visit_var_decl_stmt(self, node: VarDeclStmtNode):
        var_type = self._type_from_name(node.type_name, node)
        if node.initializer:
            init_type = node.initializer.accept(self)
            if init_type and var_type != VOID and not var_type.is_compatible(init_type):
                self._error(
                    f"Type mismatch in variable '{node.name}': cannot assign '{init_type}' to '{var_type}'",
                    node
                )
        sym = Symbol(
            name=node.name, type_=var_type, kind=SymbolKind.VARIABLE,
            line=node.line, column=node.column
        )
        try:
            self.symbol_table.insert(node.name, sym)
        except SemanticError as e:
            self.errors.append(e)
        if node.initializer:
            node.initializer.semantic_type = init_type

    def visit_expr_stmt(self, node: ExprStmtNode):
        if node.expression:
            node.expression.accept(self)

    def visit_if_stmt(self, node: IfStmtNode):
        if node.condition:
            cond_type = node.condition.accept(self)
            if cond_type and cond_type != BOOL:
                self._error("Condition of 'if' must be boolean", node.condition)
        if node.then_branch:
            node.then_branch.accept(self)
        if node.else_branch:
            node.else_branch.accept(self)

    def visit_while_stmt(self, node: WhileStmtNode):
        if node.condition:
            cond_type = node.condition.accept(self)
            if cond_type and cond_type != BOOL:
                self._error("Condition of 'while' must be boolean", node.condition)
        if node.body:
            node.body.accept(self)

    def visit_for_stmt(self, node: ForStmtNode):
        if node.init:
            node.init.accept(self)
        if node.condition:
            cond_type = node.condition.accept(self)
            if cond_type and cond_type != BOOL:
                self._error("Condition of 'for' must be boolean", node.condition)
        if node.update:
            node.update.accept(self)
        if node.body:
            node.body.accept(self)

    def visit_return_stmt(self, node: ReturnStmtNode):
        self.has_return_statement = True
        if self.current_function_return_type is None:
            self._error("Return statement outside of function", node)
            return
        if node.value:
            ret_type = node.value.accept(self)
            if ret_type and self.current_function_return_type != VOID:
                if not self.current_function_return_type.is_compatible(ret_type):
                    self._error(
                        f"Return type mismatch: expected '{self.current_function_return_type}', got '{ret_type}'",
                        node.value
                    )
        else:
            if self.current_function_return_type != VOID:
                self._error("Non-void function must return a value", node)

    def visit_empty_stmt(self, node: EmptyStmtNode):
        pass

    # ---- Expressions (return Type) ----
    def visit_literal_expr(self, node: LiteralExprNode) -> Type:
        if node.token_type == TokenType.INT_LITERAL:
            t = INT
        elif node.token_type == TokenType.FLOAT_LITERAL:
            t = FLOAT
        elif node.token_type == TokenType.STRING_LITERAL:
            t = STRING
        elif node.token_type in (TokenType.KW_TRUE, TokenType.KW_FALSE):
            t = BOOL
        else:
            t = VOID
        node.semantic_type = t
        return t

    def visit_identifier_expr(self, node: IdentifierExprNode) -> Type:
        name = node.name
        sym = self.symbol_table.lookup(name)
        if sym is None:
            self._error(f"Undeclared identifier '{name}'", node)
            node.semantic_type = VOID
            return VOID
        node.symbol = sym
        node.semantic_type = sym.type
        return sym.type

    def visit_binary_expr(self, node: BinaryExprNode) -> Type:
        left_t = node.left.accept(self) if node.left else None
        right_t = node.right.accept(self) if node.right else None
        if left_t is None or right_t is None:
            return VOID
        op = node.operator
        # Arithmetic ops
        if op in ('+', '-', '*', '/', '%'):
            if left_t == INT and right_t == INT:
                result = INT
            elif left_t == FLOAT and right_t == FLOAT:
                result = FLOAT
            elif (left_t == INT and right_t == FLOAT) or (left_t == FLOAT and right_t == INT):
                result = FLOAT
            else:
                self._error(f"Type mismatch in binary operator '{op}': {left_t} and {right_t}", node)
                result = left_t  # dummy
        elif op in ('==', '!=', '<', '<=', '>', '>='):
            if left_t in (INT, FLOAT) and right_t in (INT, FLOAT):
                result = BOOL
            else:
                self._error(f"Comparison operator '{op}' requires numeric operands", node)
                result = BOOL
        elif op in ('&&', '||'):
            if left_t == BOOL and right_t == BOOL:
                result = BOOL
            else:
                self._error(f"Logical operator '{op}' requires boolean operands", node)
                result = BOOL
        else:
            result = left_t
        node.semantic_type = result
        return result

    def visit_unary_expr(self, node: UnaryExprNode) -> Type:
        operand_t = node.operand.accept(self) if node.operand else None
        if operand_t is None:
            return VOID
        op = node.operator
        if op == '-':
            if operand_t in (INT, FLOAT):
                result = operand_t
            else:
                self._error(f"Unary '-' requires numeric operand, got {operand_t}", node)
                result = operand_t
        elif op == '!':
            if operand_t == BOOL:
                result = BOOL
            else:
                self._error(f"Unary '!' requires boolean operand, got {operand_t}", node)
                result = BOOL
        else:
            result = operand_t
        node.semantic_type = result
        return result

    def visit_call_expr(self, node: CallExprNode) -> Type:
        callee = node.callee
        if not isinstance(callee, IdentifierExprNode):
            self._error("Function call target must be an identifier", callee)
            return VOID

        func_name = callee.name
        sym = self.symbol_table.lookup(func_name)

        if sym is None:
            self._error(f"Undeclared function '{func_name}'", callee)
            # Still analyze arguments
            for arg in node.arguments:
                arg.accept(self)
            return VOID

        if sym.kind != SymbolKind.FUNCTION:
            self._error(f"'{func_name}' is not a function", callee)
            for arg in node.arguments:
                arg.accept(self)
            return VOID

        func_type = sym.type  # expected FunctionType
        if not isinstance(func_type, FunctionType):
            self._error(f"'{func_name}' has invalid function type", callee)
            for arg in node.arguments:
                arg.accept(self)
            return VOID

        # Check argument count
        if len(node.arguments) != len(func_type.param_types):
            self._error(
                f"Function '{func_name}' expects {len(func_type.param_types)} arguments, got {len(node.arguments)}",
                node
            )

        # Check argument types (only if counts match)
        for i, arg in enumerate(node.arguments):
            arg_type = arg.accept(self)
            if arg_type and i < len(func_type.param_types):
                expected = func_type.param_types[i]
                if not expected.is_compatible(arg_type):
                    self._error(
                        f"Argument {i + 1} of '{func_name}': expected '{expected}', got '{arg_type}'",
                        arg
                    )

        node.semantic_type = func_type.return_type
        return func_type.return_type

    def visit_assignment_expr(self, node: AssignmentExprNode) -> Type:
        target_type = node.target.accept(self) if node.target else None
        value_type = node.value.accept(self) if node.value else None

        if target_type is not None and value_type is not None:
            if not target_type.is_compatible(value_type):
                self._error(
                    f"Type mismatch in assignment: cannot assign '{value_type}' to '{target_type}'",
                    node
                )

        node.semantic_type = target_type or VOID
        return node.semantic_type