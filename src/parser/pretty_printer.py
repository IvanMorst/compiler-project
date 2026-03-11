from typing import Any, List
from src.parser.ast import *
from src.parser.visitor import ASTVisitor


class PrettyPrinter(ASTVisitor):
    """Красивый вывод AST в текстовом формате."""

    def __init__(self, indent_size: int = 2):
        self.indent_level = 0
        self.indent_size = indent_size
        self.output = []

    def indent(self) -> str:
        return " " * (self.indent_level * self.indent_size)

    def visit_program(self, node: ProgramNode) -> str:
        self.output.append(f"Program [line {node.line}]:")
        self.indent_level += 1
        for decl in node.declarations:
            decl.accept(self)
        self.indent_level -= 1
        return "\n".join(self.output)

    def visit_function_decl(self, node: FunctionDeclNode) -> Any:
        params = ", ".join(p.accept(self) for p in node.parameters)
        self.output.append(f"{self.indent()}FunctionDecl: {node.name} -> {node.return_type} [line {node.line}]:")
        self.indent_level += 1
        self.output.append(f"{self.indent()}Parameters: [{params}]")
        self.output.append(f"{self.indent()}Body:")
        node.body.accept(self)
        self.indent_level -= 1

    def visit_param(self, node: ParamNode) -> str:
        return f"{node.type_name} {node.name}"

    def visit_block_stmt(self, node: BlockStmtNode) -> Any:
        self.output.append(f"{self.indent()}Block [line {node.line}-...]:")
        self.indent_level += 1
        for stmt in node.statements:
            stmt.accept(self)
        self.indent_level -= 1

    def visit_var_decl_stmt(self, node: VarDeclStmtNode) -> Any:
        init = ""
        if node.initializer:
            init_val = node.initializer.accept(self)
            init = f" = {init_val}"
        self.output.append(f"{self.indent()}VarDecl: {node.type_name} {node.name}{init} [line {node.line}]")

    def visit_expr_stmt(self, node: ExprStmtNode) -> Any:
        expr = node.expression.accept(self)
        self.output.append(f"{self.indent()}ExprStmt: {expr} [line {node.line}]")

    def visit_if_stmt(self, node: IfStmtNode) -> Any:
        cond = node.condition.accept(self)
        self.output.append(f"{self.indent()}IfStmt [line {node.line}]:")
        self.indent_level += 1
        self.output.append(f"{self.indent()}Condition: {cond}")
        self.output.append(f"{self.indent()}Then:")
        node.then_branch.accept(self)
        if node.else_branch:
            self.output.append(f"{self.indent()}Else:")
            node.else_branch.accept(self)
        self.indent_level -= 1

    def visit_while_stmt(self, node: WhileStmtNode) -> Any:
        cond = node.condition.accept(self)
        self.output.append(f"{self.indent()}WhileStmt [line {node.line}]:")
        self.indent_level += 1
        self.output.append(f"{self.indent()}Condition: {cond}")
        self.output.append(f"{self.indent()}Body:")
        node.body.accept(self)
        self.indent_level -= 1

    def visit_for_stmt(self, node: ForStmtNode) -> Any:
        init = node.init.accept(self) if node.init else "None"
        cond = node.condition.accept(self) if node.condition else "None"
        update = node.update.accept(self) if node.update else "None"
        self.output.append(f"{self.indent()}ForStmt [line {node.line}]:")
        self.indent_level += 1
        self.output.append(f"{self.indent()}Init: {init}")
        self.output.append(f"{self.indent()}Condition: {cond}")
        self.output.append(f"{self.indent()}Update: {update}")
        self.output.append(f"{self.indent()}Body:")
        node.body.accept(self)
        self.indent_level -= 1

    def visit_return_stmt(self, node: ReturnStmtNode) -> Any:
        if node.value:
            val = node.value.accept(self)
            self.output.append(f"{self.indent()}Return: {val} [line {node.line}]")
        else:
            self.output.append(f"{self.indent()}Return: [line {node.line}]")

    def visit_empty_stmt(self, node: EmptyStmtNode) -> Any:
        self.output.append(f"{self.indent()}EmptyStmt [line {node.line}]")

    def visit_literal_expr(self, node: LiteralExprNode) -> str:
        return repr(node.value)

    def visit_identifier_expr(self, node: IdentifierExprNode) -> str:
        return node.name

    def visit_binary_expr(self, node: BinaryExprNode) -> str:
        left = node.left.accept(self)
        right = node.right.accept(self)
        return f"({left} {node.operator} {right})"

    def visit_unary_expr(self, node: UnaryExprNode) -> str:
        operand = node.operand.accept(self)
        return f"({node.operator}{operand})"

    def visit_call_expr(self, node: CallExprNode) -> str:
        callee = node.callee.accept(self)
        args = ", ".join(arg.accept(self) for arg in node.arguments)
        return f"{callee}({args})"

    def visit_assignment_expr(self, node: AssignmentExprNode) -> str:
        target = node.target.accept(self)
        value = node.value.accept(self)
        return f"({target} {node.operator} {value})"

    def visit_struct_decl(self, node: StructDeclNode) -> Any:
        self.output.append(f"{self.indent()}StructDecl: {node.name} [line {node.line}]:")
        self.indent_level += 1
        for field in node.fields:
            field.accept(self)
        self.indent_level -= 1