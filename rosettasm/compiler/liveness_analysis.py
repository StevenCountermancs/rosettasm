from .tac_gen import *

class AnalysisEntry:
    def __init__(self):
        self.used = set()
        self.defined = set()
        self.live_before = set()
        self.live_after = set()
        self.next_use_before = {}
        self.next_use_after = {}

##############################################################################
# Function name:        label_mapping                                        #
# Description:          Maps labels to their corresponding instruction index #
# Parameters:    list – tac_list: list of TAC instructions                   #
# Return Value: dict – mapping of Label objects to instruction indices       #
##############################################################################
def label_mapping(tac_list):

    label_lookup_table = {}

    for i, instruction in enumerate(tac_list):
        if instruction.op == "label":
            label_lookup_table[instruction.args[0]] = i

    return label_lookup_table

#############################################################################
# Function name:        control_flow_mapping                                #
# Description:          Builds control flow graph for TAC instructions      #
# Parameters:    list – tac_list: list of TAC instructions                  #
#                dict – label_lookup_table: label to index mapping          #
# Return Value: dict – mapping of instruction index to successor indices    #
#############################################################################
def control_flow_mapping(tac_list, label_lookup_table):

    control_mapping = {}

    for i, instruction in enumerate(tac_list):
        if instruction.op in ("assign", "binop", "unop", "label"):
            if (i + 1) < len(tac_list):
                control_mapping[i] = [i + 1]
            else:
                control_mapping[i] = []
        elif instruction.op == "goto":
            control_mapping[i] = [label_lookup_table[instruction.args[0]]]
        elif instruction.op == "if_goto":
            if (i + 1) < len(tac_list):
                control_mapping[i] = [label_lookup_table[instruction.args[-1]], i + 1]
            else:
                control_mapping[i] = [label_lookup_table[instruction.args[-1]]]
        else:
            raise RuntimeError(f"Operation {instruction.op} not yet implemented.")

    return control_mapping

#############################################################################
# Function name:        liveness_analysis                                   #
# Description:          Computes live variable information for TAC          #
# Parameters:    list – tac_list: list of TAC instructions                  #
#                dict – control_map: control flow mapping                   #
# Return Value: list – list of AnalysisEntry objects with liveness data     #
#############################################################################
def liveness_analysis(tac_list, control_map):

    analysis_map = [AnalysisEntry() for _ in tac_list]

    for i, instruction in enumerate(tac_list):
        if instruction.op  == "assign":
            dst, src = instruction.args
            analysis_map[i].defined.add(dst)
            if isinstance(src, (Temp, Var)):
                analysis_map[i].used.add(src)
        
        elif instruction.op == "binop":
            dst, left, bop, right = instruction.args
            analysis_map[i].defined.add(dst)
            if isinstance(left, (Temp, Var)):
                analysis_map[i].used.add(left)
            if isinstance(right, (Temp, Var)):
                analysis_map[i].used.add(right)

        elif instruction.op == "unop":
            dst, uop, src = instruction.args
            analysis_map[i].defined.add(dst)
            if isinstance(src, (Temp, Var)):
                analysis_map[i].used.add(src)

        elif instruction.op == "if_goto":
            left, relop, right, label = instruction.args
            if isinstance(left, (Temp, Var)):
                analysis_map[i].used.add(left)
            if isinstance(right, (Temp, Var)):
                analysis_map[i].used.add(right)
        
        elif instruction.op in ("goto", "label"):
            continue

        else:
            raise RuntimeError(f"{instruction.op} not currently supported.")

    changed = True
    while changed:
        changed = False

        for i in range(len(tac_list) - 1, -1, -1):
            entry = analysis_map[i]

            old_before = set(entry.live_before)
            old_after = set(entry.live_after)

            new_live_after = set()
            for j in control_map[i]:
                new_live_after |= analysis_map[j].live_before
            new_live_before = entry.used | (new_live_after - entry.defined)
            entry.live_after = new_live_after
            entry.live_before = new_live_before
        
            if (entry.live_before != old_before) or (entry.live_after != old_after):
                changed = True
    return analysis_map

