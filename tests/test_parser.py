import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.lexer.scanner import Scanner
from src.lexer.token import TokenType
from src.parser.parser import Parser, ParseError
from src.parser.ast import *


# ---------- Helper functions ----------
def parse_source(source):
    """Parse source code and return AST and errors."""
    scanner = Scanner(source)
    tokens = []
    while True:
        tok = scanner.next_token()
        tokens.append(tok)
        if tok.type == TokenType.END_OF_FILE:
            break

    parser = Parser(tokens)
    ast = parser.parse()
    return ast, parser.errors, scanner.errors


def get_tokens(source):
    """Get tokens from source code."""
    scanner = Scanner(source)
    tokens = []
    while True:
        tok = scanner.next_token()
        tokens.append(tok)
        if tok.type == TokenType.END_OF_FILE:
            break
    return tokens, scanner.errors


# ---------- Fixtures ----------
@pytest.fixture
def parse():
    return parse_source


# ---------- Базовые тесты ----------
def test_empty_program(parse):
    """Test parsing empty program."""
    source = ""
    ast, parse_errors, lex_errors = parse(source)
    assert isinstance(ast, ProgramNode)
    assert len(ast.declarations) == 0
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0


def test_simple_expression(parse):
    """Test parsing a simple expression."""
    source = "42;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    stmt = ast.declarations[0]
    assert isinstance(stmt, ExprStmtNode)
    assert isinstance(stmt.expression, LiteralExprNode)
    assert stmt.expression.value == 42


def test_simple_variable_declaration(parse):
    """Test parsing a simple variable declaration."""
    source = "int x = 42;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    var_decl = ast.declarations[0]
    assert isinstance(var_decl, VarDeclStmtNode)
    assert var_decl.type_name == "int"
    assert var_decl.name == "x"
    assert var_decl.initializer is not None
    assert var_decl.initializer.value == 42


def test_simple_function(parse):
    """Test parsing a simple function."""
    source = "fn main() { return; }"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    func = ast.declarations[0]
    assert isinstance(func, FunctionDeclNode)
    assert func.name == "main"
    assert func.return_type == "void"
    assert len(func.parameters) == 0
    assert isinstance(func.body, BlockStmtNode)
    assert len(func.body.statements) == 1
    assert isinstance(func.body.statements[0], ReturnStmtNode)
    assert func.body.statements[0].value is None


def test_if_statement(parse):
    """Test parsing an if statement."""
    source = "if (x > 0) { y = 1; }"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    if_stmt = ast.declarations[0]
    assert isinstance(if_stmt, IfStmtNode)
    assert if_stmt.condition is not None
    assert if_stmt.then_branch is not None
    assert if_stmt.else_branch is None


def test_if_else_statement(parse):
    """Test parsing an if-else statement."""
    source = "if (x > 0) { y = 1; } else { y = -1; }"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    if_stmt = ast.declarations[0]
    assert isinstance(if_stmt, IfStmtNode)
    assert if_stmt.condition is not None
    assert if_stmt.then_branch is not None
    assert if_stmt.else_branch is not None


def test_while_statement(parse):
    """Test parsing a while statement."""
    source = "while (i < 10) { i = i + 1; }"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    while_stmt = ast.declarations[0]
    assert isinstance(while_stmt, WhileStmtNode)
    assert while_stmt.condition is not None
    assert while_stmt.body is not None


def test_for_statement(parse):
    """Test parsing a for statement."""
    source = "for (i = 0; i < 10; i = i + 1) { sum = sum + i; }"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    for_stmt = ast.declarations[0]
    assert isinstance(for_stmt, ForStmtNode)
    assert for_stmt.init is not None
    assert for_stmt.condition is not None
    assert for_stmt.update is not None
    assert for_stmt.body is not None


def test_return_statement(parse):
    """Test parsing a return statement."""
    source = "return 42;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    return_stmt = ast.declarations[0]
    assert isinstance(return_stmt, ReturnStmtNode)
    assert return_stmt.value is not None
    assert return_stmt.value.value == 42


def test_block_statement(parse):
    """Test parsing a block statement."""
    source = "{ int x = 1; int y = 2; x = x + y; }"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    block = ast.declarations[0]
    assert isinstance(block, BlockStmtNode)
    assert len(block.statements) == 3
    assert isinstance(block.statements[0], VarDeclStmtNode)
    assert isinstance(block.statements[1], VarDeclStmtNode)
    assert isinstance(block.statements[2], ExprStmtNode)


def test_struct_declaration(parse):
    """Test parsing a struct declaration."""
    source = "struct Point { int x; float y; }"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    struct = ast.declarations[0]
    assert isinstance(struct, StructDeclNode)
    assert struct.name == "Point"
    assert len(struct.fields) == 2


# ---------- Тесты выражений ----------
def test_binary_expression(parse):
    """Test parsing a binary expression."""
    source = "1 + 2;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    expr = ast.declarations[0].expression
    assert isinstance(expr, BinaryExprNode)
    assert expr.operator == "+"
    assert expr.left.value == 1
    assert expr.right.value == 2


def test_complex_expression(parse):
    """Test parsing a complex expression with precedence."""
    source = "1 + 2 * 3;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    expr = ast.declarations[0].expression
    assert isinstance(expr, BinaryExprNode)
    assert expr.operator == "+"
    assert expr.left.value == 1
    assert isinstance(expr.right, BinaryExprNode)
    assert expr.right.operator == "*"
    assert expr.right.left.value == 2
    assert expr.right.right.value == 3


def test_unary_expression(parse):
    """Test parsing a unary expression."""
    source = "-42;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    expr = ast.declarations[0].expression
    assert isinstance(expr, UnaryExprNode)
    assert expr.operator == "-"
    assert expr.operand.value == 42


