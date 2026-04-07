from enum import Enum, auto
from .tac_gen import Temp, Var, Const
from copy import deepcopy
from dataclasses import dataclass, field
import re
import operator

REL_OPS = {
    "<": operator.lt,
    ">": operator.gt,
    "<=": operator.le,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne,
}


class Register(Enum):
    EAX = auto()
    EBX = auto()
    ECX = auto()
    EDX = auto()
    ESI = auto()
    EDI = auto()
    EBP = auto()
    ESP = auto()
    EIP = auto()
    EFLAGS = auto()


@dataclass
class ExecutionSnapshot:
    registers: dict
    register_values: dict
    memory_values: dict
    highlighted_registers: dict
    highlighted_stack: dict
    source_span: object = None


@dataclass
class CodegenState:
    asm: list[str] = field(default_factory=list)
    snapshots: list[ExecutionSnapshot] = field(default_factory=list)
    registers: dict = field(default_factory=dict)
    register_values: dict = field(default_factory=dict)
    memory_values: dict = field(default_factory=dict)
    homes: dict = field(default_factory=dict)
    frame_size: int = 0


alloc_regs = [Register.EAX, Register.EBX, Register.ECX, Register.EDX]


def gen_assembly(tac_list, analysis_map, label_lookup_table):
    homes = set_homes(tac_list)
    frame_size = compute_stack_size(homes)

    state = CodegenState(
        registers={reg: None for reg in Register},
        register_values={reg: None for reg in Register},
        memory_values={},
        homes=homes,
        frame_size=frame_size,
    )

    # Symbolic pointer-style starting values
    state.register_values[Register.EBP] = "previous frame"
    state.register_values[Register.ESP] = "stack top"

    emit_prologue(state)

    # Program counter
    pc = 0

    while pc < len(tac_list):
        instr = tac_list[pc]
        analysis = analysis_map[pc]
        instr_source_span = instr.source_span

        ######### ASSIGN OPERATION #########
        if instr.op == "assign":
            dst = instr.args[0]
            unload(dst, state)

            src = instr.args[1]

            if isinstance(src, (Var, Temp)):
                src_reg = ensure_in_register(src, analysis, state, source_span=instr_source_span)
                emit_assign(dst, src_reg, state, source_span=instr_source_span)
            else:
                emit_assign(dst, src.value, state, source_span=instr_source_span)

            free_dead_values(analysis, state)

            pc += 1

        ######### BINOP OPERATION #########
        elif instr.op == "binop":
            dst, left, operator, right = instr.args
            unload(dst, state)

            if operator in ("/", "%"):
                emit_div_binop(dst, left, operator, right, analysis, state, source_span=instr_source_span)
            else:
                left_reg = ensure_in_register(left, analysis, state, source_span=instr_source_span)
                right_reg = ensure_in_register(
                    right,
                    analysis,
                    state,
                    forbidden={left_reg},
                    source_span=instr_source_span,
                )

                state.registers[left_reg] = dst
                state.register_values[left_reg] = compute_binop_value(
                    operator,
                    state.register_values[left_reg],
                    state.register_values[right_reg]
                )
                emit_binop(left_reg, operator, right_reg, state, source_span=instr_source_span)

            free_dead_values(analysis, state)

            pc += 1

        ########## UNOP ##########
        elif instr.op == "unop":
            dst, operator, src = instr.args
            unload(dst, state)

            src_reg = ensure_in_register(src, analysis, state, source_span=instr_source_span)

            state.registers[src_reg] = dst
            state.register_values[src_reg] = compute_unop_value(
                operator,
                state.register_values[src_reg]
            )
            emit_unop(src_reg, operator, state, source_span=instr_source_span)

            free_dead_values(analysis, state)

            pc += 1

        elif instr.op == "label":
            pc += 1

        elif instr.op == "goto":
            target_label = instr.args[0]
            pc = label_lookup_table[target_label]

        elif instr.op == "if_goto":
            left, relop, right, target_label = instr.args
            left_value = resolve_operand_value(left, state)
            right_value = resolve_operand_value(right, state)
            condition_true = evaluate_condition(left_value, relop, right_value)

            if condition_true:
                pc = label_lookup_table[target_label]
            else:
                pc += 1

        else:
            raise NotImplementedError(f"Operation {instr.op} not currently implemented.")

    emit_epilogue(state)

    return state.asm, state.homes, state.snapshots


