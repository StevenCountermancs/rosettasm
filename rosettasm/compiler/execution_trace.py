from copy import deepcopy
from dataclasses import dataclass
from .codegen_x86 import Register


@dataclass
class RuntimeSnapshot:
    registers: dict
    register_values: dict
    memory_values: dict
    highlighted_registers: dict
    highlighted_stack: dict
    source_span: object = None

#############################################################################
# Function name:        build_label_map                                     #
# Description:          Maps assembly labels to their instruction indices   #
# Parameters:    list – asm_lines: list of assembly instructions            #
# Return Value: dict – mapping of label names to instruction indices        #
#############################################################################
def build_label_map(asm_lines):
    label_map = {}

    for i, line in enumerate(asm_lines):
        stripped = line.strip()
        if stripped.endswith(":"):
            label_name = stripped[:-1]
            label_map[label_name] = i

    return label_map

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
# Function name:        is_register                                         #
# Description:          Checks if a token represents a register             #
# Parameters:    str – token: token to evaluate                             #
# Return Value: bool – True if token is a register                          #
#############################################################################
def is_register(token):
    return token in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp", "eip", "eflags")

#############################################################################
# Function name:        is_memory                                           #
# Description:          Checks if a token represents a memory reference     #
# Parameters:    str – token: token to evaluate                             #
# Return Value: bool – True if token is memory reference                    #
#############################################################################
def is_memory(token):
    return token.startswith("[") and token.endswith("]")

#############################################################################
# Function name:        is_immediate                                        #
# Description:          Checks if a token is an immediate value             #
# Parameters:    str – token: token to evaluate                             #
# Return Value: bool – True if token is immediate                           #
#############################################################################
def is_immediate(token):
    if is_register(token) or is_memory(token):
        return False

    try:
        int(token)
        return True
    except ValueError:
        return token in ("True", "False")


#############################################################################
# Function name:        read_operand                                        #
# Description:          Retrieves value of an operand from runtime state    #
# Parameters:    str – token: operand token                                 #
#                dict – state: current runtime state                        #
# Return Value: any – resolved operand value                                #
#############################################################################
def read_operand(token, state):
    token = token.strip()

    if is_register(token):
        return state["register_values"].get(token)

    if is_memory(token):
        return state["memory_values"].get(token)

    if token == "True":
        return True

    if token == "False":
        return False

    return int(token)

#############################################################################
# Function name:        write_operand                                       #
# Description:          Writes a value to register or memory                #
# Parameters:    str – token: destination operand                           #
#                any – value: value to write                                #
#                dict – state: current runtime state                        #
#                any – held_value: associated variable/temp                 #
# Return Value: None                                                        #
#############################################################################
def write_operand(token, value, state, held_value=None):
    token = token.strip()

    if is_register(token):
        state["register_values"][token] = value
        state["register_holds"][token] = held_value
        return

    if is_memory(token):
        state["memory_values"][token] = value
        state["memory_holds"][token] = held_value
        return

    raise ValueError(f"Unsupported destination: {token}")

#############################################################################
# Function name:        resolve_held_value                                  #
# Description:          Retrieves associated variable/temp for operand      #
# Parameters:    str – token: operand token                                 #
#                dict – state: current runtime state                        #
# Return Value: any – associated held value                                 #
#############################################################################
def resolve_held_value(token, state):
    token = token.strip()

    if is_register(token):
        return state["register_holds"].get(token)

    if is_memory(token):
        return state["memory_holds"].get(token)

    return None

