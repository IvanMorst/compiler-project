import argparse
import sys
from pathlib import Path
from src.lexer.scanner import Scanner
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.semantic.symbol_table import SymbolTable
from src.ir.ir_generator import IRGenerator


def run_ir_generation(input_file: str, output_file: str = None,
                      format: str = "text", optimize: bool = False,
                      stats: bool = False, verbose: bool = False):
    """Generate IR from source file."""

    # Read source
    with open(input_file, "r", encoding="utf-8") as f:
        source = f.read()

    # Lexical analysis
    scanner = Scanner(source)
    tokens = []
    while not scanner.is_at_end():
        tok = scanner.next_token()
        tokens.append(tok)
        if tok.type.name == "END_OF_FILE":
            break

    if scanner.errors and verbose:
        print("Lexical errors:", file=sys.stderr)
        for err in scanner.errors:
            print(f"  {err}", file=sys.stderr)

    # Syntax analysis
    parser = Parser(tokens)
    ast = parser.parse()

    if parser.errors and verbose:
        print("Syntax errors:", file=sys.stderr)
        for err in parser.errors:
            print(f"  {err}", file=sys.stderr)

    # Semantic analysis
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    if analyzer.errors:
        print("Semantic errors:", file=sys.stderr)
        for err in analyzer.errors:
            print(f"  {err}", file=sys.stderr)
        if not verbose:
            return 1

    # IR Generation
    ir_gen = IRGenerator(analyzer.symbol_table)
    ir_program = ir_gen.generate(ast)

    # Generate output
    if format == "text":
        output = str(ir_program)

        # Add statistics if requested
        if stats:
            ir_stats = ir_program.get_statistics()
            output += "\n\n# IR Statistics:\n"
            output += f"#   Functions: {ir_stats['total_functions']}\n"
            output += f"#   Basic Blocks: {ir_stats['total_blocks']}\n"
            output += f"#   Instructions: {ir_stats['total_instructions']}\n"
            output += f"#   Instruction Types:\n"
            for op_name, count in sorted(ir_stats['instruction_types'].items()):
                output += f"#     {op_name}: {count}\n"

    elif format == "json":
        import json
        output = json.dumps(_ir_to_dict(ir_program), indent=2)

    elif format == "dot":
        output = _generate_cfg_dot(ir_program)

    else:
        print(f"Unknown format: {format}", file=sys.stderr)
        return 1

    # Output
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        if verbose:
            print(f"IR written to {output_file}", file=sys.stderr)
    else:
        print(output)

    return 0


def _ir_to_dict(ir_program) -> dict:
    """Convert IR program to dictionary for JSON output."""
    functions = []
    for func in ir_program.functions:
        blocks = []
        for block in func.cfg.blocks:
            instructions = []
            for instr in block.instructions:
                instructions.append({
                    'opcode': instr.opcode.name,
                    'dest': str(instr.dest) if instr.dest else None,
                    'operands': [str(op) for op in instr.operands],
                    'comment': instr.comment
                })
            blocks.append({
                'label': str(block.label),
                'instructions': instructions
            })
        functions.append({
            'name': func.name,
            'return_type': func.return_type,
            'parameters': func.parameters,
            'blocks': blocks
        })
    return {'functions': functions}


def _generate_cfg_dot(ir_program) -> str:
    """Generate Graphviz DOT for CFG visualization."""
    dot_lines = ['digraph CFG {', '    node [shape=box, fontname="Courier"];']

    for func in ir_program.functions:
        dot_lines.append(f'    subgraph cluster_{func.name} {{')
        dot_lines.append(f'        label = "{func.name}";')

        for block in func.cfg.blocks:
            # Create node with instructions
            label_parts = [f"{block.label}:\\l"]
            for instr in block.instructions:
                label_parts.append(f"  {str(instr).strip()}\\l")
            label = "".join(label_parts)

            color = "white"
            if block.is_entry:
                color = "lightgreen"
            elif block.is_exit:
                color = "lightcoral"

            dot_lines.append(f'        {block.name} [label="{label}", style=filled, fillcolor={color}];')

        # Add edges
        for block in func.cfg.blocks:
            for succ in block.successors:
                dot_lines.append(f'        {block.name} -> {succ.name};')

        dot_lines.append('    }')

    dot_lines.append('}')
    return '\n'.join(dot_lines)


def main():
    parser = argparse.ArgumentParser(description="MiniCompiler IR Generator (Sprint 4)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ir_parser = subparsers.add_parser("ir", help="Generate IR from source")
    ir_parser.add_argument("--input", "-i", required=True, help="Input source file")
    ir_parser.add_argument("--output", "-o", help="Output file for IR")
    ir_parser.add_argument("--format", "-f", choices=["text", "dot", "json"],
                           default="text", help="Output format")
    ir_parser.add_argument("--optimize", action="store_true", help="Run peephole optimizer")
    ir_parser.add_argument("--stats", action="store_true", help="Show IR statistics")
    ir_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.command == "ir":
        sys.exit(run_ir_generation(
            args.input, args.output, args.format,
            args.optimize, args.stats, args.verbose
        ))