def set_homes(tac_list):
    home = {}
    offset = -4

    for instr in tac_list:
        for arg in instr.args:
            if isinstance(arg, Var) and arg not in home:
                home[arg] = f"[ebp{offset}]"
                offset -= 4

    for instr in tac_list:
        for arg in instr.args:
            if isinstance(arg, Temp) and arg not in home:
                home[arg] = f"[ebp{offset}]"
                offset -= 4

    return home


def compute_stack_size(homes):
    max_offset = 0

    for home in homes.values():
        match = re.fullmatch(r"\[ebp(-\d+)\]", home)
        if match:
            offset = abs(int(match.group(1)))
            max_offset = max(max_offset, offset)

    return max_offset


def format_esp(frame_size):
    if frame_size == 0:
        return "ebp"
    return f"ebp-{frame_size}"


def emit_prologue(state):
    old_ebp = state.register_values[Register.EBP]

    # push ebp
    state.memory_values["[ebp]"] = old_ebp
    state.memory_values["[ebp+4]"] = "<ret>"
    state.register_values[Register.ESP] = "saved ebp slot"

    emit_asm(
        "push ebp",
        state,
        highlighted_registers={
            Register.EBP.name: "purple",
            Register.ESP.name: "purple",
        },
        highlighted_stack={"[ebp]": "purple"},
        source_span=None,
    )

    # mov ebp, esp
    state.register_values[Register.EBP] = "ebp"
    state.register_values[Register.ESP] = "ebp"

    emit_asm(
        "mov ebp, esp",
        state,
        highlighted_registers={
            Register.EBP.name: "purple",
            Register.ESP.name: "purple",
        },
        source_span=None,
    )

    # sub esp, frame_size
    if state.frame_size > 0:
        state.register_values[Register.ESP] = format_esp(state.frame_size)

        emit_asm(
            f"sub esp, {state.frame_size}",
            state,
            highlighted_registers={Register.ESP.name: "purple"},
            source_span=None,
        )


def emit_epilogue(state):
    # mov esp, ebp
    state.register_values[Register.ESP] = "ebp"

    emit_asm(
        "mov esp, ebp",
        state,
        highlighted_registers={
            Register.EBP.name: "purple",
            Register.ESP.name: "purple",
        },
        source_span=None,
    )

    # pop ebp
    state.register_values[Register.EBP] = state.memory_values.get("[ebp]", "prev frame")
    state.register_values[Register.ESP] = "stack top"

    emit_asm(
        "pop ebp",
        state,
        highlighted_registers={
            Register.EBP.name: "purple",
            Register.ESP.name: "purple",
        },
        highlighted_stack={"[ebp]": "purple"},
        source_span=None,
    )

    emit_asm(
        "ret",
        state,
        highlighted_registers={Register.ESP.name: "purple"},
        source_span=None,
    )


def get_register(value, analysis, registers, forbidden=None):
    if forbidden is None:
        forbidden = set()

    # if value already in register
    for reg in alloc_regs:
        if reg in forbidden:
            continue
        if registers[reg] == value:
            return reg, True

    # if a register is empty
    for reg in alloc_regs:
        if reg in forbidden:
            continue
        if registers[reg] is None:
            return reg, False

    # if value in register is not used after
    for reg in alloc_regs:
        if reg in forbidden:
            continue
        val = registers[reg]
        if val is not None and val not in analysis.live_after:
            return reg, False

    # if all values are used, victim is furthest use away
    furthest_use = None
    for reg in alloc_regs:
        if reg in forbidden:
            continue

        val = registers[reg]

        if val is None:
            continue

        if furthest_use is None:
            furthest_use = reg
            continue

        val_fu = registers[furthest_use]

        next_use_reg = analysis.next_use_after.get(val, float("inf"))
        next_use_fu = analysis.next_use_after.get(val_fu, float("inf"))

        if next_use_reg > next_use_fu:
            furthest_use = reg

    return furthest_use, False


def ensure_in_register(value, analysis, state, forbidden=None, source_span=None):
    reg, already_present = get_register(value, analysis, state.registers, forbidden)

    if already_present:
        return reg

    victim = state.registers[reg]

    if victim is not None:
        spill(victim, reg, state, source_span=source_span)

    state.registers[reg] = value

    if isinstance(value, Const):
        state.register_values[reg] = value.value
    else:
        state.register_values[reg] = state.memory_values.get(state.homes[value])

    emit_load(value, reg, state, source_span=source_span)
    return reg


