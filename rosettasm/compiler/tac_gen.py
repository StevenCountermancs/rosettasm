from dataclasses import dataclass
from typing import List, Union, Tuple
from .classes.node_class import (
    Node,
    ComparisonNode,
    AssignmentNode,
    IfNode,
    WhileNode,
    ForNode,
    FlowControlNode,
)


@dataclass(frozen=True)
class Temp:
    name: str


@dataclass(frozen=True)
class Var:
    name: str


@dataclass(frozen=True)
class Const:
    value: Union[int, float, str, bool]


@dataclass(frozen=True)
class Label:
    name: str


Operand = Union[Temp, Var, Const]


@dataclass
class Instr:
    op: str
    args: Tuple
    source_span: object = None   # <-- ADDED

    def __str__(self) -> str:
        op = self.op
        a = self.args

        if op == "label":
            return f"{a[0].name}:"
        if op == "goto":
            return f"   goto {a[0].name}"
        if op == "if_goto":
            left, rel, right, lab = a
            return f"   if {fmt(left)} {rel} {fmt(right)} goto {lab.name}"
        if op == "assign":
            dst, src = a
            return f"   {fmt(dst)} = {fmt(src)}"
        if op == "binop":
            dst, left, bop, right = a
            return f"   {fmt(dst)} = {fmt(left)} {bop} {fmt(right)}"
        if op == "return":
            (val,) = a
            return f"   return {fmt(val)}"
        if op == "unop":
            dst, uop, src = a
            return f"   {fmt(dst)} = {uop}{fmt(src)}"
        
        return f"   <unknown {op} {a}>"


def fmt(x):
    if isinstance(x, Temp): return x.name
    if isinstance(x, Var): return x.name
    if isinstance(x, Label): return x.name
    if isinstance(x, Const): return repr(x.value)
    return str(x)


