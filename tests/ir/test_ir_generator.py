import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.ir.ir_generator import IRGenerator
from src.ir.ir_instructions import IROpcode


def generate_ir(source_code):
    """Helper to generate IR from source."""
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
        return None  # Return None if parsing fails

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    ir_gen = IRGenerator(analyzer.symbol_table)
    return ir_gen.generate(ast)


class TestIRExpression:
    def test_integer_literal(self):
        code = "int x = 42;"
        ir = generate_ir(code)
        assert ir is not None
        # Global variable, no functions
        # This is fine for now

    def test_simple_arithmetic(self):
        code = """
        fn test() -> int {
            int x = 2 + 3;
            return x;
        }
        """
        ir = generate_ir(code)
        assert ir is not None
        func = ir.get_function("test")
        assert func is not None
        assert any(
            instr.opcode == IROpcode.ADD
            for block in func.cfg.blocks
            for instr in block.instructions
        )

    def test_comparison(self):
        code = """
        fn test() -> int {
            if (5 > 3) {
                return 1;
            }
            return 0;
        }
        """
        ir = generate_ir(code)
        assert ir is not None
        func = ir.get_function("test")
        assert any(
            instr.opcode == IROpcode.CMP_GT
            for block in func.cfg.blocks
            for instr in block.instructions
        )


class TestIRControlFlow:
    def test_if_statement_with_else(self):
        code = """
        fn test(int x) -> int {
            if (x > 0) {
                return 1;
            } else {
                return 0;
            }
        }
        """
        ir = generate_ir(code)
        assert ir is not None
        func = ir.get_function("test")
        assert func is not None
        # Should have at least 3 blocks: entry, then, else, (exit)
        assert len(func.cfg.blocks) >= 3, f"Found {len(func.cfg.blocks)} blocks"

    def test_while_loop(self):
        code = """
        fn test() -> int {
            int i = 0;
            while (i < 10) {
                i = i + 1;
            }
            return i;
        }
        """
        ir = generate_ir(code)
        assert ir is not None
        func = ir.get_function("test")
        # Should have header, body, exit blocks
        assert len(func.cfg.blocks) >= 3, f"Found {len(func.cfg.blocks)} blocks"


class TestIRFunctions:
    def test_function_call(self):
        code = """
        fn add(int a, int b) -> int {
            return a + b;
        }

        fn main() -> int {
            return add(1, 2);
        }
        """
        ir = generate_ir(code)
        assert ir is not None
        func = ir.get_function("main")
        assert func is not None
        assert any(
            instr.opcode == IROpcode.CALL
            for block in func.cfg.blocks
            for instr in block.instructions
        )


class TestIRStructure:
    def test_all_blocks_terminated(self):
        code = """
        fn test(int x) -> int {
            if (x > 0) {
                return 1;
            }
            return 0;
        }
        """
        ir = generate_ir(code)
        assert ir is not None
        func = ir.get_function("test")
        assert func is not None

        # Check that all blocks end with a terminator instruction
        for block in func.cfg.blocks:
            assert block.is_terminated(), \
                f"Block {block.name} not terminated. Last instruction: {block.get_last_instruction()}"

    def test_cfg_entry_block_exists(self):
        code = """
        fn test(int x) -> int {
            return x;
        }
        """
        ir = generate_ir(code)
        assert ir is not None
        func = ir.get_function("test")
        assert func is not None
        assert func.cfg.entry_block is not None, "No entry block"

    def test_multiple_functions(self):
        code = """
        fn foo() -> int { return 1; }
        fn bar() -> int { return 2; }
        """
        ir = generate_ir(code)
        assert ir is not None
        assert len(ir.functions) == 2, f"Expected 2 functions, got {len(ir.functions)}"
        assert ir.get_function("foo") is not None
        assert ir.get_function("bar") is not None


class TestIRStatistics:
    def test_statistics_generation(self):
        code = """
        fn add(int a, int b) -> int {
            return a + b;
        }

        fn main() -> int {
            int x = 5;
            int y = 10;
            return add(x, y);
        }
        """
        ir = generate_ir(code)
        assert ir is not None

        stats = ir.get_statistics()
        assert stats['total_functions'] == 2
        assert stats['total_blocks'] > 0
        assert stats['total_instructions'] > 0
        assert 'ADD' in stats['instruction_types'] or len(stats['instruction_types']) > 0