#############################################################################
# Function name:        basic_block_builder                                 #
# Description:          Identifies and constructs basic blocks from TAC     #
# Parameters:    list – tac_list: list of TAC instructions                  #
#                dict – label_lookup_table: label to index mapping          #
# Return Value: list – list of basic blocks (lists of instruction indices)  #
#############################################################################
def basic_block_builder(tac_list, label_lookup_table):
    leaders = set()

    if len(tac_list) > 0:
        leaders.add(0)

    for i, instr in enumerate(tac_list):
        if instr.op == "label":
            leaders.add(i)

        elif instr.op == "goto":
            leaders.add(label_lookup_table[instr.args[0]])
            if (i + 1) < len(tac_list):
                leaders.add(i + 1)
        
        elif instr.op == "if_goto":
            leaders.add(label_lookup_table[instr.args[-1]])
            if (i + 1) < len(tac_list):
                leaders.add(i + 1)
    
    sorted_leaders = sorted(leaders)

    blocks = []

    for i in range(len(sorted_leaders)):
        block = []
        if i < (len(sorted_leaders) - 1):
            for j in range(sorted_leaders[i], sorted_leaders[i + 1]):
                block.append(j)
        else:
            for j in range(sorted_leaders[i], len(tac_list)):
                block.append(j)
        blocks.append(block)
    
    return blocks

#############################################################################
# Function name:        next_use_analysis                                   #
# Description:          Computes next-use information for variables         #
# Parameters:    list – tac_list: list of TAC instructions                  #
#                list – analysis_map: liveness analysis results             #
#                list – blocks: list of basic blocks                        #
# Return Value: list – updated analysis_map with next-use data              #
#############################################################################
def next_use_analysis(tac_list, analysis_map, blocks):
    for block in blocks:
        next_use_table = {}
        for i in reversed(block):
            entry = analysis_map[i]
            entry.next_use_after = next_use_table.copy()

            for x in entry.defined:
                next_use_table.pop(x, None)
            
            for y in entry.used:
                next_use_table[y] = i
            
            entry.next_use_before = next_use_table.copy()
    return analysis_map

#############################################################################
# Function name:        analyze_tac                                         #
# Description:          Runs full analysis pipeline on TAC instructions     #
# Parameters:    list – tac_list: list of TAC instructions                  #
# Return Value: tuple – (analysis_map, blocks, label_lookup_table)          #
#############################################################################
def analyze_tac(tac_list):
    label_lookup_table = label_mapping(tac_list)
    control_map = control_flow_mapping(tac_list, label_lookup_table)
    analysis_map = liveness_analysis(tac_list, control_map)
    blocks = basic_block_builder(tac_list, label_lookup_table)
    analysis_map = next_use_analysis(tac_list, analysis_map, blocks)

    return analysis_map, blocks, label_lookup_table

#############################################################################
# Function name:        print_analysis                                      #
# Description:          Prints detailed liveness and next-use analysis      #
# Parameters:    list – tac_list: list of TAC instructions                  #
#                list – analysis_map: analysis results                      #
# Return Value: None                                                        #
#############################################################################
def print_analysis(tac_list, analysis_map):
    for i, instruction in enumerate(tac_list):
        entry = analysis_map[i]

        print(f"{i}: {instruction}")
        print(f"   used:        {entry.used}")
        print(f"   defined:     {entry.defined}")
        print(f"   live_before: {entry.live_before}")
        print(f"   live_after:  {entry.live_after}")
        print(f"   next_use_before: {entry.next_use_before}")
        print(f"   next_use_after:  {entry.next_use_after}")
        print()

#############################################################################
# Function name:        print_basic_blocks                                  #
# Description:          Prints TAC instructions grouped by basic blocks     #
# Parameters:    list – tac_list: list of TAC instructions                  #
#                list – blocks: list of basic blocks                        #
# Return Value: None                                                        #
#############################################################################
def print_basic_blocks(tac_list, blocks):
    for b_index, block in enumerate(blocks):
        print(f"Block {b_index}:")
        
        for i in block:
            print(f"   {i}: {tac_list[i]}")
        
        print()