def emit_load(val, reg, state, source_span=None):
    reg_name = reg.name.lower()

    if isinstance(val, (Var, Temp)):
        val_home = state.homes[val]
        emit_asm(
            f"mov {reg_name}, {val_home}",
            state,
            highlighted_registers={reg.name: "green"},
            highlighted_stack={val_home: "green"},
            source_span=source_span,
        )
    elif isinstance(val, Const):
        emit_asm(
            f"mov {reg_name}, {val.value}",
            state,
            highlighted_registers={reg.name: "green"},
            source_span=source_span,
        )
    else:
        raise TypeError(f"Unsupported load operand: {val}")


def emit_assign(dst, src, state, is_spill=False, source_span=None):
    val_home = state.homes[dst]
    color = "orange" if is_spill else "yellow"

    if isinstance(src, Register):
        src_name = src.name.lower()
        state.memory_values[val_home] = state.register_values[src]
        emit_asm(
            f"mov {val_home}, {src_name}",
            state,
            highlighted_stack={val_home: color},
            source_span=source_span,
        )
    else:
        state.memory_values[val_home] = src
        emit_asm(
            f"mov {val_home}, {src}",
            state,
            highlighted_stack={val_home: color},
            source_span=source_span,
        )


def emit_binop(left_reg, op, right_reg, state, source_span=None):
    left_reg_name = left_reg.name.lower()
    right_reg_name = right_reg.name.lower()
    color = "purple"

    if op == "+":
        emit_asm(
            f"add {left_reg_name}, {right_reg_name}",
            state,
            highlighted_registers={left_reg.name: color},
            source_span=source_span,
        )
    elif op == "-":
        emit_asm(
            f"sub {left_reg_name}, {right_reg_name}",
            state,
            highlighted_registers={left_reg.name: color},
            source_span=source_span,
        )
    elif op == "*":
        emit_asm(
            f"imul {left_reg_name}, {right_reg_name}",
            state,
            highlighted_registers={left_reg.name: color},
            source_span=source_span,
        )
    else:
        raise NotImplementedError(f"Unsupported binop operator: {op}")


def emit_unop(reg, op, state, source_span=None):
    reg_name = reg.name.lower()
    color = "purple"

    if op == "-":
        emit_asm(
            f"neg {reg_name}",
            state,
            highlighted_registers={reg.name: color},
            source_span=source_span,
        )


def emit_asm(line, state, highlighted_registers=None, highlighted_stack=None, source_span=None):
    if highlighted_registers is None:
        highlighted_registers = {}

    if highlighted_stack is None:
        highlighted_stack = {}

    state.asm.append(line)
    state.snapshots.append(
        ExecutionSnapshot(
            registers=deepcopy(state.registers),
            register_values=deepcopy(state.register_values),
            memory_values=deepcopy(state.memory_values),
            highlighted_registers=deepcopy(highlighted_registers),
            highlighted_stack=deepcopy(highlighted_stack),
            source_span=source_span,
        )
    )


##################################################
# DIVISION HELPERS - STRICT SPILL / RELOAD PATH
##################################################

def get_reg_divisor(registers):
    for reg in (Register.EBX, Register.ECX):
        if registers[reg] is None:
            return reg
    return Register.EBX


def ensure_eax_has_dividend(value, state, source_span=None):
    # if dividend already in EAX, reuse it
    if state.registers[Register.EAX] == value:
        return

    # always force a clean EAX for division
    eax_victim = state.registers[Register.EAX]
    if eax_victim is not None:
        spill(eax_victim, Register.EAX, state, source_span=source_span)

    state.registers[Register.EAX] = value

    if isinstance(value, Const):
        state.register_values[Register.EAX] = value.value
    else:
        state.register_values[Register.EAX] = state.memory_values.get(state.homes[value])

    emit_load(value, Register.EAX, state, source_span=source_span)


def ensure_edx_available(state, source_span=None):
    edx_victim = state.registers[Register.EDX]
    if edx_victim is not None:
        spill(edx_victim, Register.EDX, state, source_span=source_span)


def choose_divisor_register(analysis, state):
    candidates = (Register.EBX, Register.ECX)

    # Prefer Empty
    for reg in candidates:
        if state.registers[reg] is None:
            return reg

    # Prefer register dead after this instr
    for reg in candidates:
        val = state.registers[reg]
        if val is not None and val not in analysis.live_after:
            return reg

    best_reg = None
    best_next_use = -1

    for reg in candidates:
        val = state.registers[reg]
        next_use = analysis.next_use_after.get(val, float("inf"))
        if best_reg is None or next_use > best_next_use:
            best_reg = reg
            best_next_use = next_use

    return best_reg