class TACGen:
    def __init__(self):
        self.code: List[Instr] = []
        self.t = 0
        self.l = 0
        self.loop_stack: List[Tuple[Label, Label]] = []

    def new_temp(self) -> Temp:
        name = f"t{self.t}"
        self.t += 1
        return Temp(name)
    
    def new_label(self, prefix="L") -> Label:
        name = f"{prefix}{self.l}"
        self.l += 1
        return Label(name)
    
    def emit(self, op: str, *args, source_span=None):   # <-- UPDATED
        self.code.append(Instr(op, args, source_span))


    def gen(self, root: Node) -> List[Instr]:
        self.gen_node(root)
        return self.code


    def gen_node(self, node: Node):
        if node is None:
            return
        
        k = node.kind

        if k == "ProgramNode":
            for c in node.children:
                self.gen_node(c)
            return
        
        if k == "StatementNode":
            for c in node.children:
                self.gen_node(c)
            return
        
        if k == "BlockNode":
            for s in node.children:
                self.gen_node(s)
            return
        
        if k == "DeclarationNode":
            name = node.children[0].value
            if len(node.children) >= 2:
                rhs = self.gen_expr(node.children[1])
                self.emit("assign", Var(name), rhs, source_span=node.source_span)
            return
        
        if k == "AssignmentNode":
            self.gen_assignment(node)
            return
        
        if k == "IfNode":
            self.gen_if(node)
            return
        
        if k == "ElifNode":
            return
        
        if k == "ElseNode":
            return
        
        if k == "WhileNode":
            self.gen_while(node)
            return
        
        if k == "ForNode":
            self.gen_for(node)
            return
        
        if k == "FlowControlNode":
            self.gen_flow(node)
            return
        
        if k in ("ExpressionNode", "TermNode", "FactorNode", "UnaryNode", "LiteralNode", "IdentifierNode", "ComparisonNode"):
            if k == "ComparisonNode":
                return
            _ = self.gen_expr(node)
            return
        
        for c in node.children:
            self.gen_node(c)


    def gen_expr(self, node: Node) -> Operand:
        k = node.kind
        
        if k == "LiteralNode":
            v = node.value
            cat = node.operator
            if cat == "INT_LIT":
                return Const(int(v))
            if cat == "FLOAT_LIT":
                return Const(float(v))
            if cat == "BOOL_TRUE":
                return Const(True)
            if cat == "BOOL_FALSE":
                return Const(False)
            if cat == "CHAR_LITERAL":
                return Const(v)
            return Const(v)

        if k == "IdentifierNode":
            return Var(node.value)
        
        if k == "FactorNode":
            return self.gen_expr(node.children[0])
        
        if k == "UnaryNode":
            src = self.gen_expr(node.children[0])
            uop = node.operator
            t = self.new_temp()
            self.emit("unop", t, uop, src, source_span=node.source_span)
            return t
        
        if k in ("ExpressionNode", "TermNode"):
            left = self.gen_expr(node.children[0])
            right = self.gen_expr(node.children[1])
            bop = node.operator
            t = self.new_temp()
            self.emit("binop", t, left, bop, right, source_span=node.source_span)
            return t
        
        raise RuntimeError(f"Unsupported expr node: {k}")


    def emit_branch_on_comp(self, comp: ComparisonNode, true_label: Label, false_label: Label):
        left = self.gen_expr(comp.children[0])
        right = self.gen_expr(comp.children[1])
        rel = comp.operator
        self.emit("if_goto", left, rel, right, true_label, source_span=comp.source_span)
        self.emit("goto", false_label, source_span=comp.source_span)


    def gen_assignment(self, node: AssignmentNode):
        op = node.operator
        lhs = node.children[0]
        if lhs.kind != "IdentifierNode":
            raise RuntimeError("Invalid Assignment Target")
        name = lhs.value

        if op == "=":
            rhs = self.gen_expr(node.children[1])
            self.emit("assign", Var(name), rhs, source_span=node.source_span)
            return
        
        if op in ("+=", "-="):
            rhs = self.gen_expr(node.children[1])
            t = self.new_temp()
            bop = op[0]
            self.emit("binop", t, Var(name), bop, rhs, source_span=node.source_span)
            self.emit("assign", Var(name), t, source_span=node.source_span)
            return
        
        if op in ("++", "--"):
            t = self.new_temp()
            bop = "+" if op == "++" else "-"
            self.emit("binop", t, Var(name), bop, Const(1), source_span=node.source_span)
            self.emit("assign", Var(name), t, source_span=node.source_span)
            return
        
        raise RuntimeError(f"Unknown assignment op: {op}")


    def gen_if(self, node: IfNode):
        end = self.new_label("L_end_if_")

        then_lab = self.new_label("L_then_")
        else_chain_lab = self.new_label("L_elsechain_")

        comp = node.children[0]
        then_block = node.children[1]

        self.emit_branch_on_comp(comp, then_lab, else_chain_lab)

        self.emit("label", then_lab, source_span=node.source_span)
        self.gen_node(then_block)
        self.emit("goto", end, source_span=node.source_span)

        self.emit("label", else_chain_lab, source_span=node.source_span)

        i = 2
        while i < len(node.children) and node.children[i].kind == "ElifNode":
            elif_node = node.children[i]
            elif_then = self.new_label("L_then_")
            next_chain = self.new_label("L_elsechain_")

            self.emit_branch_on_comp(elif_node.children[0], elif_then, next_chain)

            self.emit("label", elif_then, source_span=node.source_span)
            self.gen_node(elif_node.children[1])

            self.emit("goto", end, source_span=node.source_span)

            self.emit("label", next_chain, source_span=node.source_span)
            i += 1

        if i < len(node.children) and node.children[i].kind == "ElseNode":
            self.gen_node(node.children[i].children[0])

        self.emit("label", end, source_span=node.source_span)


    def gen_while(self, node: WhileNode):
        head = self.new_label("L_while_head_")
        body = self.new_label("L_while_body_")
        end = self.new_label("L_while_end_")

        self.emit("label", head, source_span=node.source_span)
        self.emit_branch_on_comp(node.children[0], body, end)

        self.emit("label", body, source_span=node.source_span)
        self.loop_stack.append((head, end))
        self.gen_node(node.children[1])
        self.loop_stack.pop()
        self.emit("goto", head, source_span=node.source_span)

        self.emit("label", end, source_span=node.source_span)


    def gen_for(self, node: ForNode):
        if len(node.children) == 1:
            head = self.new_label("L_for_head_")
            body = self.new_label("L_for_body")
            end = self.new_label("L_for_end")

            self.emit("label", head, source_span=node.source_span)
            self.emit("goto", body, source_span=node.source_span)
            self.emit("label", body, source_span=node.source_span)
            self.loop_stack.append((head, end))
            self.gen_node(node.children[0])
            self.loop_stack.pop()
            self.emit("goto", head, source_span=node.source_span)
            self.emit("label", end, source_span=node.source_span)
            return
        
        decl, cond, incr, block = node.children

        self.gen_node(decl)

        head = self.new_label("L_for_head_")
        body = self.new_label("L_for_body_")
        end = self.new_label("L_for_end_")

        self.emit("label", head, source_span=node.source_span)
        self.emit_branch_on_comp(cond, body, end)

        self.emit("label", body, source_span=node.source_span)
        incr_lab = self.new_label("L_for_incr_")
        self.loop_stack.append((incr_lab, end))

        self.gen_node(block)

        self.emit("label", incr_lab, source_span=node.source_span)
        self.gen_node(incr)
        self.loop_stack.pop()
        self.emit("goto", head, source_span=node.source_span)

        self.emit("label", end, source_span=node.source_span)


    def gen_flow(self, node: FlowControlNode):
        if not self.loop_stack:
            raise RuntimeError(f"{node.value} used outside loop")
        cont_lab, break_lab = self.loop_stack[-1]
        if node.value == "break":
            self.emit("goto", break_lab, source_span=node.source_span)
        elif node.value == "continue":
            self.emit("goto", cont_lab, source_span=node.source_span)
        else:
            raise RuntimeError(f"Unknown flow op: {node.value}")