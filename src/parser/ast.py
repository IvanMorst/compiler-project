from abc import ABC, abstractmethod
from typing import List, Optional, Union, Any
from enum import Enum
from src.lexer.token import TokenType


class ASTNode(ABC):
    """Базовый класс для всех узлов AST."""
    def __init__(self, line: int, column: int):
        self.line = line
        self.column = column

    @abstractmethod
    def accept(self, visitor: 'ASTVisitor') -> Any:
        pass


# ---- Expression Nodes ----

class ExpressionNode(ASTNode, ABC):
    """Базовый класс для выражений."""
    pass


class LiteralExprNode(ExpressionNode):
    """Литерал: число, строка, булево значение."""
    def __init__(self, line: int, column: int, value: Union[int, float, str, bool], token_type: TokenType):
        super().__init__(line, column)
        self.value = value
        self.token_type = token_type

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_literal_expr(self)


class IdentifierExprNode(ExpressionNode):
    """Идентификатор (переменная, функция, структура)."""
    def __init__(self, line: int, column: int, name: str):
        super().__init__(line, column)
        self.name = name

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_identifier_expr(self)


class BinaryExprNode(ExpressionNode):
    """Бинарная операция: a + b, a * b, a && b и т.д."""
    def __init__(self, line: int, column: int,
                 left: ExpressionNode,
                 operator: str,
                 right: ExpressionNode):
        super().__init__(line, column)
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_binary_expr(self)


class UnaryExprNode(ExpressionNode):
    """Унарная операция: -a, !b."""
    def __init__(self, line: int, column: int,
                 operator: str,
                 operand: ExpressionNode):
        super().__init__(line, column)
        self.operator = operator
        self.operand = operand

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_unary_expr(self)


class CallExprNode(ExpressionNode):
    """Вызов функции: foo(1, 2, 3)."""
    def __init__(self, line: int, column: int,
                 callee: ExpressionNode,
                 arguments: List[ExpressionNode]):
        super().__init__(line, column)
        self.callee = callee
        self.arguments = arguments

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_call_expr(self)


class AssignmentExprNode(ExpressionNode):
    """Присваивание: x = 5, x += 1 и т.д."""
    def __init__(self, line: int, column: int,
                 target: ExpressionNode,
                 operator: str,
                 value: ExpressionNode):
        super().__init__(line, column)
        self.target = target
        self.operator = operator
        self.value = value

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_assignment_expr(self)


# ---- Statement Nodes ----

class StatementNode(ASTNode, ABC):
    """Базовый класс для инструкций."""
    pass


class BlockStmtNode(StatementNode):
    """Блок инструкций: { ... }."""
    def __init__(self, line: int, column: int, statements: List[StatementNode]):
        super().__init__(line, column)
        self.statements = statements

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_block_stmt(self)


class ExprStmtNode(StatementNode):
    """Инструкция-выражение: x = 5; foo();"""
    def __init__(self, line: int, column: int, expression: ExpressionNode):
        super().__init__(line, column)
        self.expression = expression

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_expr_stmt(self)


class IfStmtNode(StatementNode):
    """Условная инструкция: if (cond) then [else]."""
    def __init__(self, line: int, column: int,
                 condition: ExpressionNode,
                 then_branch: StatementNode,
                 else_branch: Optional[StatementNode] = None):
        super().__init__(line, column)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_if_stmt(self)


class WhileStmtNode(StatementNode):
    """Цикл while: while (cond) body."""
    def __init__(self, line: int, column: int,
                 condition: ExpressionNode,
                 body: StatementNode):
        super().__init__(line, column)
        self.condition = condition
        self.body = body

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_while_stmt(self)


class ForStmtNode(StatementNode):
    """Цикл for: for (init; cond; update) body."""
    def __init__(self, line: int, column: int,
                 init: Optional[StatementNode],
                 condition: Optional[ExpressionNode],
                 update: Optional[ExpressionNode],
                 body: StatementNode):
        super().__init__(line, column)
        self.init = init
        self.condition = condition
        self.update = update
        self.body = body

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_for_stmt(self)


class ReturnStmtNode(StatementNode):
    """Инструкция return: return [value];"""
    def __init__(self, line: int, column: int,
                 value: Optional[ExpressionNode] = None):
        super().__init__(line, column)
        self.value = value

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_return_stmt(self)


class VarDeclStmtNode(StatementNode):
    """Объявление переменной: int x = 5;"""
    def __init__(self, line: int, column: int,
                 type_name: str,
                 name: str,
                 initializer: Optional[ExpressionNode] = None):
        super().__init__(line, column)
        self.type_name = type_name
        self.name = name
        self.initializer = initializer

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_var_decl_stmt(self)


class EmptyStmtNode(StatementNode):
    """Пустая инструкция: ;"""
    def __init__(self, line: int, column: int):
        super().__init__(line, column)

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_empty_stmt(self)


# ---- Declaration Nodes ----

class DeclarationNode(ASTNode, ABC):
    """Базовый класс для объявлений."""
    pass


class ParamNode(ASTNode):
    """Параметр функции: int x"""
    def __init__(self, line: int, column: int,
                 type_name: str,
                 name: str):
        super().__init__(line, column)
        self.type_name = type_name
        self.name = name

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_param(self)


class FunctionDeclNode(DeclarationNode):
    """Объявление функции: fn foo() -> int { ... }"""
    def __init__(self, line: int, column: int,
                 name: str,
                 parameters: List[ParamNode],
                 return_type: str,
                 body: BlockStmtNode):
        super().__init__(line, column)
        self.name = name
        self.parameters = parameters
        self.return_type = return_type
        self.body = body

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_function_decl(self)


class StructDeclNode(DeclarationNode):
    """Объявление структуры: struct Point { int x; int y; }"""
    def __init__(self, line: int, column: int,
                 name: str,
                 fields: List[VarDeclStmtNode]):
        super().__init__(line, column)
        self.name = name
        self.fields = fields

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_struct_decl(self)


# ---- Program Node ----

class ProgramNode(ASTNode):
    """Корневой узел программы."""
    def __init__(self, declarations: List[ASTNode]):
        super().__init__(1, 1)
        self.declarations = declarations

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_program(self)