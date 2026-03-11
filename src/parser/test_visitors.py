import pytest
from src.parser.pretty_printer import PrettyPrinter
from src.parser.dot_generator import DOTGenerator
from src.parser.json_generator import JSONGenerator
import json


class TestVisitors:
    """Тесты для классов-посетителей AST."""

    def test_pretty_printer_basic(self, sample_program_node, pretty_printer):
        """Тест pretty printer для базовой программы."""
        output = pretty_printer.visit_program(sample_program_node)

        # Проверяем наличие ключевых элементов
        assert "Program" in output
        assert "FunctionDecl: main -> int" in output
        assert "Parameters: []" in output
        assert "VarDecl: int x = 42" in output
        assert "Return: x" in output

        # Проверяем отступы
        lines = output.split('\n')
        assert lines[0] == "Program [line 1]:"
        assert lines[1].startswith("  FunctionDecl:")
        assert lines[2].startswith("    Parameters:")

    def test_pretty_printer_complex(self, parse_source, pretty_printer):
        """Тест pretty printer для сложной программы."""
        source = """
        fn factorial(n: int) -> int {
            if (n <= 1) {
                return 1;
            } else {
                return n * factorial(n - 1);
            }
        }
        """
        program = parse_source(source)
        output = pretty_printer.visit_program(program)

        # Проверяем структуру if-else
        assert "IfStmt" in output
        assert "Condition: (n <= 1)" in output or "Condition: n <= 1" in output
        assert "Then:" in output
        assert "Else:" in output
        assert "Return: (n * factorial((n - 1)))" in output or "Return: n * factorial(n - 1)" in output

    def test_dot_generator_basic(self, sample_program_node, dot_generator):
        """Тест генерации DOT для базовой программы."""
        dot = dot_generator.generate(sample_program_node)

        # Проверяем структуру DOT
        assert dot.startswith("digraph AST {")
        assert "node [fontname=\"Courier\", shape=box];" in dot
        assert "edge [fontname=\"Courier\"];" in dot

        # Проверяем наличие узлов
        assert "label=\"Program" in dot
        assert "label=\"Function" in dot
        assert "label=\"VarDecl" in dot

        # Проверяем наличие рёбер
        assert "->" in dot

    def test_dot_generator_colors(self, sample_program_node, dot_generator):
        """Тест цветовой кодировки в DOT."""
        dot = dot_generator.generate(sample_program_node)

        # Проверяем наличие атрибутов цвета
        assert "fillcolor=" in dot
        assert "style=\"filled\"" in dot

    def test_json_generator_basic(self, sample_program_node, json_generator):
        """Тест генерации JSON для базовой программы."""
        json_str = json_generator.generate(sample_program_node)
        data = json.loads(json_str)

        # Проверяем структуру JSON
        assert data["node_type"] == "Program"
        assert len(data["declarations"]) == 1

        func = data["declarations"][0]
        assert func["node_type"] == "FunctionDecl"
        assert func["name"] == "main"
        assert func["return_type"] == "int"
        assert len(func["parameters"]) == 0

        body = func["body"]
        assert body["node_type"] == "Block"
        assert len(body["statements"]) == 2

        # Проверяем объявление переменной
        var_decl = body["statements"][0]
        assert var_decl["node_type"] == "VarDecl"
        assert var_decl["type_name"] == "int"
        assert var_decl["name"] == "x"
        assert var_decl["initializer"]["value"] == 42

    def test_json_generator_complex(self, parse_source, json_generator):
        """Тест генерации JSON для сложной программы."""
        source = """
        fn add(a: int, b: int) -> int {
            return a + b;
        }
        """
        program = parse_source(source)
        json_str = json_generator.generate(program)
        data = json.loads(json_str)

        # Проверяем параметры функции
        func = data["declarations"][0]
        assert len(func["parameters"]) == 2
        assert func["parameters"][0]["type_name"] == "int"
        assert func["parameters"][0]["name"] == "a"

        # Проверяем return с бинарной операцией
        return_stmt = func["body"]["statements"][0]
        assert return_stmt["node_type"] == "ReturnStmt"
        bin_expr = return_stmt["value"]
        assert bin_expr["node_type"] == "BinaryExpr"
        assert bin_expr["operator"] == "+"

    def test_visitor_pattern_extensibility(self, sample_program_node):
        """Тест расширяемости паттерна Visitor."""

        # Создаём кастомный visitor
        class NodeCounter(PrettyPrinter):
            def __init__(self):
                super().__init__()
                self.count = 0

            def visit_program(self, node):
                self.count += 1
                return super().visit_program(node)

            def visit_function_decl(self, node):
                self.count += 1
                return super().visit_function_decl(node)

            def visit_block_stmt(self, node):
                self.count += 1
                return super().visit_block_stmt(node)

        counter = NodeCounter()
        counter.visit_program(sample_program_node)

        # Должно быть 3 узла: Program, FunctionDecl, Block
        assert counter.count == 3