import sys
from pathlib import Path

# Add project root to path before imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer

def analyze_source(source_code):
    scanner = Scanner(source_code)
    tokens = []
    while not scanner.is_at_end():
        tok = scanner.next_token()
        tokens.append(tok)
        if tok.type.name == "END_OF_FILE":
            break
    parser = Parser(tokens)
    ast = parser.parse()
    if parser.errors:
        # Return parse errors instead
        errors = parser.errors
        return [], [str(e) for e in errors]
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    return analyzer.errors, [str(e) for e in analyzer.errors]

class TestSemanticValid:
    def test_simple_function(self):
        code = """
        fn add(a: int, b: int) -> int {
            return a + b;
        }
        """
        errors, err_msgs = analyze_source(code)
        assert len(errors) == 0, f"Got errors: {err_msgs}"

    def test_variable_decl_and_use(self):
        code = """
        int x = 5;
        int y = x + 2;
        """
        errors, _ = analyze_source(code)
        assert len(errors) == 0

    def test_if_with_bool_condition(self):
        code = """
        fn main() -> int {
            bool flag = true;
            if (flag) {
                return 1;
            }
            return 0;
        }
        """
        errors, _ = analyze_source(code)
        assert len(errors) == 0, f"Got errors: {_}"

    def test_float_operations(self):
        code = """
        float f = 3.14;
        float g = f * 2.0;
        """
        errors, _ = analyze_source(code)
        assert len(errors) == 0

    def test_struct_usage(self):
        code = """
        struct Point { int x; int y; }
        fn dist(p: Point) -> int {
            return p.x + p.y;
        }
        """
        errors, _ = analyze_source(code)
        assert len(errors) == 0

class TestSemanticInvalid:
    def test_undeclared_variable(self):
        code = """
        fn main() {
            x = 5;
        }
        """
        errors, msgs = analyze_source(code)
        assert len(errors) > 0
        assert any("undeclared" in m.lower() or "unknown" in m.lower() for m in msgs)

    def test_type_mismatch_assignment(self):
        code = """
        int x = "hello";
        """
        errors, msgs = analyze_source(code)
        assert len(errors) > 0
        assert any("type mismatch" in m.lower() for m in msgs)

    def test_return_type_error(self):
        code = """
        fn foo() -> int {
            return 3.14;
        }
        """
        errors, msgs = analyze_source(code)
        assert len(errors) > 0
        assert any("return" in m.lower() and "type" in m.lower() for m in msgs)

    def test_function_arg_count(self):
        code = """
        fn bar(a: int) -> void {
            return;
        }
        fn baz() -> void {
            bar(1, 2);
        }
        """
        errors, msgs = analyze_source(code)
        assert len(errors) > 0, f"Got no errors, msgs: {msgs}"
        assert any("expects" in m.lower() or "argument" in m.lower() for m in msgs), f"Error messages: {msgs}"

    def test_duplicate_definition(self):
        code = """
        int x = 1;
        int x = 2;
        """
        errors, msgs = analyze_source(code)
        assert len(errors) > 0
        assert any("duplicate" in m.lower() for m in msgs)

    def test_condition_not_bool(self):
        code = """
        fn main() -> void {
            int a = 5;
            if (a) { }
        }
        """
        errors, msgs = analyze_source(code)
        assert len(errors) > 0
        assert any("condition" in m.lower() and "boolean" in m.lower() for m in msgs)

    def test_invalid_operator(self):
        code = """
        bool b = true;
        int c = -b;
        """
        errors, msgs = analyze_source(code)
        assert len(errors) > 0
        assert any("unary '-'" in m.lower() for m in msgs)