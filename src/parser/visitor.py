from abc import ABC, abstractmethod
from typing import Any


class ASTVisitor(ABC):
    """Базовый класс Visitor для обхода AST."""

    @abstractmethod
    def visit_program(self, node: 'ProgramNode') -> Any:
        pass

    @abstractmethod
    def visit_literal_expr(self, node: 'LiteralExprNode') -> Any:
        pass

    @abstractmethod
    def visit_identifier_expr(self, node: 'IdentifierExprNode') -> Any:
        pass

    @abstractmethod
    def visit_binary_expr(self, node: 'BinaryExprNode') -> Any:
        pass

    @abstractmethod
    def visit_unary_expr(self, node: 'UnaryExprNode') -> Any:
        pass

    @abstractmethod
    def visit_call_expr(self, node: 'CallExprNode') -> Any:
        pass

    @abstractmethod
    def visit_assignment_expr(self, node: 'AssignmentExprNode') -> Any:
        pass

    @abstractmethod
    def visit_block_stmt(self, node: 'BlockStmtNode') -> Any:
        pass

    @abstractmethod
    def visit_expr_stmt(self, node: 'ExprStmtNode') -> Any:
        pass

    @abstractmethod
    def visit_if_stmt(self, node: 'IfStmtNode') -> Any:
        pass

    @abstractmethod
    def visit_while_stmt(self, node: 'WhileStmtNode') -> Any:
        pass

    @abstractmethod
    def visit_for_stmt(self, node: 'ForStmtNode') -> Any:
        pass

    @abstractmethod
    def visit_return_stmt(self, node: 'ReturnStmtNode') -> Any:
        pass

    @abstractmethod
    def visit_var_decl_stmt(self, node: 'VarDeclStmtNode') -> Any:
        pass

    @abstractmethod
    def visit_empty_stmt(self, node: 'EmptyStmtNode') -> Any:
        pass

    @abstractmethod
    def visit_param(self, node: 'ParamNode') -> Any:
        pass

    @abstractmethod
    def visit_function_decl(self, node: 'FunctionDeclNode') -> Any:
        pass

    @abstractmethod
    def visit_struct_decl(self, node: 'StructDeclNode') -> Any:
        pass