def ensure_divisor_in_register(value, analysis, state, source_span=None):
    # if divisor already in EBX or ECX, reuse it
    for reg in (Register.EBX, Register.ECX):
        if state.registers[reg] == value:
            return reg

    reg = choose_divisor_register(analysis, state)

    victim = state.registers[reg]
    if victim is not None:
        spill(victim, reg, state, source_span=source_span)

    state.registers[reg] = value

    if isinstance(value, Const):
        state.register_values[reg] = value.value
    else:
        state.register_values[reg] = state.memory_values.get(state.homes[value])

    emit_load(value, reg, state, source_span=source_span)
    return reg


def emit_div_binop(dst, left, op, right, analysis, state, source_span=None):
    ensure_eax_has_dividend(left, state, source_span=source_span)
    ensure_edx_available(state, source_span=source_span)
    divisor_reg = ensure_divisor_in_register(right, analysis, state, source_span=source_span)

    eax_value = state.register_values[Register.EAX]

    if eax_value is None:
        state.registers[Register.EDX] = "(cdq)"
        state.register_values[Register.EDX] = None
    elif eax_value < 0:
        state.registers[Register.EDX] = "(cdq)"
        state.register_values[Register.EDX] = -1
    else:
        state.registers[Register.EDX] = "(cdq)"
        state.register_values[Register.EDX] = 0

    emit_asm(
        "cdq",
        state,
        highlighted_registers={
            Register.EAX.name: "purple",
            Register.EDX.name: "purple",
        },
        source_span=source_span,
    )

    left_value = state.register_values[Register.EAX]
    right_value = state.register_values[divisor_reg]

    if left_value is None or right_value in (None, 0):
        quotient = None
        remainder = None
    else:
        quotient = left_value // right_value
        remainder = left_value % right_value

    if op == "/":
        state.registers[Register.EAX] = dst
        state.register_values[Register.EAX] = quotient
        state.registers[Register.EDX] = None
        state.register_values[Register.EDX] = None

    elif op == "%":
        state.registers[Register.EDX] = dst
        state.register_values[Register.EDX] = remainder
        state.registers[Register.EAX] = None
        state.register_values[Register.EAX] = None

    else:
        raise NotImplementedError(f"Unsupported division operator: {op}")

    if op == "/":
        result_highlight = {Register.EAX.name: "purple"}
    elif op == "%":
        result_highlight = {Register.EDX.name: "purple"}
    else:
        result_highlight = {}

    emit_asm(
        f"idiv {divisor_reg.name.lower()}",
        state,
        highlighted_registers=result_highlight,
        source_span=source_span,
    )


##################################################
# GENERAL HELPERS
##################################################

def spill(victim, reg, state, source_span=None):
    if victim is not None:
        emit_assign(victim, reg, state, is_spill=True, source_span=source_span)
        state.registers[reg] = None
        state.register_values[reg] = None


def unload(value, state):
    for reg in alloc_regs:
        if state.registers[reg] == value:
            state.registers[reg] = None
            state.register_values[reg] = None


def free_dead_values(analysis, state):
    for reg in alloc_regs:
        current_reg_value = state.registers[reg]
        if current_reg_value is not None and current_reg_value not in analysis.live_after:
            state.registers[reg] = None
            state.register_values[reg] = None


def compute_binop_value(op, left_value, right_value):
    if left_value is None or right_value is None:
        return None

    if op == "+":
        return left_value + right_value
    if op == "-":
        return left_value - right_value
    if op == "*":
        return left_value * right_value

    raise NotImplementedError(f"Unsupported binop operator: {op}")

def compute_unop_value(op, value):
    if value is None:
        return None

    if op == "-":
        return -value

    raise NotImplementedError(f"Unsupported unary operator: {op}")

def resolve_operand_value(operand, state):
    if isinstance(operand, Const):
        return operand.value
    
    for reg in alloc_regs:
        if state.registers[reg] == operand:
            return state.register_values[reg]
        
    if isinstance(operand, (Var, Temp)):
        return state.memory_values.get(state.homes[operand])
    
    raise TypeError(f"Unsupported operand: {operand}")

def evaluate_condition(left_value, relop, right_value):
    if left_value is None or right_value is None:
        return False


    if relop in REL_OPS:
        return REL_OPS[relop](left_value, right_value)
    
    raise NotImplementedError(f"Unsupported relational operator: {relop}")