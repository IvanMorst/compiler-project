import argparse
import sys
import os

# Добавляем путь к корневой директории в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.lexer.scanner import Scanner


def main():
    parser = argparse.ArgumentParser(description="MiniCompiler Lexical Analyzer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lex_parser = subparsers.add_parser("lex", help="Run lexer on input file")
    lex_parser.add_argument("--input", "-i", required=True, help="Input source file")
    lex_parser.add_argument("--output", "-o", required=True, help="Output token file")

    args = parser.parse_args()

    if args.command == "lex":
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                source = f.read()
        except FileNotFoundError:
            print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading input file: {e}", file=sys.stderr)
            sys.exit(1)

        scanner = Scanner(source)
        tokens = []
        while not scanner.is_at_end():
            tok = scanner.next_token()
            tokens.append(tok)
            if tok.type.name == "END_OF_FILE":
                break

        # Write tokens to output
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                for tok in tokens:
                    f.write(tok.format() + "\n")
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)

        # Report errors to stderr
        for err in scanner.errors:
            print(err, file=sys.stderr)

        if scanner.errors:
            sys.exit(1)


if __name__ == "__main__":
    main()