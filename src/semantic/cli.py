import argparse
import sys
import os
from pathlib import Path
from src.lexer.scanner import Scanner
from src.parser.ast import CallExprNode, BlockStmtNode, ExpressionNode
from src.parser.parser import Parser
from src.parser.pretty_printer import PrettyPrinter
from src.semantic.analyzer import SemanticAnalyzer
from src.semantic.symbol_table import SymbolTable

def run_semantic(input_file: str, output_file: str = None, verbose: bool = False, show_types: bool = False, dump_symbols: bool = False):
    with open(input_file, "r", encoding="utf-8") as f:
        source = f.read()

    # Lex
    scanner = Scanner(source)
    tokens = []
    while not scanner.is_at_end():
        tok = scanner.next_token()
        tokens.append(tok)
        if tok.type.name == "END_OF_FILE":
            break
    if scanner.errors:
        for err in scanner.errors:
            print(f"lexical error: {err}", file=sys.stderr)
        return 1

    # Parse
    parser = Parser(tokens)
    ast = parser.parse()
    if parser.errors:
        for err in parser.errors:
            print(f"syntax error: {err}", file=sys.stderr)
        return 1

    # Semantic analysis
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)  # accepted errors are stored
    if analyzer.errors:
        for err in analyzer.errors:
            print(f"semantic error: {err}", file=sys.stderr)
        if not verbose:
            return 1
    else:
        if verbose:
            print("Semantic analysis passed.", file=sys.stderr)

    if dump_symbols:
        all_syms = analyzer.symbol_table.get_all_symbols()
        print("Symbol Table:")
        for scope, syms in all_syms.items():
            print(f"  {scope}:")
            for s in syms:
                print(f"    {s}")

    if show_types:
        # Print type-annotated AST (text format with types)
        # We can reuse PrettyPrinter but it doesn't show types.
        # We'll just print a simple representation.
        def print_typed(node, indent=0):
            if isinstance(node, ExpressionNode) and node.semantic_type:
                type_str = f" : {node.semantic_type}"
            else:
                type_str = ""
            print(" " * indent + f"{node.__class__.__name__}{type_str}")
            if hasattr(node, 'left'):
                print_typed(node.left, indent+2)
            if hasattr(node, 'right'):
                print_typed(node.right, indent+2)
            if hasattr(node, 'operand'):
                print_typed(node.operand, indent+2)
            if isinstance(node, CallExprNode):
                for arg in node.arguments:
                    print_typed(arg, indent+2)
            if isinstance(node, BlockStmtNode):
                for stmt in node.statements:
                    print_typed(stmt, indent+2)
            # etc. (simplified)
        print_typed(ast)

    if output_file:
        # For now we output a summary to file: symbol table dump
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("Semantic analysis complete.\n")
            if analyzer.errors:
                f.write(f"{len(analyzer.errors)} error(s) found.\n")
            if dump_symbols:
                f.write("Symbol Table:\n")
                all_syms = analyzer.symbol_table.get_all_symbols()
                for scope, syms in all_syms.items():
                    f.write(f"  {scope}:\n")
                    for s in syms:
                        f.write(f"    {s}\n")

    return 0

def main():
    parser = argparse.ArgumentParser(description="MiniCompiler Semantic Analyzer (Sprint 3)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Run semantic analysis on a source file")
    check_parser.add_argument("--input", "-i", required=True, help="Input source file")
    check_parser.add_argument("--output", "-o", help="Output file for report")
    check_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    check_parser.add_argument("--show-types", action="store_true", help="Show type annotations in AST")
    check_parser.add_argument("--dump-symbols", action="store_true", help="Dump symbol table")

    args = parser.parse_args()
    if args.command == "check":
        sys.exit(run_semantic(args.input, args.output, args.verbose, args.show_types, args.dump_symbols))