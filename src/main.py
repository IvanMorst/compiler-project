#!/usr/bin/env python3
"""
MiniCompiler - Главный интерфейс командной строки
Объединяет функциональность всех спринтов.
"""

import argparse
import sys
from pathlib import Path

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer import cli as lexer_cli
from src.parser import cli as parser_cli


def main():
    parser = argparse.ArgumentParser(description="MiniCompiler - Компилятор C-подобного языка")
    subparsers = parser.add_subparsers(dest="command", required=True,
                                       help="Available commands")

    # Команда lex (из Sprint 1)
    lex_parser = subparsers.add_parser("lex", help="Run lexical analysis (tokenization)")
    lex_parser.add_argument("--input", "-i", required=True, help="Input source file")
    lex_parser.add_argument("--output", "-o", required=True, help="Output token file")

    # Команда parse (из Sprint 2)
    parse_parser = subparsers.add_parser("parse", help="Run syntactic analysis (build AST)")
    parse_parser.add_argument("--input", "-i", required=True, help="Input source file")
    parse_parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parse_parser.add_argument("--format", "-f", choices=["text", "dot", "json"],
                              default="text", help="Output format (default: text)")
    parse_parser.add_argument("--verbose", "-v", action="store_true",
                              help="Print verbose error information")

    # Команда test
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--lexer", action="store_true", help="Run lexer tests")
    test_parser.add_argument("--parser", action="store_true", help="Run parser tests")

    args = parser.parse_args()

    if args.command == "lex":
        # Перенаправляем в lexer CLI
        sys.argv = [sys.argv[0], "lex", "--input", args.input, "--output", args.output]
        lexer_cli.main()
    elif args.command == "parse":
        # Перенаправляем в parser CLI
        cmd = ["parse", "--input", args.input]
        if args.output:
            cmd.extend(["--output", args.output])
        cmd.extend(["--format", args.format])
        if args.verbose:
            cmd.append("--verbose")
        sys.argv = [sys.argv[0]] + cmd
        parser_cli.main()
    elif args.command == "test":
        # Запуск тестов
        test_runner = Path(__file__).parent.parent / "tests" / "test_runner.py"
        if args.lexer:
            os.system(f"python {test_runner} --lexer")
        elif args.parser:
            os.system(f"python {test_runner} --parser")
        else:
            # Запускаем все тесты
            os.system(f"python {test_runner}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()