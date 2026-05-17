from typing import Dict, Optional, Any, List
from src.parser.ast import *
from src.parser.visitor import ASTVisitor
from src.semantic.symbol_table import SymbolTable, SymbolKind
from src.semantic.type_system import Type, TypeKind, INT, FLOAT, BOOL, VOID, STRING
from .ir_instructions import (
    IROpcode, IROperand, Temporary, Variable, Literal, Label,
    MemoryLocation, IRInstruction, IRBuilder
)
from .basic_block import BasicBlock, FunctionIR, IRProgram


class IRGenerator(ASTVisitor):
    """Generates IR from decorated AST using visitor pattern."""

    def __init__(self, symbol_table: SymbolTable):
        self.symbol_table = symbol_table
        self.builder = IRBuilder()
        self.program: Optional[IRProgram] = None
        self.current_function: Optional[FunctionIR] = None
        self.current_block: Optional[BasicBlock] = None
        self.current_loop_continue: Optional[Label] = None
        self.current_loop_break: Optional[Label] = None

        # Track variable to temporary mapping
        self.var_temp_map: Dict[str, Temporary] = {}

        # Track expression results
        self.last_result: Optional[IROperand] = None

        # Expression string cache for comments
        self.expr_str_cache: Dict[int, str] = {}

    def generate(self, ast: ProgramNode) -> IRProgram:
        """Generate IR for entire program."""
        self.program = IRProgram()
        ast.accept(self)
        return self.program

    def get_function_ir(self, name: str) -> Optional[FunctionIR]:
        """Get IR for specific function."""
        if self.program:
            return self.program.get_function(name)
        return None

    def get_all_ir(self) -> Optional[IRProgram]:
        """Get complete IR program."""
        return self.program

    def _new_block(self, label: Label, comment: str = "") -> BasicBlock:
        """Create a new basic block."""
        block = BasicBlock(label)
        # Don't add label instruction here - will be added when we start emitting to it
        return block

    def _start_block(self, block: BasicBlock):
        """Start emitting to a block and add its label."""
        self.current_block = block
        # Add label instruction only once
        if not any(instr.opcode == IROpcode.LABEL and str(instr.dest) == str(block.label)
                   for instr in block.instructions):
            block.add_instruction(self.builder.emit_label(block.label))

    def _to_operand(self, value: Any) -> IROperand:
        """Convert Python value to IR operand."""
        if isinstance(value, int):
            return Literal(value)
        elif isinstance(value, float):
            return Literal(value)
        elif isinstance(value, bool):
            return Literal(value)
        elif isinstance(value, str):
            return Literal(value)
        elif isinstance(value, IROperand):
            return value
        return Literal(value)

    def _get_expression_string(self, node) -> str:
        """Get a string representation of an expression for comments."""
        if isinstance(node, LiteralExprNode):
            return str(node.value)
        elif isinstance(node, IdentifierExprNode):
            return node.name
        elif isinstance(node, BinaryExprNode):
            left_str = self._get_expression_string(node.left)
            right_str = self._get_expression_string(node.right)
            return f"({left_str} {node.operator} {right_str})"
        elif isinstance(node, UnaryExprNode):
            operand_str = self._get_expression_string(node.operand)
            return f"({node.operator}{operand_str})"
        elif isinstance(node, CallExprNode):
            callee_str = self._get_expression_string(node.callee)
            args_str = ", ".join(self._get_expression_string(a) for a in node.arguments)
            return f"{callee_str}({args_str})"
        elif isinstance(node, AssignmentExprNode):
            target_str = self._get_expression_string(node.target)
            value_str = self._get_expression_string(node.value)
            return f"({target_str} {node.operator} {value_str})"
        return "?"

    # ============ PROGRAM ============
    def visit_program(self, node: ProgramNode):
        """Process program declarations."""
        for decl in node.declarations:
            if isinstance(decl, FunctionDeclNode):
                decl.accept(self)

    # ============ FUNCTION DECLARATION ============
    def visit_function_decl(self, node: FunctionDeclNode):
        """Generate IR for function declaration."""
        func = FunctionIR(node.name, node.return_type,
                          [{'name': p.name, 'type': p.type_name} for p in node.parameters])
        self.program.add_function(func)
        self.current_function = func
        self.var_temp_map = {}

        # Create entry block
        entry_label = self.builder.new_label(f"{node.name}_entry")
        entry_block = self._new_block(entry_label)
        func.cfg.add_block(entry_block)
        func.cfg.set_entry(entry_block)
        self._start_block(entry_block)

        # Map parameters to temporaries
        for param in node.parameters:
            temp = Temporary(param.name)
            self.var_temp_map[param.name] = temp
            func.local_vars.append({
                'name': param.name,
                'type': param.type_name,
                'temp': temp.name
            })

        # Process function body
        if node.body:
            node.body.accept(self)

        # Ensure function ends with return if needed
        if not self.current_block.is_terminated():
            if func.return_type == "void":
                self.current_block.add_instruction(
                    self.builder.emit_return(comment="return void")
                )
            else:
                self.current_block.add_instruction(
                    self.builder.emit_return(Literal(0), "default return")
                )

    # ============ BLOCK STATEMENT ============
    def visit_block_stmt(self, node: BlockStmtNode):
        """Process block of statements."""
        for stmt in node.statements:
            stmt.accept(self)

    # ============ VARIABLE DECLARATION ============
    def visit_var_decl_stmt(self, node: VarDeclStmtNode):
        """Generate IR for variable declaration."""
        var_temp = self.builder.new_temp(node.name)
        self.var_temp_map[node.name] = var_temp

        if self.current_function:
            self.current_function.local_vars.append({
                'name': node.name,
                'type': node.type_name,
                'temp': var_temp.name
            })

        if node.initializer:
            node.initializer.accept(self)
            if self.last_result:
                expr_str = self._get_expression_string(node.initializer)
                self.current_block.add_instruction(
                    self.builder.emit_move(var_temp, self.last_result,
                                           f"{node.name} = {expr_str}")
                )
                self.last_result = var_temp

    # ============ EXPRESSION STATEMENT ============
    def visit_expr_stmt(self, node: ExprStmtNode):
        """Process expression statement."""
        if node.expression:
            node.expression.accept(self)

    # ============ IF STATEMENT ============
    def visit_if_stmt(self, node: IfStmtNode):
        """Generate IR for if statement."""
        then_label = self.builder.new_label("then")
        else_label = self.builder.new_label("else") if node.else_branch else None
        endif_label = self.builder.new_label("endif")

        # Evaluate condition
        node.condition.accept(self)
        cond_result = self.last_result

        # Create blocks
        then_block = self._new_block(then_label)
        self.current_function.cfg.add_block(then_block)

        else_block = None
        if node.else_branch:
            else_block = self._new_block(else_label)
            self.current_function.cfg.add_block(else_block)

        endif_block = self._new_block(endif_label)
        self.current_function.cfg.add_block(endif_block)

        # Add conditional jump from current block
        cond_str = self._get_expression_string(node.condition)
        if else_block:
            self.current_block.add_instruction(
                self.builder.emit_jump_if(cond_result, then_label, f"if ({cond_str})")
            )
            self.current_block.add_instruction(
                self.builder.emit_jump(else_label, "else")
            )
        else:
            self.current_block.add_instruction(
                self.builder.emit_jump_if(cond_result, then_label, f"if ({cond_str})")
            )
            self.current_block.add_instruction(
                self.builder.emit_jump(endif_label)
            )

        # Connect blocks
        self.current_function.cfg.connect_blocks(self.current_block, then_block)
        if else_block:
            self.current_function.cfg.connect_blocks(self.current_block, else_block)
        else:
            self.current_function.cfg.connect_blocks(self.current_block, endif_block)

        # Generate then branch
        self._start_block(then_block)
        node.then_branch.accept(self)
        if not self.current_block.is_terminated():
            self.current_block.add_instruction(self.builder.emit_jump(endif_label))
        self.current_function.cfg.connect_blocks(self.current_block, endif_block)

        # Generate else branch if present
        if node.else_branch:
            self._start_block(else_block)
            node.else_branch.accept(self)
            if not self.current_block.is_terminated():
                self.current_block.add_instruction(self.builder.emit_jump(endif_label))
            self.current_function.cfg.connect_blocks(self.current_block, endif_block)

        # Continue at endif
        self._start_block(endif_block)

    # ============ WHILE STATEMENT ============
    def visit_while_stmt(self, node: WhileStmtNode):
        """Generate IR for while loop."""
        loop_header = self.builder.new_label("while_header")
        loop_body = self.builder.new_label("while_body")
        loop_exit = self.builder.new_label("while_exit")

        old_continue = self.current_loop_continue
        old_break = self.current_loop_break
        self.current_loop_continue = loop_header
        self.current_loop_break = loop_exit

        # Jump to loop header
        self.current_block.add_instruction(
            self.builder.emit_jump(loop_header, "while loop")
        )

        # Create header block
        header_block = self._new_block(loop_header)
        self.current_function.cfg.add_block(header_block)
        self.current_function.cfg.connect_blocks(self.current_block, header_block)

        self._start_block(header_block)
        node.condition.accept(self)
        cond_result = self.last_result

        # Create body and exit blocks
        body_block = self._new_block(loop_body)
        self.current_function.cfg.add_block(body_block)

        exit_block = self._new_block(loop_exit)
        self.current_function.cfg.add_block(exit_block)

        # Add conditional jump
        cond_str = self._get_expression_string(node.condition)
        self.current_block.add_instruction(
            self.builder.emit_jump_if(cond_result, loop_body, f"while ({cond_str})")
        )
        self.current_block.add_instruction(
            self.builder.emit_jump(loop_exit)
        )
        self.current_function.cfg.connect_blocks(self.current_block, body_block)
        self.current_function.cfg.connect_blocks(self.current_block, exit_block)

        # Generate body
        self._start_block(body_block)
        node.body.accept(self)
        if not self.current_block.is_terminated():
            self.current_block.add_instruction(
                self.builder.emit_jump(loop_header, "loop back")
            )
        self.current_function.cfg.connect_blocks(self.current_block, header_block)

        # Continue after loop
        self._start_block(exit_block)

        self.current_loop_continue = old_continue
        self.current_loop_break = old_break

    # ============ RETURN STATEMENT ============
    def visit_return_stmt(self, node: ReturnStmtNode):
        """Generate IR for return statement."""
        if node.value:
            node.value.accept(self)
            expr_str = self._get_expression_string(node.value)
            self.current_block.add_instruction(
                self.builder.emit_return(self.last_result, f"return {expr_str}")
            )
        else:
            self.current_block.add_instruction(
                self.builder.emit_return(comment="return")
            )

    # ============ LITERAL EXPRESSION ============
    def visit_literal_expr(self, node: LiteralExprNode) -> Any:
        """Process literal value."""
        self.last_result = Literal(node.value)
        return self.last_result

    # ============ IDENTIFIER EXPRESSION ============
    def visit_identifier_expr(self, node: IdentifierExprNode) -> Any:
        """Process identifier (variable reference)."""
        if node.name in self.var_temp_map:
            self.last_result = self.var_temp_map[node.name]
        else:
            # Look up in function parameters
            if self.current_function:
                for param in self.current_function.parameters:
                    if param['name'] == node.name:
                        self.last_result = Temporary(node.name)
                        self.var_temp_map[node.name] = self.last_result
                        return self.last_result
            # If not found, create a temporary (should not happen after semantic analysis)
            temp = Temporary(node.name)
            self.var_temp_map[node.name] = temp
            self.last_result = temp
        return self.last_result

    # ============ BINARY EXPRESSION ============
    def visit_binary_expr(self, node: BinaryExprNode) -> Any:
        """Generate IR for binary expressions."""
        node.left.accept(self)
        left_result = self.last_result

        node.right.accept(self)
        right_result = self.last_result

        opcode_map = {
            '+': IROpcode.ADD,
            '-': IROpcode.SUB,
            '*': IROpcode.MUL,
            '/': IROpcode.DIV,
            '%': IROpcode.MOD,
            '==': IROpcode.CMP_EQ,
            '!=': IROpcode.CMP_NE,
            '<': IROpcode.CMP_LT,
            '<=': IROpcode.CMP_LE,
            '>': IROpcode.CMP_GT,
            '>=': IROpcode.CMP_GE,
            '&&': IROpcode.AND,
            '||': IROpcode.OR,
        }

        opcode = opcode_map.get(node.operator)
        if opcode:
            result_temp = self.builder.new_temp()
            expr_str = self._get_expression_string(node)
            instr = self.builder.emit(
                opcode, result_temp, [left_result, right_result],
                expr_str
            )
            self.current_block.add_instruction(instr)
            self.last_result = result_temp

        return self.last_result

    # ============ UNARY EXPRESSION ============
    def visit_unary_expr(self, node: UnaryExprNode) -> Any:
        """Generate IR for unary expressions."""
        node.operand.accept(self)
        operand_result = self.last_result

        expr_str = self._get_expression_string(node)

        if node.operator == '-':
            result_temp = self.builder.new_temp()
            instr = self.builder.emit(
                IROpcode.NEG, result_temp, [operand_result], expr_str
            )
            self.current_block.add_instruction(instr)
            self.last_result = result_temp
        elif node.operator == '!':
            result_temp = self.builder.new_temp()
            instr = self.builder.emit(
                IROpcode.NOT, result_temp, [operand_result], expr_str
            )
            self.current_block.add_instruction(instr)
            self.last_result = result_temp

        return self.last_result

    # ============ CALL EXPRESSION ============
    def visit_call_expr(self, node: CallExprNode) -> Any:
        """Generate IR for function calls."""
        # Generate arguments
        arg_temps = []
        for i, arg in enumerate(node.arguments):
            arg.accept(self)
            arg_temps.append(self.last_result)
            self.current_block.add_instruction(
                self.builder.emit_param(i, self.last_result, f"param {i}")
            )

        # Get function name
        func_name = ""
        if isinstance(node.callee, IdentifierExprNode):
            func_name = node.callee.name

        # Emit CALL instruction
        expr_str = self._get_expression_string(node)
        call_instr = self.builder.emit_call(
            func_name, arg_temps, expr_str
        )
        self.current_block.add_instruction(call_instr)
        self.last_result = call_instr.dest

        return self.last_result

    # ============ ASSIGNMENT EXPRESSION ============
    def visit_assignment_expr(self, node: AssignmentExprNode) -> Any:
        """Generate IR for assignment."""
        node.value.accept(self)
        value_result = self.last_result

        if isinstance(node.target, IdentifierExprNode):
            target_name = node.target.name
            if target_name in self.var_temp_map:
                target_temp = self.var_temp_map[target_name]
            else:
                target_temp = Temporary(target_name)
                self.var_temp_map[target_name] = target_temp

            expr_str = self._get_expression_string(node)

            if node.operator == '=':
                self.current_block.add_instruction(
                    self.builder.emit_move(target_temp, value_result, expr_str)
                )
            else:
                # Compound assignment
                opcode_map = {
                    '+=': IROpcode.ADD,
                    '-=': IROpcode.SUB,
                    '*=': IROpcode.MUL,
                    '/=': IROpcode.DIV,
                    '%=': IROpcode.MOD,
                }
                opcode = opcode_map.get(node.operator)
                if opcode:
                    temp_result = self.builder.new_temp()
                    self.current_block.add_instruction(
                        self.builder.emit(opcode, temp_result, [target_temp, value_result], expr_str)
                    )
                    self.current_block.add_instruction(
                        self.builder.emit_move(target_temp, temp_result, f"update {target_name}")
                    )

            self.last_result = target_temp

        return self.last_result

    # ============ EMPTY STATEMENT ============
    def visit_empty_stmt(self, node: EmptyStmtNode):
        pass

    # ============ STUBS ============
    def visit_param(self, node: ParamNode):
        pass

    def visit_struct_decl(self, node: StructDeclNode):
        pass

    def visit_for_stmt(self, node: ForStmtNode):
        """Generate IR for for loop (simplified)."""
        if node.init:
            node.init.accept(self)

        loop_header = self.builder.new_label("for_header")
        loop_body = self.builder.new_label("for_body")
        loop_update = self.builder.new_label("for_update")
        loop_exit = self.builder.new_label("for_exit")

        old_continue = self.current_loop_continue
        old_break = self.current_loop_break
        self.current_loop_continue = loop_update
        self.current_loop_break = loop_exit

        self.current_block.add_instruction(
            self.builder.emit_jump(loop_header, "for loop")
        )

        header_block = self._new_block(loop_header)
        self.current_function.cfg.add_block(header_block)
        self.current_function.cfg.connect_blocks(self.current_block, header_block)

        self._start_block(header_block)
        if node.condition:
            node.condition.accept(self)
            cond_result = self.last_result
        else:
            cond_result = Literal(True)

        body_block = self._new_block(loop_body)
        update_block = self._new_block(loop_update)
        exit_block = self._new_block(loop_exit)

        self.current_function.cfg.add_block(body_block)
        self.current_function.cfg.add_block(update_block)
        self.current_function.cfg.add_block(exit_block)

        cond_str = self._get_expression_string(node.condition) if node.condition else "true"
        self.current_block.add_instruction(
            self.builder.emit_jump_if(cond_result, loop_body, f"for ({cond_str})")
        )
        self.current_block.add_instruction(
            self.builder.emit_jump(loop_exit)
        )
        self.current_function.cfg.connect_blocks(self.current_block, body_block)
        self.current_function.cfg.connect_blocks(self.current_block, exit_block)

        self._start_block(body_block)
        node.body.accept(self)
        if not self.current_block.is_terminated():
            self.current_block.add_instruction(
                self.builder.emit_jump(loop_update, "for update")
            )
        self.current_function.cfg.connect_blocks(self.current_block, update_block)

        self._start_block(update_block)
        if node.update:
            node.update.accept(self)
        self.current_block.add_instruction(
            self.builder.emit_jump(loop_header, "for loop back")
        )
        self.current_function.cfg.connect_blocks(self.current_block, header_block)

        self._start_block(exit_block)

        self.current_loop_continue = old_continue
        self.current_loop_break = old_break