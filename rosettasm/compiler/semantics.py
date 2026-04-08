from .classes.scope_class import ScopeStack
from .classes.symbol_class import Symbol

class SemanticError(Exception):
    pass

TYPE_MAP = {
    "int": "int",
    "float": "float",
    "boolean": "bool",
    "bool": "bool",
    "char": "char",
}

NUMERIC = {"int", "float"}

#############################################################################
# Function name:        is_numeric                                          #
# Description:          Checks if a type is numeric (int or float)          #
# Parameters:    str –  t: type to evaluate                                 #
# Return Value: bool – True if type is numeric, False otherwise             #
#############################################################################
def is_numeric(t: str | None) -> bool:
    return t in NUMERIC

#############################################################################
# Function name:        is_assignable                                       #
# Description:          Determines if one type can be assigned to another   #
# Parameters:    str –  dst: destination type                               #
#                str –  src: source type                                    #
# Return Value: bool – True if assignment is valid, False otherwise         #
#############################################################################
def is_assignable(dst: str | None, src: str | None) -> bool:
    if dst is None or src is None:
        return True
    if dst == src:
        return True
    return dst == "float" and src == "int"

#############################################################################
# Function name:        semantics                                           #
# Description:          Performs semantic analysis on the AST               #
# Parameters:    Node – ast_root: root of the abstract syntax tree          #
# Return Value: None                                                        #
#############################################################################
def semantics(ast_root):
    scopes = ScopeStack()
    scopes.push()
    _visit(ast_root, scopes)
    scopes.pop()

#############################################################################
# Function name:        semantic_err                                        #
# Description:          Raises a semantic error with optional location info #
# Parameters:    str –  msg: error message                                  #
#                Node – node: AST node for error context                    #
# Return Value: None (raises SemanticError)                                 #
#############################################################################
def semantic_err(msg: str, node=None):
    if node and node.source_span:
        raise SemanticError(f"[Line {node.source_span.line}] {msg}")
    raise SemanticError(msg)

