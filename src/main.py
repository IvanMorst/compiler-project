#!/usr/bin/env python3
"""
MiniCompiler - Главный интерфейс командной строки
Объединяет функциональность всех спринтов.
"""

import argparse
import sys
from pathlib import Path
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer import cli as lexer_cli
from src.parser import cli as parser_cli
from src.semantic import cli as semantic_cli
from src.ir import cli as ir_cli


def main():
    parser = argparse.ArgumentParser(description="MiniCompiler - Компилятор C-подобного языка")
    subparsers = parser.add_subparsers(dest="command", required=True,
                                       help="Available commands")

    # Команда lex (Sprint 1)
    lex_parser = subparsers.add_parser("lex", help="Run lexical analysis (tokenization)")
    lex_parser.add_argument("--input", "-i", required=True, help="Input source file")
    lex_parser.add_argument("--output", "-o", required=True, help="Output token file")

    # Команда parse (Sprint 2)
    parse_parser = subparsers.add_parser("parse", help="Run syntactic analysis (build AST)")
    parse_parser.add_argument("--input", "-i", required=True, help="Input source file")
    parse_parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parse_parser.add_argument("--format", "-f", choices=["text", "dot", "json"],
                              default="text", help="Output format (default: text)")
    parse_parser.add_argument("--verbose", "-v", action="store_true",
                              help="Print verbose error information")

    # Команда check (Sprint 3)
    check_parser = subparsers.add_parser("check", help="Run semantic analysis")
    check_parser.add_argument("--input", "-i", required=True, help="Input source file")
    check_parser.add_argument("--output", "-o", help="Output file for report")
    check_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    check_parser.add_argument("--show-types", action="store_true", help="Show type annotations")
    check_parser.add_argument("--dump-symbols", action="store_true", help="Dump symbol table")

    # Команда ir (Sprint 4)
    ir_parser = subparsers.add_parser("ir", help="Generate Intermediate Representation")
    ir_parser.add_argument("--input", "-i", required=True, help="Input source file")
    ir_parser.add_argument("--output", "-o", help="Output file for IR")
    ir_parser.add_argument("--format", "-f", choices=["text", "dot", "json"],
                           default="text", help="Output format")
    ir_parser.add_argument("--optimize", action="store_true", help="Run optimizer")
    ir_parser.add_argument("--stats", action="store_true", help="Show statistics")
    ir_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # Команда test
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--lexer", action="store_true", help="Run lexer tests")
    test_parser.add_argument("--parser", action="store_true", help="Run parser tests")
    test_parser.add_argument("--semantic", action="store_true", help="Run semantic tests")
    test_parser.add_argument("--ir", action="store_true", help="Run IR tests")

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
    elif args.command == "check":
        sys.exit(semantic_cli.run_semantic(
            args.input, args.output, args.verbose,
            args.show_types, args.dump_symbols
        ))
    elif args.command == "ir":
        sys.exit(ir_cli.run_ir_generation(
            args.input, args.output, args.format,
            args.optimize, args.stats, args.verbose
        ))
    elif args.command == "test":
        test_runner = Path(__file__).parent.parent / "tests" / "test_runner.py"
        if args.lexer:
            os.system(f"python {test_runner} --lexer")
        elif args.parser:
            os.system(f"python {test_runner} --parser")
        elif args.semantic:
            os.system(f"pytest tests/semantic/test_semantic.py -v")
        elif args.ir:
            os.system(f"pytest tests/ir/test_ir_generator.py -v")
        else:
            os.system(f"python {test_runner}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()