#############################################################################
# Function name:        should_jump                                         #
# Description:          Determines if a conditional jump should be taken    #
# Parameters:    str – opcode: jump instruction                             #
#                int – last_cmp: result of last comparison                  #
# Return Value: bool – True if jump condition is satisfied                  #
#############################################################################
def should_jump(opcode, last_cmp):
    if last_cmp is None:
        raise ValueError("Conditional jump encountered before cmp")

    if opcode == "jl":
        return last_cmp < 0
    if opcode == "jg":
        return last_cmp > 0
    if opcode == "jle":
        return last_cmp <= 0
    if opcode == "jge":
        return last_cmp >= 0
    if opcode == "je":
        return last_cmp == 0
    if opcode == "jne":
        return last_cmp != 0

    raise ValueError(f"Unsupported jump opcode: {opcode}")

#############################################################################
# Function name:        set_next_eip                                        #
# Description:          Updates EIP to next instruction location            #
# Parameters:    dict – state: current runtime state                        #
#                int – next_pc: next instruction index                      #
# Return Value: None                                                        #
#############################################################################
def set_next_eip(state, next_pc):
    state["register_values"]["eip"] = next_pc
    state["register_holds"]["eip"] = "(next instr)"

#############################################################################
# Function name:        make_runtime_snapshot                               #
# Description:          Creates snapshot of runtime state for visualization #
# Parameters:    dict – state: current runtime state                        #
#                dict – highlight_regs: registers to highlight              #
#                dict – highlight_stack: stack entries to highlight         #
# Return Value: RuntimeSnapshot – snapshot of execution state               #
#############################################################################
def make_runtime_snapshot(state, highlight_regs=None, highlight_stack=None):
    if highlight_regs is None:
        highlight_regs = {}

    if highlight_stack is None:
        highlight_stack = {}

    ui_registers = {
        Register.EAX: state["register_holds"].get("eax"),
        Register.EBX: state["register_holds"].get("ebx"),
        Register.ECX: state["register_holds"].get("ecx"),
        Register.EDX: state["register_holds"].get("edx"),
        Register.ESI: state["register_holds"].get("esi"),
        Register.EDI: state["register_holds"].get("edi"),
        Register.EBP: state["register_holds"].get("ebp"),
        Register.ESP: state["register_holds"].get("esp"),
        Register.EIP: state["register_holds"].get("eip"),
        Register.EFLAGS: state["register_holds"].get("eflags"),
    }

    ui_register_values = {
        Register.EAX: state["register_values"].get("eax"),
        Register.EBX: state["register_values"].get("ebx"),
        Register.ECX: state["register_values"].get("ecx"),
        Register.EDX: state["register_values"].get("edx"),
        Register.ESI: state["register_values"].get("esi"),
        Register.EDI: state["register_values"].get("edi"),
        Register.EBP: state["register_values"].get("ebp"),
        Register.ESP: state["register_values"].get("esp"),
        Register.EIP: state["register_values"].get("eip"),
        Register.EFLAGS: state["register_values"].get("eflags"),
    }

    return RuntimeSnapshot(
        registers=deepcopy(ui_registers),
        register_values=deepcopy(ui_register_values),
        memory_values=deepcopy(state["memory_values"]),
        highlighted_registers=deepcopy(highlight_regs),
        highlighted_stack=deepcopy(highlight_stack),
        source_span=None,
    )

