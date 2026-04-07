class Node:
    def __init__(self, kind, value=None, operator=None, children=None, source_span=None):
        self.kind = kind
        self.value = value
        self.operator = operator
        self.source_span = source_span
        
        if children is None:
            self.children = []
        elif isinstance(children, list):
            self.children = children
        else:
            self.children = [children]

    def __repr__(self):
        return (
            f"Node:\n"
            f"Kind: {self.kind}\n"
            f"Value: {self.value}\n"
            f"Operator: {self.operator}\n"
            f"SourceSpan: {self.source_span}\n"
            f"Children: {self.children}"
        )

class LiteralNode(Node):
    def __init__(self, value, source_span=None):
        super().__init__("LiteralNode", value=value, source_span=source_span)

class IdentifierNode(Node):
    def __init__(self, value, source_span=None):
        super().__init__("IdentifierNode", value=value, source_span=source_span)

class FactorNode(Node):
    def __init__(self, children, source_span=None):
        super().__init__("FactorNode", children=children, source_span=source_span)

class TermNode(Node):
    def __init__(self, operator, children, source_span=None):
        super().__init__("TermNode", operator=operator, children=children, source_span=source_span)

class ExpressionNode(Node):
    def __init__(self, operator, children, source_span=None):
        super().__init__("ExpressionNode", operator=operator, children=children, source_span=source_span)

class DeclarationNode(Node):
    def __init__(self, value, children, source_span=None):
        super().__init__("DeclarationNode", value=value, children=children, source_span=source_span)

class AssignmentNode(Node):
    def __init__(self, operator, children, source_span=None):
        super().__init__("AssignmentNode", operator=operator, children=children, source_span=source_span)

class BlockNode(Node):
    def __init__(self, children, source_span=None):
        super().__init__("BlockNode", children=children, source_span=source_span)

class FlowControlNode(Node):
    def __init__(self, value, source_span=None):
        super().__init__("FlowControlNode", value=value, source_span=source_span)

class IfNode(Node):
    def __init__(self, children, source_span=None):
        super().__init__("IfNode", children=children, source_span=source_span)

class ElifNode(Node):
    def __init__(self, children, source_span=None):
        super().__init__("ElifNode", children=children, source_span=source_span)

class ElseNode(Node):
    def __init__(self, children, source_span=None):
        super().__init__("ElseNode", children=children, source_span=source_span)

class ComparisonNode(Node):
    def __init__(self, operator, children, source_span=None):
        super().__init__("ComparisonNode", operator=operator, children=children, source_span=source_span)

class WhileNode(Node):
    def __init__(self, children, source_span=None):
        super().__init__("WhileNode", children=children, source_span=source_span)

class ForNode(Node):
    def __init__(self, children, source_span=None):
        super().__init__("ForNode", children=children, source_span=source_span)

class ProgramNode(Node):
    def __init__(self, children, source_span=None):
        super().__init__("ProgramNode", children=children, source_span=source_span)

class StatementNode(Node):
    def __init__(self, children, source_span=None):
        super().__init__("StatementNode", children=children, source_span=source_span)

class UnaryNode(Node):
    def __init__(self, operator, children, source_span=None):
        super().__init__("UnaryNode", operator=operator, children=children, source_span=source_span)