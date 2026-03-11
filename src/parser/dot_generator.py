from typing import List, Set
from src.parser.ast import *
from src.parser.visitor import ASTVisitor


class DOTGenerator(ASTVisitor):
    """Генератор Graphviz DOT для визуализации AST."""

    def __init__(self):
        self.nodes: List[str] = []
        self.edges: List[str] = []
        self.counter = 0
        self.node_stack: List[int] = []
        self.node_colors = {
            'ProgramNode': 'lightblue',
            'FunctionDeclNode': 'lightgreen',
            'StructDeclNode': 'lightyellow',
            'BlockStmtNode': 'lightgray',
            'VarDeclStmtNode': 'lightcyan',
            'IfStmtNode': 'lightpink',
            'WhileStmtNode': 'lightsalmon',
            'ForStmtNode': 'lightcoral',
            'ReturnStmtNode': 'lightseagreen',
            'ExprStmtNode': 'lightsteelblue',
            'EmptyStmtNode': 'lightgrey',
            'BinaryExprNode': 'lightskyblue',
            'UnaryExprNode': 'lightblue2',
            'LiteralExprNode': 'lightgoldenrod',
            'IdentifierExprNode': 'lightgoldenrodyellow',
            'CallExprNode': 'lightpink2',
            'AssignmentExprNode': 'lightcyan2',
            'ParamNode': 'lightgreen2',
        }

    def _new_node_id(self) -> int:
        self.counter += 1
        return self.counter

    def _add_node(self, node_id: int, label: str, node_type: str) -> None:
        color = self.node_colors.get(node_type, 'white')
        self.nodes.append(f'    n{node_id} [label="{label}", style="filled", fillcolor="{color}"];')

    def _add_edge(self, from_id: int, to_id: int) -> None:
        self.edges.append(f'    n{from_id} -> n{to_id};')

    def generate(self, node: ASTNode) -> str:
        """Генерирует DOT-представление AST."""
        self.nodes = []
        self.edges = []
        self.counter = 0
        self.node_stack = []
        node.accept(self)

        dot = ['digraph AST {',
               '    node [fontname="Courier", shape=box];',
               '    edge [fontname="Courier"];']
        dot.extend(self.nodes)
        dot.extend(self.edges)
        dot.append('}')
        return '\n'.join(dot)

    # ---- Visitor implementations ----

    def visit_program(self, node: ProgramNode) -> Any:
        node_id = self._new_node_id()
        self._add_node(node_id, f"Program\n[{node.line}]", 'ProgramNode')
        self.node_stack.append(node_id)

        for decl in node.declarations:
            child_id = decl.accept(self)
            self._add_edge(node_id, child_id)

        self.node_stack.pop()
        return node_id

    def visit_function_decl(self, node: FunctionDeclNode) -> int:
        node_id = self._new_node_id()
        label = f"Function\n{node.name} -> {node.return_type}\n[{node.line}]"
        self._add_node(node_id, label, 'FunctionDeclNode')

        # Параметры
        for param in node.parameters:
            param_id = param.accept(self)
            self._add_edge(node_id, param_id)

        # Тело функции
        body_id = node.body.accept(self)
        self._add_edge(node_id, body_id)

        return node_id

    def visit_param(self, node: ParamNode) -> int:
        node_id = self._new_node_id()
        label = f"Param\n{node.type_name} {node.name}\n[{node.line}]"
        self._add_node(node_id, label, 'ParamNode')
        return node_id

    def visit_block_stmt(self, node: BlockStmtNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"Block\n[{node.line}]", 'BlockStmtNode')

        for stmt in node.statements:
            child_id = stmt.accept(self)
            self._add_edge(node_id, child_id)

        return node_id

    def visit_var_decl_stmt(self, node: VarDeclStmtNode) -> int:
        node_id = self._new_node_id()
        label = f"VarDecl\n{node.type_name} {node.name}\n[{node.line}]"
        self._add_node(node_id, label, 'VarDeclStmtNode')

        if node.initializer:
            init_id = node.initializer.accept(self)
            self._add_edge(node_id, init_id)

        return node_id

    def visit_expr_stmt(self, node: ExprStmtNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"ExprStmt\n[{node.line}]", 'ExprStmtNode')

        expr_id = node.expression.accept(self)
        self._add_edge(node_id, expr_id)

        return node_id

    def visit_if_stmt(self, node: IfStmtNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"If\n[{node.line}]", 'IfStmtNode')

        cond_id = node.condition.accept(self)
        self._add_edge(node_id, cond_id)

        then_id = node.then_branch.accept(self)
        self._add_edge(node_id, then_id)

        if node.else_branch:
            else_id = node.else_branch.accept(self)
            self._add_edge(node_id, else_id)

        return node_id

    def visit_while_stmt(self, node: WhileStmtNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"While\n[{node.line}]", 'WhileStmtNode')

        cond_id = node.condition.accept(self)
        self._add_edge(node_id, cond_id)

        body_id = node.body.accept(self)
        self._add_edge(node_id, body_id)

        return node_id

    def visit_for_stmt(self, node: ForStmtNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"For\n[{node.line}]", 'ForStmtNode')

        if node.init:
            init_id = node.init.accept(self)
            self._add_edge(node_id, init_id)

        if node.condition:
            cond_id = node.condition.accept(self)
            self._add_edge(node_id, cond_id)

        if node.update:
            update_id = node.update.accept(self)
            self._add_edge(node_id, update_id)

        body_id = node.body.accept(self)
        self._add_edge(node_id, body_id)

        return node_id

    def visit_return_stmt(self, node: ReturnStmtNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"Return\n[{node.line}]", 'ReturnStmtNode')

        if node.value:
            val_id = node.value.accept(self)
            self._add_edge(node_id, val_id)

        return node_id

    def visit_empty_stmt(self, node: EmptyStmtNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"Empty\n[{node.line}]", 'EmptyStmtNode')
        return node_id

    def visit_literal_expr(self, node: LiteralExprNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"Literal\n{repr(node.value)}\n[{node.line}]", 'LiteralExprNode')
        return node_id

    def visit_identifier_expr(self, node: IdentifierExprNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"Identifier\n{node.name}\n[{node.line}]", 'IdentifierExprNode')
        return node_id

    def visit_binary_expr(self, node: BinaryExprNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"Binary\n{node.operator}\n[{node.line}]", 'BinaryExprNode')

        left_id = node.left.accept(self)
        self._add_edge(node_id, left_id)

        right_id = node.right.accept(self)
        self._add_edge(node_id, right_id)

        return node_id

    def visit_unary_expr(self, node: UnaryExprNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"Unary\n{node.operator}\n[{node.line}]", 'UnaryExprNode')

        operand_id = node.operand.accept(self)
        self._add_edge(node_id, operand_id)

        return node_id

    def visit_call_expr(self, node: CallExprNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"Call\n[{node.line}]", 'CallExprNode')

        callee_id = node.callee.accept(self)
        self._add_edge(node_id, callee_id)

        for arg in node.arguments:
            arg_id = arg.accept(self)
            self._add_edge(node_id, arg_id)

        return node_id

    def visit_assignment_expr(self, node: AssignmentExprNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"Assignment\n{node.operator}\n[{node.line}]", 'AssignmentExprNode')

        target_id = node.target.accept(self)
        self._add_edge(node_id, target_id)

        value_id = node.value.accept(self)
        self._add_edge(node_id, value_id)

        return node_id

    def visit_struct_decl(self, node: StructDeclNode) -> int:
        node_id = self._new_node_id()
        self._add_node(node_id, f"Struct\n{node.name}\n[{node.line}]", 'StructDeclNode')

        for field in node.fields:
            field_id = field.accept(self)
            self._add_edge(node_id, field_id)

        return node_id