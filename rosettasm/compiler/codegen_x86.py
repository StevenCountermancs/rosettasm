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

JUMP_MAP = {
    "<": "jl",
    ">": "jg",
    "<=": "jle",
    ">=": "jge",
    "==": "je",
    "!=": "jne",
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
    tac_to_asm_map: dict = field(default_factory=dict)
    current_tac_index: int | None = None
    frame_size: int = 0


alloc_regs = [Register.EAX, Register.EBX, Register.ECX, Register.EDX]

#############################################################################
# Function name:        gen_assembly                                        #
# Description:          Generates x86 assembly and execution trace from TAC #
# Parameters:    list – tac_list: list of TAC instructions                  #
#                list – analysis_map: liveness/next-use analysis data       #
# Return Value: tuple – (asm, homes, snapshots, tac_to_asm_map)             #
#############################################################################
def gen_assembly(tac_list, analysis_map):
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

    for i, instr in enumerate(tac_list):
        state.current_tac_index = i
        analysis = analysis_map[i]
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

        elif instr.op == "label":
            emit_label(instr.args[0], state, source_span=instr_source_span)

        elif instr.op == "goto":
            target_label = instr.args[0]
            emit_goto(target_label, state, source_span=instr_source_span)

        elif instr.op == "if_goto":
            left, relop, right, target_label = instr.args
            emit_if_goto(
                left,
                relop,
                right,
                target_label,
                analysis,
                state,
                source_span=instr_source_span,
            )

        else:
            raise NotImplementedError(f"Operation {instr.op} not currently implemented.")

    state.current_tac_index = None
    emit_epilogue(state)

    return state.asm, state.homes, state.snapshots, state.tac_to_asm_map

#############################################################################
# Function name:        set_homes                                           #
# Description:          Assigns stack locations for variables and temps     #
# Parameters:    list – tac_list: list of TAC instructions                  #
# Return Value: dict – mapping of operands to stack locations               #
#############################################################################
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

#############################################################################
# Function name:        compute_stack_size                                  #
# Description:          Computes required stack frame size from homes       #
# Parameters:    dict – homes: mapping of operands to stack locations       #
# Return Value: int – total stack frame size                                #
#############################################################################
def compute_stack_size(homes):
    max_offset = 0

    for home in homes.values():
        match = re.fullmatch(r"\[ebp(-\d+)\]", home)
        if match:
            offset = abs(int(match.group(1)))
            max_offset = max(max_offset, offset)

    return max_offset

#############################################################################
# Function name:        format_esp                                          #
# Description:          Formats ESP position relative to EBP                #
# Parameters:    int – frame_size: size of stack frame                      #
# Return Value: str – formatted ESP value                                   #
#############################################################################
def format_esp(frame_size):
    if frame_size == 0:
        return "ebp"
    return f"ebp-{frame_size}"

#############################################################################
# Function name:        emit_prologue                                       #
# Description:          Emits function prologue assembly instructions       #
# Parameters:    CodegenState – state: current codegen state                #
# Return Value: None                                                        #
#############################################################################
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

#############################################################################
# Function name:        emit_epilogue                                       #
# Description:          Emits function epilogue assembly instructions       #
# Parameters:    CodegenState – state: current codegen state                #
# Return Value: None                                                        #
#############################################################################
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

####################################################################################
# Function name:        get_register                                               #
# Description:          Selects a register for a value using allocation heuristics #
# Parameters:    Operand – value: value to place in register                       #
#                AnalysisEntry – analysis: liveness data                           #
#                dict – registers: current register mapping                        #
#                set – forbidden: registers to avoid                               #
# Return Value: tuple – (Register, bool indicating if already present)             #
####################################################################################
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

#############################################################################
# Function name:        ensure_in_register                                  #
# Description:          Ensures a value is loaded into a register           #
# Parameters:    Operand – value: value to load                             #
#                AnalysisEntry – analysis: liveness data                    #
#                CodegenState – state: current codegen state                #
#                set – forbidden: registers to avoid                        #
#                object – source_span: source mapping info                  #
# Return Value: Register – register containing the value                    #
#############################################################################
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

#############################################################################
# Function name:        emit_load                                           #
# Description:          Emits assembly to load a value into a register      #
# Parameters:    Operand – val: value to load                               #
#                Register – reg: destination register                       #
#                CodegenState – state: current codegen state                #
#                object – source_span: source mapping info                  #
# Return Value: None                                                        #
#############################################################################
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

#############################################################################
# Function name:        emit_assign                                         #
# Description:          Emits assembly to store a value into memory         #
# Parameters:    Operand – dst: destination variable/temp                   #
#                Register/Const – src: source value                         #
#                CodegenState – state: current codegen state                #
#                bool – is_spill: indicates spill operation                 #
#                object – source_span: source mapping info                  #
# Return Value: None                                                        #
#############################################################################
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
    elif isinstance(src, Const):
        state.memory_values[val_home] = src.value
        emit_asm(f"mov {val_home}, {src.value}",
                 state,
                 highlighted_stack={val_home: color},
                 source_span=source_span,
                )

    else:
        state.memory_values[val_home] = src
        emit_asm(f"mov {val_home}, {src}",
                 state,
                 highlighted_stack={val_home: color},
                 source_span=source_span,
                 )

#############################################################################
# Function name:        emit_binop                                          #
# Description:          Emits assembly for binary arithmetic operations     #
# Parameters:    Register – left_reg: destination register                  #
#                str – op: operator (+, -, *)                               #
#                Register – right_reg: source register                      #
#                CodegenState – state: current codegen state                #
#                object – source_span: source mapping info                  #
# Return Value: None                                                        #
#############################################################################
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

#############################################################################
# Function name:        emit_unop                                           #
# Description:          Emits assembly for unary operations                 #
# Parameters:    Register – reg: target register                            #
#                str – op: unary operator                                   #
#                CodegenState – state: current codegen state                #
#                object – source_span: source mapping info                  #
# Return Value: None                                                        #
#############################################################################
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

#############################################################################
# Function name:        emit_label                                          #
# Description:          Emits a label in assembly output                    #
# Parameters:    Label – label: label to emit                               #
#                CodegenState – state: current codegen state                #
#                object – source_span: source mapping info                  #
# Return Value: None                                                        #
#############################################################################
def emit_label(label, state, source_span=None):
    emit_asm(
        f"{label.name}:",
        state,
        source_span=source_span,
    )

#############################################################################
# Function name:        emit_goto                                           #
# Description:          Emits an unconditional jump instruction             #
# Parameters:    Label – label: target label                                #
#                CodegenState – state: current codegen state                #
#                object – source_span: source mapping info                  #
# Return Value: None                                                        #
#############################################################################
def emit_goto(label, state, source_span=None):
    emit_asm(
        f"jmp {label.name}",
        state,
        highlighted_registers={Register.EIP.name: "purple"},
        source_span=source_span,
    )

#############################################################################
# Function name:        emit_if_goto                                        #
# Description:          Emits conditional jump based on comparison          #
# Parameters:    Operand – left: left operand                               #
#                str – relop: relational operator                           #
#                Operand – right: right operand                             #
#                Label – target_label: jump target                          #
#                AnalysisEntry – analysis: liveness data                    #
#                CodegenState – state: current codegen state                #
#                object – source_span: source mapping info                  #
# Return Value: None                                                        #
#############################################################################
def emit_if_goto(left, relop, right, target_label, analysis, state, source_span=None):
    left_reg = ensure_in_register(left, analysis, state, source_span=source_span)
    right_reg = ensure_in_register(
        right,
        analysis,
        state,
        forbidden={left_reg},
        source_span=source_span,
    )

    emit_asm(
        f"cmp {left_reg.name.lower()}, {right_reg.name.lower()}",
        state,
        highlighted_registers={
            left_reg.name: "purple",
            right_reg.name: "purple",
            Register.EFLAGS.name: "purple",
        },
        source_span=source_span,
    )

    jump_instr = JUMP_MAP[relop]
    emit_asm(
        f"{jump_instr} {target_label.name}",
        state,
        highlighted_registers={Register.EIP.name: "purple"},
        source_span=source_span,
    )

#############################################################################
# Function name:        emit_asm                                            #
# Description:          Appends assembly line and records execution snapshot#
# Parameters:    str – line: assembly instruction                           #
#                CodegenState – state: current codegen state                #
#                dict – highlighted_registers: register highlight info      #
#                dict – highlighted_stack: stack highlight info             #
#                object – source_span: source mapping info                  #
# Return Value: None                                                        #
#############################################################################
def emit_asm(line, state, highlighted_registers=None, highlighted_stack=None, source_span=None):
    if highlighted_registers is None:
        highlighted_registers = {}

    if highlighted_stack is None:
        highlighted_stack = {}

    asm_index = len(state.asm)
    state.asm.append(line)

    if state.current_tac_index is not None:
        state.tac_to_asm_map.setdefault(state.current_tac_index, []).append(asm_index)

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

#############################################################################
# Function name:        get_reg_divisor                                     #
# Description:          Selects a register for division divisor             #
# Parameters:    dict – registers: current register mapping                 #
# Return Value: Register – selected register                                #
#############################################################################
def get_reg_divisor(registers):
    for reg in (Register.EBX, Register.ECX):
        if registers[reg] is None:
            return reg
    return Register.EBX

#############################################################################
# Function name:        ensure_eax_has_dividend                             #
# Description:          Ensures dividend is loaded into EAX                 #
# Parameters:    Operand – value: dividend value                            #
#                CodegenState – state: current codegen state                #
#                object – source_span: source mapping info                  #
# Return Value: None                                                        #
#############################################################################
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

#############################################################################
# Function name:        ensure_edx_available                                #
# Description:          Ensures EDX is available for division operations    #
# Parameters:    CodegenState – state: current codegen state                #
#                object – source_span: source mapping info                  #
# Return Value: None                                                        #
#############################################################################
def ensure_edx_available(state, source_span=None):
    edx_victim = state.registers[Register.EDX]
    if edx_victim is not None:
        spill(edx_victim, Register.EDX, state, source_span=source_span)

#############################################################################
# Function name:        choose_divisor_register                             #
# Description:          Selects optimal register for divisor                #
# Parameters:    AnalysisEntry – analysis: liveness data                    #
#                CodegenState – state: current codegen state                #
# Return Value: Register – chosen register                                  #
#############################################################################
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

#############################################################################
# Function name:        ensure_divisor_in_register                          #
# Description:          Loads divisor into appropriate register             #
# Parameters:    Operand – value: divisor                                   #
#                AnalysisEntry – analysis: liveness data                    #
#                CodegenState – state: current codegen state                #
#                object – source_span: source mapping info                  #
# Return Value: Register – register containing divisor                      #
#############################################################################
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

#############################################################################
# Function name:        emit_div_binop                                      #
# Description:          Emits assembly for division and modulo operations   #
# Parameters:    Operand – dst: destination variable                        #
#                Operand – left: dividend                                   #
#                str – op: operator (/ or %)                                #
#                Operand – right: divisor                                   #
#                AnalysisEntry – analysis: liveness data                    #
#                CodegenState – state: current codegen state                #
#                object – source_span: source mapping info                  #
# Return Value: None                                                        #
#############################################################################
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

#############################################################################
# Function name:        spill                                               #
# Description:          Spills register value to memory                     #
# Parameters:    Operand – victim: value being spilled                      #
#                Register – reg: register holding value                     #
#                CodegenState – state: current codegen state                #
#                object – source_span: source mapping info                  #
# Return Value: None                                                        #
#############################################################################
def spill(victim, reg, state, source_span=None):
    if victim is None:
        return
    
    if isinstance(victim, Const):
        state.registers[reg] = None
        state.register_values[reg] = None
        return

    emit_assign(victim, reg, state, is_spill=True, source_span=source_span)
    state.registers[reg] = None
    state.register_values[reg] = None

#############################################################################
# Function name:        unload                                              #
# Description:          Removes value from any register                     #
# Parameters:    Operand – value: value to unload                           #
#                CodegenState – state: current codegen state                #
# Return Value: None                                                        #
#############################################################################
def unload(value, state):
    for reg in alloc_regs:
        if state.registers[reg] == value:
            state.registers[reg] = None
            state.register_values[reg] = None

#############################################################################
# Function name:        free_dead_values                                    #
# Description:          Frees registers holding dead values                 #
# Parameters:    AnalysisEntry – analysis: liveness data                    #
#                CodegenState – state: current codegen state                #
# Return Value: None                                                        #
#############################################################################
def free_dead_values(analysis, state):
    for reg in alloc_regs:
        current_reg_value = state.registers[reg]
        if current_reg_value is not None and current_reg_value not in analysis.live_after:
            state.registers[reg] = None
            state.register_values[reg] = None

#############################################################################
# Function name:        compute_binop_value                                 #
# Description:          Computes result of binary operation for tracing     #
# Parameters:    str – op: operator                                         #
#                any – left_value: left operand value                       #
#                any – right_value: right operand value                     #
# Return Value: any – computed result or None                               #
#############################################################################
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

#############################################################################
# Function name:        compute_unop_value                                  #
# Description:          Computes result of unary operation for tracing      #
# Parameters:    str – op: operator                                         #
#                any – value: operand value                                 #
# Return Value: any – computed result or None                               #
#############################################################################
def compute_unop_value(op, value):
    if value is None:
        return None

    if op == "-":
        return -value

    raise NotImplementedError(f"Unsupported unary operator: {op}")