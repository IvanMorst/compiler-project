from typing import List, Optional, Set, Dict
from dataclasses import dataclass, field
from .ir_instructions import IRInstruction, IROpcode, Label


@dataclass
class BasicBlock:
    """A basic block of IR instructions with single entry/exit."""
    label: Label
    instructions: List[IRInstruction] = field(default_factory=list)
    predecessors: List['BasicBlock'] = field(default_factory=list)
    successors: List['BasicBlock'] = field(default_factory=list)
    is_entry: bool = False
    is_exit: bool = False

    @property
    def name(self) -> str:
        return str(self.label)

    def add_instruction(self, instr: IRInstruction):
        """Add instruction to block."""
        self.instructions.append(instr)

    def add_predecessor(self, block: 'BasicBlock'):
        """Add predecessor block."""
        if block not in self.predecessors:
            self.predecessors.append(block)

    def add_successor(self, block: 'BasicBlock'):
        """Add successor block."""
        if block not in self.successors:
            self.successors.append(block)

    def get_last_instruction(self) -> Optional[IRInstruction]:
        """Get the last instruction in block."""
        if self.instructions:
            return self.instructions[-1]
        return None

    def is_terminated(self) -> bool:
        """Check if block ends with control flow instruction."""
        if not self.instructions:
            return False
        last = self.get_last_instruction()
        return last and last.opcode in {
            IROpcode.JUMP, IROpcode.JUMP_IF, IROpcode.JUMP_IF_NOT,
            IROpcode.RETURN
        }

    def __str__(self) -> str:
        lines = [f"{self.label}:"]
        for instr in self.instructions:
            lines.append(str(instr))
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"BasicBlock({self.name}, {len(self.instructions)} insns)"


class ControlFlowGraph:
    """Control flow graph for a function."""

    def __init__(self, name: str):
        self.name = name
        self.blocks: List[BasicBlock] = []
        self.entry_block: Optional[BasicBlock] = None
        self.exit_block: Optional[BasicBlock] = None

    def add_block(self, block: BasicBlock):
        """Add a basic block to the CFG."""
        self.blocks.append(block)

    def set_entry(self, block: BasicBlock):
        """Set entry block."""
        block.is_entry = True
        self.entry_block = block

    def set_exit(self, block: BasicBlock):
        """Set exit block."""
        block.is_exit = True
        self.exit_block = block

    def connect_blocks(self, from_block: BasicBlock, to_block: BasicBlock):
        """Add control flow edge between blocks."""
        from_block.add_successor(to_block)
        to_block.add_predecessor(from_block)

    def get_block_by_label(self, label: Label) -> Optional[BasicBlock]:
        """Find block by label."""
        for block in self.blocks:
            if block.label.name == label.name:
                return block
        return None

    def __str__(self) -> str:
        lines = [f"CFG for '{self.name}':"]
        for block in self.blocks:
            lines.append(f"  {block.name}: {len(block.instructions)} instructions")
            lines.append(f"    Predecessors: {[b.name for b in block.predecessors]}")
            lines.append(f"    Successors: {[b.name for b in block.successors]}")
        return "\n".join(lines)


class FunctionIR:
    """Complete IR for a single function."""

    def __init__(self, name: str, return_type: str = "void",
                 parameters: Optional[List[Dict]] = None):
        self.name = name
        self.return_type = return_type
        self.parameters = parameters or []
        self.cfg = ControlFlowGraph(name)
        self.symbol_table: Dict[str, str] = {}  # source var -> IR temp mapping
        self.local_vars: List[Dict] = []

    def allocate_variable(self, source_name: str) -> str:
        """Map source variable to IR temporary."""
        temp_name = f"{source_name}_{len(self.symbol_table)}"
        self.symbol_table[source_name] = temp_name
        return temp_name

    def get_variable_temp(self, source_name: str) -> Optional[str]:
        """Get IR temporary for source variable."""
        return self.symbol_table.get(source_name)

    def __str__(self) -> str:
        lines = [f"function {self.name}: {self.return_type} "
                 f"({', '.join(p['type'] for p in self.parameters)})"]
        lines.append(f"  # Entry: {self.cfg.entry_block.name if self.cfg.entry_block else 'none'}")
        for block in self.cfg.blocks:
            lines.append(str(block))
        return "\n".join(lines)


class IRProgram:
    """Complete IR program with functions and global data."""

    def __init__(self, source_name: str = ""):
        self.source_name = source_name
        self.functions: List[FunctionIR] = []
        self.global_vars: List[Dict] = []

    def add_function(self, func: FunctionIR):
        """Add function to program."""
        self.functions.append(func)

    def get_function(self, name: str) -> Optional[FunctionIR]:
        """Get function by name."""
        for func in self.functions:
            if func.name == name:
                return func
        return None

    def get_statistics(self) -> Dict:
        """Get IR program statistics."""
        stats = {
            'total_functions': len(self.functions),
            'total_blocks': sum(len(f.cfg.blocks) for f in self.functions),
            'total_instructions': 0,
            'instruction_types': {},
            'total_temporaries': 0
        }

        for func in self.functions:
            for block in func.cfg.blocks:
                for instr in block.instructions:
                    stats['total_instructions'] += 1
                    op_name = instr.opcode.name
                    stats['instruction_types'][op_name] = \
                        stats['instruction_types'].get(op_name, 0) + 1

        return stats

    def __str__(self) -> str:
        lines = [f"# Program: {self.source_name}"]
        lines.append("")
        for func in self.functions:
            lines.append(str(func))
            lines.append("")
        return "\n".join(lines)