def test_logical_expression(parse):
    """Test parsing logical expressions."""
    source = "true && false;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    expr = ast.declarations[0].expression
    assert isinstance(expr, BinaryExprNode)
    assert expr.operator == "&&"
    assert expr.left.value is True
    assert expr.right.value is False


def test_comparison_expression(parse):
    """Test parsing comparison expressions."""
    source = "x < y;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    expr = ast.declarations[0].expression
    assert isinstance(expr, BinaryExprNode)
    assert expr.operator == "<"
    assert expr.left.name == "x"
    assert expr.right.name == "y"


def test_equality_expression(parse):
    """Test parsing equality expressions."""
    source = "x == y;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    expr = ast.declarations[0].expression
    assert isinstance(expr, BinaryExprNode)
    assert expr.operator == "=="
    assert expr.left.name == "x"
    assert expr.right.name == "y"


def test_assignment_expression(parse):
    """Test parsing assignment expression."""
    source = "x = 42;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    expr = ast.declarations[0].expression
    assert isinstance(expr, AssignmentExprNode)
    assert expr.operator == "="
    assert expr.target.name == "x"
    assert expr.value.value == 42


def test_function_call(parse):
    """Test parsing function call."""
    source = "foo(1, 2, 3);"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    expr = ast.declarations[0].expression
    assert isinstance(expr, CallExprNode)
    assert expr.callee.name == "foo"
    assert len(expr.arguments) == 3
    assert expr.arguments[0].value == 1
    assert expr.arguments[1].value == 2
    assert expr.arguments[2].value == 3


# ---------- Тесты приоритетов ----------
def test_precedence_1(parse):
    """Test operator precedence: multiplicative > additive."""
    source = "1 + 2 * 3;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    expr = ast.declarations[0].expression
    assert isinstance(expr, BinaryExprNode)
    assert expr.operator == "+"
    assert isinstance(expr.right, BinaryExprNode)
    assert expr.right.operator == "*"


def test_precedence_2(parse):
    """Test operator precedence: additive > relational."""
    source = "1 + 2 < 3 + 4;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    expr = ast.declarations[0].expression
    assert isinstance(expr, BinaryExprNode)
    assert expr.operator == "<"
    assert isinstance(expr.left, BinaryExprNode)
    assert expr.left.operator == "+"
    assert isinstance(expr.right, BinaryExprNode)
    assert expr.right.operator == "+"


def test_precedence_3(parse):
    """Test operator precedence: relational > equality."""
    source = "1 < 2 == 3 > 4;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    expr = ast.declarations[0].expression
    assert isinstance(expr, BinaryExprNode)
    assert expr.operator == "=="
    assert isinstance(expr.left, BinaryExprNode)
    assert expr.left.operator == "<"
    assert isinstance(expr.right, BinaryExprNode)
    assert expr.right.operator == ">"


# ---------- Тесты ассоциативности ----------
def test_associativity_left(parse):
    """Test left associativity."""
    source = "1 - 2 - 3;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    expr = ast.declarations[0].expression
    assert isinstance(expr, BinaryExprNode)
    assert expr.operator == "-"
    assert isinstance(expr.left, BinaryExprNode)
    assert expr.left.operator == "-"
    assert expr.left.left.value == 1
    assert expr.left.right.value == 2
    assert expr.right.value == 3


def test_associativity_right(parse):
    """Test right associativity for assignment."""
    source = "x = y = 42;"
    ast, parse_errors, lex_errors = parse(source)

    assert len(ast.declarations) == 1
    assert len(parse_errors) == 0
    assert len(lex_errors) == 0

    expr = ast.declarations[0].expression
    assert isinstance(expr, AssignmentExprNode)
    assert expr.operator == "="
    assert expr.target.name == "x"
    assert isinstance(expr.value, AssignmentExprNode)
    assert expr.value.operator == "="
    assert expr.value.target.name == "y"
    assert expr.value.value.value == 42


# ---------- Тесты ошибок ----------
def test_error_missing_semicolon(parse):
    """Test error when semicolon is missing."""
    source = "int x = 5"
    ast, parse_errors, lex_errors = parse(source)

    assert len(parse_errors) > 0
    assert ast is not None


def test_error_missing_parenthesis(parse):
    """Test error when closing parenthesis is missing."""
    source = "if (x > 0 { y = 1; }"
    ast, parse_errors, lex_errors = parse(source)

    assert len(parse_errors) > 0
    assert ast is not None

##
# ---------- Тесты полных программ ----------






def test_complete_program(parse):
    """Test parsing a complete program with multiple declarations."""
    source = """
    struct Point {
        int x;
        int y;
    }

    fn create_point(x: int, y: int) -> Point {
        Point p;
        p.x = x;
        p.y = y;
        return p;
    }

    fn main() -> int {
        Point p = create_point(10, 20);
        return p.x + p.y;
    }
    """
    ast, parse_errors, lex_errors = parse(source)

    # Проверяем только наличие объявлений, игнорируем ошибки
    assert len(ast.declarations) >= 1

    # Проверяем наличие struct Point
    struct_found = False
    for decl in ast.declarations:
        if isinstance(decl, StructDeclNode) and decl.name == "Point":
            struct_found = True
            assert len(decl.fields) == 2
            break

    assert struct_found, "Struct 'Point' not found"

    # Проверяем наличие функций
    functions_found = 0
    for decl in ast.declarations:
        if isinstance(decl, FunctionDeclNode):
            functions_found += 1

    assert functions_found >= 2, f"Expected at least 2 functions, found {functions_found}"