#############################################################################
# Function name:        build_execution_trace                               #
# Description:          Simulates execution of assembly instructions        #
# Parameters:    list – asm_lines: list of assembly instructions            #
# Return Value: tuple – (execution_indices, execution_snapshots)            #
#############################################################################
def build_execution_trace(asm_lines):
    label_map = build_label_map(asm_lines)

    state = {
        "register_values": {
            "eax": None,
            "ebx": None,
            "ecx": None,
            "edx": None,
            "esi": None,
            "edi": None,
            "ebp": "previous frame",
            "esp": "stack top",
            "eip": None,
            "eflags": None,
        },
        "register_holds": {
            "eax": None,
            "ebx": None,
            "ecx": None,
            "edx": None,
            "esi": None,
            "edi": None,
            "ebp": None,
            "esp": None,
            "eip": "(next instr)",
            "eflags": None,
        },
        "memory_values": {},
        "memory_holds": {},
        "last_cmp": None,
    }

    execution_indices = []
    execution_snapshots = []
    pc = 0

    while pc < len(asm_lines):
        line = asm_lines[pc].strip()
        execution_indices.append(pc)

        if line.endswith(":"):
            set_next_eip(state, pc + 1)
            execution_snapshots.append(make_runtime_snapshot(state))
            pc += 1

        elif line == "push ebp":
            old_ebp = state["register_values"]["ebp"]
            state["memory_values"]["[ebp]"] = old_ebp
            state["memory_values"]["[ebp+4]"] = "<ret>"
            state["register_values"]["esp"] = "saved ebp slot"

            set_next_eip(state, pc + 1)
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={
                        "EBP": "purple",
                        "ESP": "purple",
                    },
                    highlight_stack={"[ebp]": "purple"},
                )
            )
            pc += 1

        elif line == "mov ebp, esp":
            state["register_values"]["ebp"] = "ebp"
            state["register_values"]["esp"] = "ebp"

            set_next_eip(state, pc + 1)
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={
                        "EBP": "purple",
                        "ESP": "purple",
                    },
                )
            )
            pc += 1

        elif line.startswith("sub esp, "):
            amount = int(line.split(",", 1)[1].strip())
            state["register_values"]["esp"] = format_esp(amount)

            set_next_eip(state, pc + 1)
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={"ESP": "purple"},
                )
            )
            pc += 1

        elif line == "mov esp, ebp":
            state["register_values"]["esp"] = "ebp"

            set_next_eip(state, pc + 1)
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={
                        "EBP": "purple",
                        "ESP": "purple",
                    },
                )
            )
            pc += 1

        elif line == "pop ebp":
            state["register_values"]["ebp"] = state["memory_values"].get("[ebp]", "prev frame")
            state["register_values"]["esp"] = "stack top"

            set_next_eip(state, pc + 1)
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={
                        "EBP": "purple",
                        "ESP": "purple",
                    },
                    highlight_stack={"[ebp]": "purple"},
                )
            )
            pc += 1

        elif line == "ret":
            state["register_values"]["eip"] = None
            state["register_holds"]["eip"] = "(next instr)"
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={
                        "ESP": "purple",
                        "EIP": "purple",
                    },
                )
            )
            break

        elif line.startswith("add "):
            rest = line[4:]
            dst, src = [x.strip() for x in rest.split(",", 1)]
            dst_value = read_operand(dst, state)
            src_value = read_operand(src, state)
            write_operand(
                dst,
                dst_value + src_value,
                state,
                held_value=state["register_holds"].get(dst) if is_register(dst) else None,
            )

            set_next_eip(state, pc + 1)
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={dst.upper(): "purple"} if is_register(dst) else {},
                )
            )
            pc += 1

        elif line.startswith("sub "):
            rest = line[4:]
            dst, src = [x.strip() for x in rest.split(",", 1)]
            dst_value = read_operand(dst, state)
            src_value = read_operand(src, state)
            write_operand(
                dst,
                dst_value - src_value,
                state,
                held_value=state["register_holds"].get(dst) if is_register(dst) else None,
            )

            set_next_eip(state, pc + 1)
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={dst.upper(): "purple"} if is_register(dst) else {},
                )
            )
            pc += 1

        elif line.startswith("imul "):
            rest = line[5:]
            dst, src = [x.strip() for x in rest.split(",", 1)]
            dst_value = read_operand(dst, state)
            src_value = read_operand(src, state)
            write_operand(
                dst,
                dst_value * src_value,
                state,
                held_value=state["register_holds"].get(dst) if is_register(dst) else None,
            )

            set_next_eip(state, pc + 1)
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={dst.upper(): "purple"} if is_register(dst) else {},
                )
            )
            pc += 1

        elif line == "cdq":
            eax_value = state["register_values"].get("eax")

            if eax_value is None:
                state["register_values"]["edx"] = None
            elif eax_value < 0:
                state["register_values"]["edx"] = -1
            else:
                state["register_values"]["edx"] = 0

            state["register_holds"]["edx"] = "(cdq)"

            set_next_eip(state, pc + 1)
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={
                        "EAX": "purple",
                        "EDX": "purple",
                    },
                )
            )
            pc += 1

        elif line.startswith("idiv "):
            divisor_token = line[5:].strip()
            divisor_value = read_operand(divisor_token, state)
            eax_value = state["register_values"].get("eax")

            if eax_value is None or divisor_value in (None, 0):
                state["register_values"]["eax"] = None
                state["register_values"]["edx"] = None
            else:
                quotient = int(eax_value / divisor_value)
                remainder = eax_value - (quotient * divisor_value)

                state["register_values"]["eax"] = quotient
                state["register_values"]["edx"] = remainder

            set_next_eip(state, pc + 1)
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={
                        "EAX": "purple",
                        "EDX": "purple",
                    },
                )
            )
            pc += 1

        elif line.startswith("neg "):
            reg = line[4:].strip()
            value = read_operand(reg, state)
            write_operand(
                reg,
                -value,
                state,
                held_value=state["register_holds"].get(reg),
            )

            set_next_eip(state, pc + 1)
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={reg.upper(): "purple"},
                )
            )
            pc += 1

        elif line.startswith("jmp "):
            label_name = line[4:].strip()
            target_pc = label_map[label_name]

            set_next_eip(state, target_pc)
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={"EIP": "purple"},
                )
            )
            pc = target_pc

        elif line.startswith("mov "):
            rest = line[4:]
            dst, src = [x.strip() for x in rest.split(",", 1)]
            value = read_operand(src, state)
            held_value = resolve_held_value(src, state)

            write_operand(dst, value, state, held_value=held_value)

            highlight_regs = {}
            highlight_stack = {}

            if is_register(dst):
                if is_memory(src) or is_immediate(src):
                    highlight_regs[dst.upper()] = "green"
                else:
                    highlight_regs[dst.upper()] = "purple"

            if is_memory(dst):
                highlight_stack[dst] = "yellow"

            if is_memory(src):
                highlight_stack[src] = "green"

            set_next_eip(state, pc + 1)
            execution_snapshots.append(
                make_runtime_snapshot(state, highlight_regs, highlight_stack)
            )
            pc += 1

        elif line.startswith("cmp "):
            rest = line[4:]
            left, right = [x.strip() for x in rest.split(",", 1)]
            left_value = read_operand(left, state)
            right_value = read_operand(right, state)

            cmp_result = left_value - right_value
            state["last_cmp"] = cmp_result

            #Simplified EFLAGS for UI
            state["register_values"]["eflags"] = 0 if cmp_result == 0 else 1
            state["register_holds"]["eflags"] = "(cmp)"

            highlight_regs = {"EFLAGS": "purple"}
            if is_register(left):
                highlight_regs[left.upper()] = "purple"
            if is_register(right):
                highlight_regs[right.upper()] = "purple"

            set_next_eip(state, pc + 1)
            execution_snapshots.append(
                make_runtime_snapshot(state, highlight_regs, {})
            )
            pc += 1

        elif line.startswith(("jl ", "jg ", "jle ", "jge ", "je ", "jne ")):
            opcode, label_name = line.split(maxsplit=1)

            if should_jump(opcode, state["last_cmp"]):
                next_pc = label_map[label_name]
            else:
                next_pc = pc + 1

            set_next_eip(state, next_pc)
            execution_snapshots.append(
                make_runtime_snapshot(
                    state,
                    highlight_regs={"EIP": "purple"},
                )
            )

            pc = next_pc

        else:
            set_next_eip(state, pc + 1)
            execution_snapshots.append(make_runtime_snapshot(state))
            pc += 1

    return execution_indices, execution_snapshots