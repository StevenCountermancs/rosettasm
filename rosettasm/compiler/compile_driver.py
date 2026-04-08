from .lexer import tokenize
from .parser import parseProgram
from .semantics import semantics
from .tac_gen import TACGen
from .liveness_analysis import analyze_tac
from .codegen_x86 import gen_assembly
from .execution_trace import build_execution_trace


#############################################################################
# Function name:        read_source                                         #
# Description:          Reads source code from a file path                  #
# Parameters:    str –  path: path to the source file                       #
# Return Value: str – source code read from the file                        #
#############################################################################
def read_source(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


#############################################################################
# Function name:        compile_source_text                                 #
# Description:          Runs the full compilation pipeline on source text   #
# Parameters:    str –  source: source code to compile                      #
# Return Value: tuple – compilation outputs for UI and execution tracing    #
#############################################################################
def compile_source_text(source: str):
    tokens = tokenize(source)
    ast = parseProgram(tokens)
    semantics(ast)

    gen = TACGen()
    tac_list = gen.gen(ast)

    analysis_map, _, _ = analyze_tac(tac_list)
    asm, home, register_snapshots, tac_to_asm_map = gen_assembly(tac_list, analysis_map)
    execution_indices, execution_snapshots = build_execution_trace(asm)

    return asm, home, register_snapshots, execution_indices, execution_snapshots, tac_to_asm_map


#############################################################################
# Function name:        compile_file                                        #
# Description:          Reads a source file and compiles its contents       #
# Parameters:    str –  path: path to the source file                       #
# Return Value: tuple – compilation outputs for UI and execution tracing    #
#############################################################################
def compile_file(path: str):
    source = read_source(path)
    return compile_source_text(source)
