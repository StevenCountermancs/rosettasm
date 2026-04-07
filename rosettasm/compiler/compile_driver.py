from .lexer import tokenize
from .parser import parseProgram
from .semantics import semantics, SemanticError
from .tac_gen import TACGen
from .liveness_analysis import analyze_tac
from .codegen_x86 import gen_assembly

def read_source(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
    
def compile_source_text(source: str):
    tokens = tokenize(source)
    ast = parseProgram(tokens)
    semantics(ast)
    gen = TACGen()
    tac_list = gen.gen(ast)
    analysis_map, blocks, label_lookup_table = analyze_tac(tac_list)
    asm, home, register_snapshots = gen_assembly(tac_list, analysis_map, label_lookup_table)
    return asm, home, register_snapshots

def compile_file(path: str):
    source = read_source(path)
    return compile_source_text(source)

if __name__ == "__main__":
    path = r"C:\Users\steve\OneDrive - DeSales University\Desktop\MetASM VSCode\program.txt"
    try:
        asm, home, register_snapshots = compile_file(path)
        print(len(asm), len(register_snapshots))

        for i in range(len(asm) - 1):
            snap = register_snapshots[i]
            print(f"\nSTEP {i}")
            print("ASM:", asm[i])
            print("REGISTERS", snap.registers)
            print("VALUES:", snap.register_values)
            
    except (SyntaxError, SemanticError, RuntimeError) as e:
        print(f"Error: {e}"),