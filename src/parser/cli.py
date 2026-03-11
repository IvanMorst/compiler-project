import argparse
import sys
import os
from pathlib import Path
from typing import Optional

from src.lexer.scanner import Scanner
from src.lexer.token import Token
from src.parser.parser import Parser
from src.parser.pretty_printer import PrettyPrinter
from src.parser.dot_generator import DOTGenerator
from src.parser.json_generator import JSONGenerator


def run_parser(input_file: str, output_file: Optional[str], format: str = "text", verbose: bool = False):
    """
    Запускает парсер на входном файле и выводит AST в указанном формате.
    """
    # Чтение исходного файла
    with open(input_file, "r", encoding="utf-8") as f:
        source = f.read()

    # Лексический анализ
    scanner = Scanner(source)
    tokens = []
    while not scanner.is_at_end():
        token = scanner.next_token()
        tokens.append(token)
        if token.type.name == "END_OF_FILE":
            break

    if scanner.errors and verbose:
        print("Lexical errors:", file=sys.stderr)
        for err in scanner.errors:
            print(f"  {err}", file=sys.stderr)

    # Синтаксический анализ
    parser = Parser(tokens)
    ast = parser.parse()

    if parser.errors and verbose:
        print("Syntax errors:", file=sys.stderr)
        for err in parser.errors:
            print(f"  {err}", file=sys.stderr)

    # Генерация вывода
    if format == "text":
        printer = PrettyPrinter()
        output = printer.visit_program(ast)
    elif format == "dot":
        generator = DOTGenerator()
        output = generator.generate(ast)
    elif format == "json":
        generator = JSONGenerator()
        output = generator.generate(ast)
    else:
        raise ValueError(f"Unknown format: {format}")

    # Вывод результата
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        if verbose:
            print(f"AST written to {output_file}", file=sys.stderr)
    else:
        print(output)

    # Возвращаем код ошибки
    if scanner.errors or parser.errors:
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description="MiniCompiler Parser (Sprint 2)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Команда parse
    parse_parser = subparsers.add_parser("parse", help="Parse source file and output AST")
    parse_parser.add_argument("--input", "-i", required=True, help="Input source file")
    parse_parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parse_parser.add_argument("--format", "-f", choices=["text", "dot", "json"],
                              default="text", help="Output format (default: text)")
    parse_parser.add_argument("--verbose", "-v", action="store_true",
                              help="Print verbose error information")

    # Команда test (для запуска тестов парсера)
    test_parser = subparsers.add_parser("test", help="Run parser tests")
    test_parser.add_argument("--parser", action="store_true", help="Run parser tests")

    args = parser.parse_args()

    if args.command == "parse":
        sys.exit(run_parser(args.input, args.output, args.format, args.verbose))
    elif args.command == "test" and args.parser:
        # Запуск тестов парсера через test_runner
        test_runner_path = Path(__file__).parent.parent.parent / "tests" / "test_runner.py"
        os.system(f"python {test_runner_path} --parser")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()