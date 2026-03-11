import json
from typing import Any, Dict
from src.parser.ast import *
from src.parser.visitor import ASTVisitor


class JSONGenerator(ASTVisitor):
    """Генератор JSON представления AST."""

    def generate(self, node: ASTNode) -> str:
        """Генерирует JSON строку из AST."""
        result = node.accept(self)
        return json.dumps(result, indent=2, ensure_ascii=False)

    def _node_to_dict(self, node_type: str, **kwargs) -> Dict[str, Any]:
        """Создаёт словарь с метаданными узла."""
        return {
            "node_type": node_type,
            **kwargs
        }

    def visit_program(self, node: ProgramNode) -> Dict:
        declarations = [decl.accept(self) for decl in node.declarations]
        return self._node_to_dict("Program", declarations=declarations)

    def visit_function_decl(self, node: FunctionDeclNode) -> Dict:
        params = [param.accept(self) for param in node.parameters]
        body = node.body.accept(self)
        return self._node_to_dict(
            "FunctionDecl",
            name=node.name,
            return_type=node.return_type,
            parameters=params,
            body=body,
            line=node.line,
            column=node.column
        )

    def visit_param(self, node: ParamNode) -> Dict:
        return self._node_to_dict(
            "Param",
            type_name=node.type_name,
            name=node.name,
            line=node.line,
            column=node.column
        )

    def visit_struct_decl(self, node: StructDeclNode) -> Dict:
        fields = [field.accept(self) for field in node.fields]
        return self._node_to_dict(
            "StructDecl",
            name=node.name,
            fields=fields,
            line=node.line,
            column=node.column
        )

    def visit_var_decl_stmt(self, node: VarDeclStmtNode) -> Dict:
        init = node.initializer.accept(self) if node.initializer else None
        return self._node_to_dict(
            "VarDecl",
            type_name=node.type_name,
            name=node.name,
            initializer=init,
            line=node.line,
            column=node.column
        )

    def visit_block_stmt(self, node: BlockStmtNode) -> Dict:
        statements = [stmt.accept(self) for stmt in node.statements]
        return self._node_to_dict(
            "Block",
            statements=statements,
            line=node.line,
            column=node.column
        )

    def visit_expr_stmt(self, node: ExprStmtNode) -> Dict:
        expr = node.expression.accept(self)
        return self._node_to_dict(
            "ExprStmt",
            expression=expr,
            line=node.line,
            column=node.column
        )

    def visit_if_stmt(self, node: IfStmtNode) -> Dict:
        cond = node.condition.accept(self)
        then_branch = node.then_branch.accept(self)
        else_branch = node.else_branch.accept(self) if node.else_branch else None
        return self._node_to_dict(
            "IfStmt",
            condition=cond,
            then_branch=then_branch,
            else_branch=else_branch,
            line=node.line,
            column=node.column
        )

    def visit_while_stmt(self, node: WhileStmtNode) -> Dict:
        cond = node.condition.accept(self)
        body = node.body.accept(self)
        return self._node_to_dict(
            "WhileStmt",
            condition=cond,
            body=body,
            line=node.line,
            column=node.column
        )

    def visit_for_stmt(self, node: ForStmtNode) -> Dict:
        init = node.init.accept(self) if node.init else None
        cond = node.condition.accept(self) if node.condition else None
        update = node.update.accept(self) if node.update else None
        body = node.body.accept(self)
        return self._node_to_dict(
            "ForStmt",
            init=init,
            condition=cond,
            update=update,
            body=body,
            line=node.line,
            column=node.column
        )

    def visit_return_stmt(self, node: ReturnStmtNode) -> Dict:
        value = node.value.accept(self) if node.value else None
        return self._node_to_dict(
            "ReturnStmt",
            value=value,
            line=node.line,
            column=node.column
        )

    def visit_empty_stmt(self, node: EmptyStmtNode) -> Dict:
        return self._node_to_dict(
            "EmptyStmt",
            line=node.line,
            column=node.column
        )

    def visit_literal_expr(self, node: LiteralExprNode) -> Dict:
        return self._node_to_dict(
            "Literal",
            value=node.value,
            type_name=node.token_type.name,
            line=node.line,
            column=node.column
        )

    def visit_identifier_expr(self, node: IdentifierExprNode) -> Dict:
        return self._node_to_dict(
            "Identifier",
            name=node.name,
            line=node.line,
            column=node.column
        )

    def visit_binary_expr(self, node: BinaryExprNode) -> Dict:
        left = node.left.accept(self)
        right = node.right.accept(self)
        return self._node_to_dict(
            "BinaryExpr",
            operator=node.operator,
            left=left,
            right=right,
            line=node.line,
            column=node.column
        )

    def visit_unary_expr(self, node: UnaryExprNode) -> Dict:
        operand = node.operand.accept(self)
        return self._node_to_dict(
            "UnaryExpr",
            operator=node.operator,
            operand=operand,
            line=node.line,
            column=node.column
        )

    def visit_call_expr(self, node: CallExprNode) -> Dict:
        callee = node.callee.accept(self)
        args = [arg.accept(self) for arg in node.arguments]
        return self._node_to_dict(
            "CallExpr",
            callee=callee,
            arguments=args,
            line=node.line,
            column=node.column
        )

    def visit_assignment_expr(self, node: AssignmentExprNode) -> Dict:
        target = node.target.accept(self)
        value = node.value.accept(self)
        return self._node_to_dict(
            "AssignmentExpr",
            operator=node.operator,
            target=target,
            value=value,
            line=node.line,
            column=node.column
        )