#!/usr/bin/env python3
"""
Универсальный тестовый раннер для MiniCompiler.
Поддерживает тесты лексера и парсера.
"""

import os
import sys
import difflib
import argparse
from pathlib import Path

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.parser.pretty_printer import PrettyPrinter

TEST_DIR = Path(__file__).parent
LEXER_DIR = TEST_DIR / "lexer"
PARSER_DIR = TEST_DIR / "parser"


def run_lexer_test(src_file, expected_file):
    """Запускает тест лексера."""
    with open(src_file, "r", encoding="utf-8") as f:
        source = f.read()

    scanner = Scanner(source)
    tokens = []
    while not scanner.is_at_end():
        tok = scanner.next_token()
        tokens.append(tok)
        if tok.type.name == "END_OF_FILE":
            break

    # Форматируем токены
    output_lines = [tok.format() for tok in tokens]

    # Читаем ожидаемый вывод
    with open(expected_file, "r", encoding="utf-8") as f:
        expected_lines = [line.rstrip("\n") for line in f]

    if output_lines == expected_lines:
        return True, None
    else:
        diff = difflib.unified_diff(expected_lines, output_lines,
                                    fromfile=str(expected_file),
                                    tofile="<actual>", lineterm="")
        return False, "\n".join(diff)


def run_parser_test(src_file, expected_file):
    """Запускает тест парсера (сравнение pretty-printed AST)."""
    with open(src_file, "r", encoding="utf-8") as f:
        source = f.read()

    # Лексический анализ
    scanner = Scanner(source)
    tokens = []
    while not scanner.is_at_end():
        tok = scanner.next_token()
        tokens.append(tok)
        if tok.type.name == "END_OF_FILE":
            break

    if scanner.errors:
        # Если есть лексические ошибки, тест должен их обрабатывать
        # Для простоты считаем, что в валидных тестах их нет
        pass

    # Синтаксический анализ
    parser = Parser(tokens)
    ast = parser.parse()

    # Pretty print AST
    printer = PrettyPrinter()
    output = printer.visit_program(ast)
    output_lines = output.split("\n")

    # Читаем ожидаемый вывод
    with open(expected_file, "r", encoding="utf-8") as f:
        expected_lines = [line.rstrip("\n") for line in f]

    if output_lines == expected_lines:
        return True, None
    else:
        diff = difflib.unified_diff(expected_lines, output_lines,
                                    fromfile=str(expected_file),
                                    tofile="<actual>", lineterm="")
        return False, "\n".join(diff)


def run_tests_in_dir(test_dir, test_func, recursive=True):
    """Запускает все тесты в директории."""
    passed = 0
    failed = 0

    if recursive:
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                if file.endswith(".src"):
                    src_file = Path(root) / file
                    expected_file = src_file.with_suffix(".expected")
                    if not expected_file.exists():
                        print(f"Missing expected file for {src_file}")
                        failed += 1
                        continue

                    ok, diff = test_func(src_file, expected_file)
                    rel_path = src_file.relative_to(TEST_DIR)
                    if ok:
                        print(f"  PASS: {rel_path}")
                        passed += 1
                    else:
                        print(f"  FAIL: {rel_path}")
                        if diff:
                            print(diff)
                        failed += 1
    else:
        for src_file in test_dir.glob("*.src"):
            expected_file = src_file.with_suffix(".expected")
            if not expected_file.exists():
                print(f"Missing expected file for {src_file}")
                failed += 1
                continue

            ok, diff = test_func(src_file, expected_file)
            rel_path = src_file.relative_to(TEST_DIR)
            if ok:
                print(f"  PASS: {rel_path}")
                passed += 1
            else:
                print(f"  FAIL: {rel_path}")
                if diff:
                    print(diff)
                failed += 1

    return passed, failed


def main():
    parser = argparse.ArgumentParser(description="MiniCompiler Test Runner")
    parser.add_argument("--lexer", action="store_true", help="Run lexer tests only")
    parser.add_argument("--parser", action="store_true", help="Run parser tests only")
    args = parser.parse_args()

    total_passed = 0
    total_failed = 0

    # Запуск тестов лексера
    if args.lexer or (not args.lexer and not args.parser):
        print("\n=== Lexer Tests ===")

        # Валидные тесты
        print("\nValid tests:")
        p, f = run_tests_in_dir(LEXER_DIR / "valid", run_lexer_test, recursive=False)
        total_passed += p
        total_failed += f

        # Невалидные тесты
        print("\nInvalid tests:")
        p, f = run_tests_in_dir(LEXER_DIR / "invalid", run_lexer_test, recursive=False)
        total_passed += p
        total_failed += f

    # Запуск тестов парсера
    if args.parser or (not args.lexer and not args.parser):
        print("\n=== Parser Tests ===")

        for category in ["expressions", "statements", "declarations", "full_programs"]:
            category_dir = PARSER_DIR / "valid" / category
            if category_dir.exists():
                print(f"\nValid/{category}:")
                p, f = run_tests_in_dir(category_dir, run_parser_test, recursive=False)
                total_passed += p
                total_failed += f

        # Тесты на синтаксические ошибки
        invalid_dir = PARSER_DIR / "invalid" / "syntax_errors"
        if invalid_dir.exists():
            print("\nInvalid/syntax_errors:")
            p, f = run_tests_in_dir(invalid_dir, run_parser_test, recursive=False)
            total_passed += p
            total_failed += f

    print(f"\n=== Summary: {total_passed} passed, {total_failed} failed ===")
    sys.exit(1 if total_failed > 0 else 0)


if __name__ == "__main__":
    main()