#############################################################################
# Function name:        _visit                                              #
# Description:          Recursively traverses AST to validate semantics     #
# Parameters:    Node – node: current AST node                              #
#                ScopeStack – scopes: current scope stack                   #
#                int – loop_depth: current loop nesting level               #
# Return Value: str/None – inferred type of expression if applicable        #
#############################################################################
def _visit(node, scopes, loop_depth=0):
    if node is None:
        return

    match node.kind:
        case "ProgramNode":
            for child in node.children:
                _visit(child, scopes, loop_depth)

        case "BlockNode":
            scopes.push()
            for stmt in node.children:
                _visit(stmt, scopes, loop_depth)
            scopes.pop()

        case "DeclarationNode":
            dtype = TYPE_MAP.get(node.value, node.value)
            ident_node = node.children[0]
            name = ident_node.value

            sym = Symbol(name=name, decl_node=node, type=dtype, initialized=(len(node.children) >= 2))

            try:
                scopes.declare(sym)
            except ValueError as e:
                semantic_err(str(e), node)

            if len(node.children) >= 2:
                init_t = _visit(node.children[1], scopes, loop_depth)
                if not is_assignable(dtype, init_t):
                    semantic_err(f"Cannot initialize '{name}' as {dtype} with {init_t}", node)

            return dtype

        case "IdentifierNode":
            name = node.value
            sym = scopes.lookup(name)
            if sym is None:
                semantic_err(f"Undeclared identifier: {name}", node)
            if not sym.initialized:
                semantic_err(f"Use of '{name}' before initialization", node)
            return sym.type

        case "AssignmentNode":
            lhs_node = node.children[0]
            if lhs_node.kind != "IdentifierNode":
                semantic_err("Invalid assignment target", node)
            
            sym = scopes.lookup(lhs_node.value)
            if sym is None:
                semantic_err(f"Undeclared identifier: {lhs_node.value}", node)

            lhs_t = sym.type
            op = node.operator
            
            if op in ("=", "+=", "-="):
                rhs_t = _visit(node.children[1], scopes, loop_depth)

                if op != "=" and not (is_numeric(lhs_t) and is_numeric(rhs_t)):
                    semantic_err(f"Operator '{op}' requires numeric types, got {lhs_t} and {rhs_t}", node)
                
                if not is_assignable(lhs_t, rhs_t):
                    semantic_err(f"Type mismatch: cannot assign {rhs_t} to {lhs_t}", node)

                sym.initialized = True
                return lhs_t
            
            if op in ("++", "--"):
                if not is_numeric(lhs_t):
                    semantic_err(f"Operator '{op}' requires numeric type, got {lhs_t}", node)
                
                sym.initialized = True
                return lhs_t
            
            semantic_err(f"Unknown assignment operator: {op}", node)

        case "IfNode":
            cond_t = _visit(node.children[0], scopes, loop_depth)
            if cond_t != "bool":
                semantic_err(f"If condition must be bool, got {cond_t}", node)
            _visit(node.children[1], scopes, loop_depth)
            for optional in node.children[2:]:
                _visit(optional, scopes, loop_depth)

        case "ElifNode":
            cond_t = _visit(node.children[0], scopes, loop_depth)
            if cond_t != "bool":
                semantic_err(f"Elif condition must be bool, got {cond_t}", node)
            _visit(node.children[1], scopes, loop_depth)

        case "ElseNode":
            _visit(node.children[0], scopes, loop_depth)

        case "WhileNode":
            cond_t = _visit(node.children[0], scopes, loop_depth)
            if cond_t != "bool":
                semantic_err(f"While condition must be bool, got {cond_t}", node)
            _visit(node.children[1], scopes, loop_depth + 1)

        case "ForNode":
            scopes.push()
            if len(node.children) == 1:
                _visit(node.children[0], scopes, loop_depth + 1)
            else:
                _visit(node.children[0], scopes, loop_depth)
                cond_t = _visit(node.children[1], scopes, loop_depth)
                if cond_t != "bool":
                    semantic_err(f"For condition must be bool, got {cond_t}", node)
                _visit(node.children[3], scopes, loop_depth + 1)
                _visit(node.children[2], scopes, loop_depth)
            scopes.pop()

        case "UnaryNode":
            operand_t = _visit(node.children[0], scopes, loop_depth)
            op = node.operator

            if op == "-":
                if not is_numeric(operand_t):
                    semantic_err(f"Unary '{op}' requires numeric operand, got {operand_t}", node)
                return operand_t
            semantic_err(f"Unknown unary operator: {op}", node)

        case "FactorNode":
            return _visit(node.children[0], scopes, loop_depth)
        
        case "TermNode" | "ExpressionNode":
            left_t = _visit(node.children[0], scopes, loop_depth)
            right_t = _visit(node.children[1], scopes, loop_depth)
            op = node.operator

            if op in ("+", "-", "*", "/", "%"):
                if not (is_numeric(left_t) and is_numeric(right_t)):
                    semantic_err(f"Operator '{op}' requires numeric operands, got {left_t} and {right_t}", node)
                if left_t == "float" or right_t == "float":
                    return "float"
                return "int"
            return None
        
        case "ComparisonNode":
            left_t = _visit(node.children[0], scopes, loop_depth)
            right_t = _visit(node.children[1], scopes, loop_depth)
            op = node.operator

            if op in ("<", ">", "<=", ">="):
                if not (is_numeric(left_t) and is_numeric(right_t)):
                    semantic_err(f"Operator '{op}' requires numeric operands, got {left_t} and {right_t}", node)
            elif op in ("==", "!="):
                if left_t != right_t and not (is_numeric(left_t) and is_numeric(right_t)):
                    semantic_err(f"Equality '{op}' requires comparable types, got {left_t} and {right_t}", node)
            return "bool"

        case "StatementNode":
            for child in node.children:
                _visit(child, scopes, loop_depth)

        case "LiteralNode":
            category = node.operator

            if category == "INT_LIT":
                return "int"
            if category == "FLOAT_LIT":
                return "float"
            if category in ("BOOL_TRUE", "BOOL_FALSE"):
                return "bool"
            if category == "CHAR_LITERAL":
                return "char"
            
            return None
        
        case "FlowControlNode":
            op = node.value
            if op in ("break", "continue") and loop_depth == 0:
                semantic_err(f"'{op}' used outside of a loop", node)

        case _:
            for child in node.children:
                _visit(child, scopes, loop_depth)