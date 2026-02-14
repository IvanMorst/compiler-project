import os
import sys
import difflib
from pathlib import Path

# Add project root to path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.lexer.scanner import Scanner

TEST_DIR = Path(__file__).parent / "lexer"
VALID_DIR = TEST_DIR / "valid"
INVALID_DIR = TEST_DIR / "invalid"

def run_test(src_file, expected_file):
    """Run lexer on src_file and compare output to expected_file."""
    with open(src_file, "r", encoding="utf-8") as f:
        source = f.read()
    scanner = Scanner(source)
    tokens = []
    while not scanner.is_at_end():
        tok = scanner.next_token()
        tokens.append(tok)
        if tok.type.name == "END_OF_FILE":
            break
    # Format tokens
    output_lines = [tok.format() for tok in tokens]
    # Read expected lines
    with open(expected_file, "r", encoding="utf-8") as f:
        expected_lines = [line.rstrip("\n") for line in f]

    if output_lines == expected_lines:
        return True, None
    else:
        diff = difflib.unified_diff(expected_lines, output_lines,
                                    fromfile=str(expected_file),
                                    tofile="<actual>", lineterm="")
        return False, "\n".join(diff)

def main():
    passed = 0
    failed = 0

    # Valid tests
    for src_file in VALID_DIR.glob("*.src"):
        expected_file = src_file.with_suffix(".expected")
        if not expected_file.exists():
            print(f"Missing expected file for {src_file}")
            failed += 1
            continue
        ok, diff = run_test(src_file, expected_file)
        if ok:
            print(f"PASS: {src_file.name}")
            passed += 1
        else:
            print(f"FAIL: {src_file.name}")
            print(diff)
            failed += 1

    # Invalid tests (still produce tokens but may include error tokens; we still compare)
    for src_file in INVALID_DIR.glob("*.src"):
        expected_file = src_file.with_suffix(".expected")
        if not expected_file.exists():
            print(f"Missing expected file for {src_file}")
            failed += 1
            continue
        ok, diff = run_test(src_file, expected_file)
        if ok:
            print(f"PASS: {src_file.name}")
            passed += 1
        else:
            print(f"FAIL: {src_file.name}")
            print(diff)
            failed += 1

    print(f"\nTests: {passed} passed, {failed} failed")
    sys.exit(1 if failed > 0 else 0)

if __name__ == "__main__":
    main()