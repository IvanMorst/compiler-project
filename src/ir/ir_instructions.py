from enum import Enum, auto
from typing import List, Optional, Union, Any
from dataclasses import dataclass


class IROpcode(Enum):
    """IR instruction opcodes for three-address code."""
    # Arithmetic
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    NEG = auto()

    # Logical
    AND = auto()
    OR = auto()
    NOT = auto()
    XOR = auto()

    # Comparisons
    CMP_EQ = auto()
    CMP_NE = auto()
    CMP_LT = auto()
    CMP_LE = auto()
    CMP_GT = auto()
    CMP_GE = auto()

    # Memory
    LOAD = auto()
    STORE = auto()
    ALLOCA = auto()
    GEP = auto()  # Get Element Pointer

    # Control Flow
    JUMP = auto()
    JUMP_IF = auto()
    JUMP_IF_NOT = auto()
    LABEL = auto()
    PHI = auto()

    # Functions
    CALL = auto()
    RETURN = auto()
    PARAM = auto()

    # Data Movement
    MOVE = auto()


class IROperand:
    """Base class for IR operands."""

    def __str__(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return str(self)


@dataclass
class Temporary(IROperand):
    """Virtual register / temporary variable."""
    name: str
    ir_type: Optional[Any] = None  # Type annotation

    def __str__(self) -> str:
        return f"%{self.name}"


@dataclass
class Variable(IROperand):
    """Named variable (source-level)."""
    name: str
    ir_type: Optional[Any] = None

    def __str__(self) -> str:
        return f"@{self.name}"


@dataclass
class Literal(IROperand):
    """Constant literal value."""
    value: Union[int, float, str, bool]
    ir_type: Optional[Any] = None

    def __str__(self) -> str:
        if isinstance(self.value, str):
            return f'"{self.value}"'
        elif isinstance(self.value, bool):
            return str(self.value).lower()
        return str(self.value)


@dataclass
class Label(IROperand):
    """Basic block label."""
    name: str

    def __str__(self) -> str:
        return f"L_{self.name}"


@dataclass
class MemoryLocation(IROperand):
    """Memory address operand."""
    base: IROperand
    offset: Optional[int] = None

    def __str__(self) -> str:
        if self.offset:
            return f"[{self.base}+{self.offset}]"
        return f"[{self.base}]"


class IRInstruction:
    """Single IR instruction in three-address code format."""

    def __init__(self, opcode: IROpcode, dest: Optional[IROperand] = None,
                 operands: Optional[List[IROperand]] = None,
                 comment: str = ""):
        self.opcode = opcode
        self.dest = dest
        self.operands = operands or []
        self.comment = comment
        self.line_number: Optional[int] = None  # Source line reference

    def __str__(self) -> str:
        parts = []

        # Label instruction
        if self.opcode == IROpcode.LABEL:
            return f"{self.dest}:{self._format_comment()}"

        # PHI instruction
        if self.opcode == IROpcode.PHI:
            phi_pairs = ", ".join(f"({op}, {str(op).split('_')[1] if hasattr(op, 'name') else op})"
                                  for op in self.operands)
            return f"    {self.dest} = PHI {phi_pairs}{self._format_comment()}"

        # Destination
        if self.dest:
            parts.append(f"    {self.dest} = {self.opcode.name}")
        else:
            parts.append(f"    {self.opcode.name}")

        # Operands
        if self.operands:
            parts.append(", ".join(str(op) for op in self.operands))

        result = " ".join(parts)

        # Comment
        result += self._format_comment()

        return result

    def _format_comment(self) -> str:
        """Format comment for output."""
        if self.comment:
            return f"  # {self.comment}"
        return ""

    def __repr__(self) -> str:
        return str(self)


class IRBuilder:
    """Builder for constructing IR instructions easily."""

    def __init__(self):
        self.temp_counter = 0
        self.label_counter = 0

    def new_temp(self, prefix: str = "t") -> Temporary:
        """Create a new temporary variable."""
        self.temp_counter += 1
        return Temporary(f"{prefix}{self.temp_counter}")

    def new_label(self, prefix: str = "L") -> Label:
        """Create a new label."""
        self.label_counter += 1
        return Label(f"{prefix}{self.label_counter}")

    def emit(self, opcode: IROpcode, dest: Optional[IROperand] = None,
             operands: Optional[List[IROperand]] = None,
             comment: str = "") -> IRInstruction:
        """Create a new IR instruction."""
        return IRInstruction(opcode, dest, operands, comment)

    # Arithmetic
    def emit_add(self, left: IROperand, right: IROperand, comment: str = "") -> IRInstruction:
        dest = self.new_temp()
        return self.emit(IROpcode.ADD, dest, [left, right], comment)

    def emit_sub(self, left: IROperand, right: IROperand, comment: str = "") -> IRInstruction:
        dest = self.new_temp()
        return self.emit(IROpcode.SUB, dest, [left, right], comment)

    def emit_mul(self, left: IROperand, right: IROperand, comment: str = "") -> IRInstruction:
        dest = self.new_temp()
        return self.emit(IROpcode.MUL, dest, [left, right], comment)

    def emit_div(self, left: IROperand, right: IROperand, comment: str = "") -> IRInstruction:
        dest = self.new_temp()
        return self.emit(IROpcode.DIV, dest, [left, right], comment)

    def emit_mod(self, left: IROperand, right: IROperand, comment: str = "") -> IRInstruction:
        dest = self.new_temp()
        return self.emit(IROpcode.MOD, dest, [left, right], comment)

    def emit_neg(self, operand: IROperand, comment: str = "") -> IRInstruction:
        dest = self.new_temp()
        return self.emit(IROpcode.NEG, dest, [operand], comment)

    # Comparison
    def emit_cmp(self, cmp_type: IROpcode, left: IROperand, right: IROperand,
                 comment: str = "") -> IRInstruction:
        dest = self.new_temp()
        return self.emit(cmp_type, dest, [left, right], comment)

    # Control flow
    def emit_jump(self, label: Label, comment: str = "") -> IRInstruction:
        return self.emit(IROpcode.JUMP, None, [label], comment)

    def emit_jump_if(self, cond: IROperand, label: Label, comment: str = "") -> IRInstruction:
        return self.emit(IROpcode.JUMP_IF, None, [cond, label], comment)

    def emit_jump_if_not(self, cond: IROperand, label: Label, comment: str = "") -> IRInstruction:
        return self.emit(IROpcode.JUMP_IF_NOT, None, [cond, label], comment)

    def emit_label(self, label: Label, comment: str = "") -> IRInstruction:
        return self.emit(IROpcode.LABEL, label, [], comment)

    # Memory
    def emit_load(self, addr: IROperand, comment: str = "") -> IRInstruction:
        dest = self.new_temp()
        return self.emit(IROpcode.LOAD, dest, [MemoryLocation(addr)], comment)

    def emit_store(self, addr: IROperand, value: IROperand, comment: str = "") -> IRInstruction:
        return self.emit(IROpcode.STORE, None, [MemoryLocation(addr), value], comment)

    # Functions
    def emit_call(self, func_name: str, args: List[IROperand], comment: str = "") -> IRInstruction:
        dest = self.new_temp()
        operands = [Variable(func_name)] + args
        return self.emit(IROpcode.CALL, dest, operands, comment)

    def emit_return(self, value: Optional[IROperand] = None, comment: str = "") -> IRInstruction:
        operands = [value] if value else []
        return self.emit(IROpcode.RETURN, None, operands, comment)

    def emit_param(self, index: int, value: IROperand, comment: str = "") -> IRInstruction:
        return self.emit(IROpcode.PARAM, None, [Literal(index), value], comment)

    def emit_move(self, dest: IROperand, src: IROperand, comment: str = "") -> IRInstruction:
        return self.emit(IROpcode.MOVE, dest, [src], comment)