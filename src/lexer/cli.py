import argparse
import sys
from .scanner import Scanner

def main():
    parser = argparse.ArgumentParser(description="MiniCompiler Lexical Analyzer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lex_parser = subparsers.add_parser("lex", help="Run lexer on input file")
    lex_parser.add_argument("--input", "-i", required=True, help="Input source file")
    lex_parser.add_argument("--output", "-o", required=True, help="Output token file")

    args = parser.parse_args()

    if args.command == "lex":
        with open(args.input, "r", encoding="utf-8") as f:
            source = f.read()
        scanner = Scanner(source)
        tokens = []
        while not scanner.is_at_end():
            tok = scanner.next_token()
            tokens.append(tok)
            if tok.type.name == "END_OF_FILE":
                break
        with open(args.output, "w", encoding="utf-8") as f:
            for tok in tokens:
                f.write(tok.format() + "\n")
        for err in scanner.errors:
            print(err, file=sys.stderr)
        if scanner.errors:
            sys.exit(1)

if __name__ == "__main__":
    main()