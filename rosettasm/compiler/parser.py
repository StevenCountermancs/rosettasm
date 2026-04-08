from .constants.constants import (
    TYPE_KEYWORDS,
    COMPARISON_OPS,
    ASSIGN_OPS,
    LITERALS,
    FLOW_OPS,
    BINARY_ASSIGN_OPS,
    UNARY_ASSIGN_OPS,
)

from .classes.node_class import (
    ProgramNode,
    StatementNode,
    DeclarationNode,
    AssignmentNode,
    IfNode,
    ElifNode,
    ElseNode,
    WhileNode,
    ForNode,
    FlowControlNode,
    BlockNode,
    ComparisonNode,
    ExpressionNode,
    TermNode,
    FactorNode,
    LiteralNode,
    IdentifierNode,
    UnaryNode,
)

#############################################################################
# Function name:        parseProgram                                        #
# Description:          Parses a list of tokens into a ProgramNode AST      #
# Parameters:    list – tokens: list of token objects to parse              #
# Return Value: ProgramNode – root node of the generated AST                #
#############################################################################
#Base level of hierarchy
def parseProgram(tokens):
    
    ast = []
    
    #While tokens in program run
    while (tokens):
        ast.append(parseStatement(tokens))
    
    return ProgramNode(ast)
##################################################################################


##############################################################################
# Function name:        parseStatement                                       #
# Description:          Determines and parses a single statement from tokens #
# Parameters:    list – tokens: remaining tokens to be parsed                #
# Return Value: StatementNode – parsed statement node                        #
##############################################################################
#Need to determine the type of statement and call associated function
def parseStatement(tokens):

    #Check for tokens (safety check)
    if not tokens:
        return

    current_token = tokens[0]

    #Determine type of statement based on first token of eachs statement
    match current_token.category:

        # Declarations must start with a type keyword
        case "INT" | "FLOAT" | "BOOLEAN" | "CHAR_TYPE":
            child = parseDeclaration(tokens)
            return StatementNode(child, source_span=child.source_span)

        # Assignment with "=", "+=", "-=", "++", "--"
        case "IDENTIFIER":
            child = parseAssignment(tokens)
            return StatementNode(child, source_span=child.source_span)

        # Check for conditional has to start with "if"
        case "IF":
            child = parseIfStatement(tokens)
            return StatementNode(child, source_span=child.source_span)

        # "While" token for while loop
        case "WHILE":
            child = parseWhileLoop(tokens)
            return StatementNode(child, source_span=child.source_span)

        # "For" token for for loop
        case "FOR":
            child = parseForLoop(tokens)
            return StatementNode(child, source_span=child.source_span)

        # Break and continue for flow control
        case "BREAK" | "CONTINUE":
            child = parseFlowControl(tokens)
            return StatementNode(child, source_span=child.source_span)

        # If not in any of these, default to expression as they can start with non-terminals
        case _:
            child = parseExprStmt(tokens)
            return StatementNode(child, source_span=child.source_span)

##################################################################################

#############################################################################
# Function name:        parseDeclaration                                    #
# Description:          Parses a variable declaration with optional init    #
# Parameters:    list – tokens: remaining tokens to be parsed               #
# Return Value: DeclarationNode – parsed declaration node                   #
#############################################################################
def parseDeclaration(tokens):

    #decl_type will be value of declarationNode
    dType_tok = expect(tokens, TYPE_KEYWORDS, group_mode=True, return_tok_obj=True)
    dType = dType_tok.value

    #decl_id will be child of declarationNode
    identifier = parseFactor(tokens)

    declChildren = [identifier]

    #Optional initialization of identifier
    if tokens and tokens[0].category == "ASSIGN":

        expect(tokens, "ASSIGN")
        declChildren.append(parseExpression(tokens))

    expect(tokens, "SCOLON")

    return DeclarationNode(dType, declChildren, source_span=dType_tok.source_span)

#################################################################################

#############################################################################
# Function name:        parseAssignment                                     #
# Description:          Parses an assignment or update expression           #
# Parameters:    list – tokens: remaining tokens to be parsed               #
#                bool – need_scolon: whether a semicolon is required        #
# Return Value: AssignmentNode – parsed assignment node                     #
#############################################################################
def parseAssignment(tokens, need_scolon=True):

    #This will be a child in the node
    assignId = parseFactor(tokens)

    #This will be value in the node
    operator_tok = expect(tokens, ASSIGN_OPS, group_mode=True, return_tok_obj=True)
    operator = operator_tok.value

    assignmentChildren = [assignId]
    
    if operator in BINARY_ASSIGN_OPS:
        #Mandatory expression following +=, -=, =
        assignmentChildren.append(parseExpression(tokens))
    elif operator in UNARY_ASSIGN_OPS:
        #No expression needed
        pass
    else:
        raise SyntaxError(f"Improper assignment operator {operator}.")
        
    if need_scolon:
        expect(tokens, "SCOLON")

    return AssignmentNode(operator, assignmentChildren, source_span=assignId.source_span)

#################################################################################

#############################################################################
# Function name:        parseIfStatement                                    #
# Description:          Parses an if-elif-else conditional structure        #
# Parameters:    list – tokens: remaining tokens to be parsed               #
# Return Value: IfNode – parsed conditional node                            #
#############################################################################
def parseIfStatement(tokens):

    #discard if, we know it's an if statement
    if_tok = expect(tokens, "IF", return_tok_obj=True)

    ifCondition = parseComparExpression(tokens)
    ifBlock = parseBlock(tokens)

    ifChildren = [ifCondition, ifBlock]

    #iterate to resolve all elif because there can be many
    while tokens and tokens[0].category == "ELIF":

        elif_tok = expect(tokens, "ELIF", return_tok_obj=True)
        ElifChildren = []
        ElifChildren.append(parseComparExpression(tokens))
        ElifChildren.append(parseBlock(tokens))
        ifChildren.append(ElifNode(ElifChildren, source_span=elif_tok.source_span))

    #optional else default (can only be 1)
    if tokens and tokens[0].category == "ELSE":

        else_tok = expect(tokens, "ELSE", return_tok_obj=True)
        elseChildren = [parseBlock(tokens)]
        ifChildren.append(ElseNode(elseChildren, source_span=else_tok.source_span))

    return IfNode(ifChildren, source_span=if_tok.source_span)

################################################################################

#############################################################################
# Function name:        parseWhileLoop                                      #
# Description:          Parses a while loop construct                       #
# Parameters:    list – tokens: remaining tokens to be parsed               #
# Return Value: WhileNode – parsed while loop node                          #
#############################################################################
def parseWhileLoop(tokens):

    #Discard while token, we know it's a while node
    while_tok = expect(tokens, "WHILE", return_tok_obj=True)

    whileChildren = []
    whileChildren.append(parseComparExpression(tokens))
    whileChildren.append(parseBlock(tokens))

    return WhileNode(whileChildren, source_span=while_tok.source_span)

################################################################################

#############################################################################
# Function name:        parseForLoop                                        #
# Description:          Parses a for loop construct                         #
# Parameters:    list – tokens: remaining tokens to be parsed               #
# Return Value: ForNode – parsed for loop node                              #
#############################################################################
def parseForLoop(tokens):

    #Discard for
    for_tok = expect(tokens, "FOR", return_tok_obj=True)

    #Handle parenthesis in comparison expression?
    expect(tokens, "LPAREN")

    if tokens[0].category == "SCOLON":
        expect(tokens, "SCOLON")
        expect(tokens, "SCOLON")
        expect(tokens, "RPAREN")

        return ForNode(children=[parseBlock(tokens)], source_span=for_tok.source_span)

    forChildren = []

    #Iterator declaration
    forChildren.append(parseDeclaration(tokens))

    #Comparison expression
    forChildren.append(parseComparExpression(tokens))
    expect(tokens, "SCOLON")

    #Increment/Decrement etc
    forChildren.append(parseAssignment(tokens, False))
    expect(tokens, "RPAREN")

    #For loop body
    forChildren.append(parseBlock(tokens))

    return ForNode(forChildren, source_span=for_tok.source_span)
    
##################################################################################

#############################################################################
# Function name:        parseFlowControl                                    #
# Description:          Parses flow control statements (break/continue)     #
# Parameters:    list – tokens: remaining tokens to be parsed               #
# Return Value: FlowControlNode – parsed flow control node                  #
#############################################################################
def parseFlowControl(tokens):
    flow_tok = expect(tokens, FLOW_OPS, group_mode=True, return_tok_obj=True)
    flowOp = flow_tok.value
    expect(tokens, "SCOLON")

    return FlowControlNode(flowOp, source_span=flow_tok.source_span)

##################################################################################

#############################################################################
# Function name:        parseBlock                                          #
# Description:          Parses a block of statements enclosed in braces     #
# Parameters:    list – tokens: remaining tokens to be parsed               #
# Return Value: BlockNode – parsed block node                               #
#############################################################################
def parseBlock(tokens):

    #Brace seen, remove from list
    lbrace_tok = expect(tokens, "LBRACE", return_tok_obj=True)

    blockChildren = []

    while tokens and tokens[0].category != "RBRACE":
        blockChildren.append(parseStatement(tokens))

    expect(tokens, "RBRACE")

    return BlockNode(blockChildren, source_span=lbrace_tok.source_span)

###################################################################################

#############################################################################
# Function name:        parseComparExpression                               #
# Description:          Parses a comparison expression                      #
# Parameters:    list – tokens: remaining tokens to be parsed               #
# Return Value: ComparisonNode – parsed comparison node                     #
#############################################################################
def parseComparExpression(tokens):

    lparen = False
    if tokens[0].category == "LPAREN":
        lparen = True
        expect(tokens, "LPAREN")

    comparisonChildren = []
    comparisonChildren.append(parseExpression(tokens))
    comp_tok = expect(tokens, COMPARISON_OPS, group_mode=True, return_tok_obj=True)
    compOp = comp_tok.value
    comparisonChildren.append(parseExpression(tokens))

    if lparen:
        expect(tokens, "RPAREN")

    return ComparisonNode(compOp, comparisonChildren, source_span=comp_tok.source_span)

###################################################################################

#############################################################################
# Function name:        parseExpression                                     #
# Description:          Parses an additive expression (+, -)                #
# Parameters:    list – tokens: remaining tokens to be parsed               #
# Return Value: ExpressionNode – parsed expression node                     #
#############################################################################
def parseExpression(tokens):

    node = parseTerm(tokens)

    while tokens and tokens[0].category in ("ADD", "SUB"):
        op_tok = expect(tokens, ("ADD", "SUB"), group_mode=True, return_tok_obj=True)

        right = parseTerm(tokens)

        node = ExpressionNode(op_tok.value, [node, right], source_span=op_tok.source_span)

    return node

#####################################################################################

#############################################################################
# Function name:        parseTerm                                           #
# Description:          Parses a multiplicative expression (*, /, %)        #
# Parameters:    list – tokens: remaining tokens to be parsed               #
# Return Value: TermNode – parsed term node                                 #
#############################################################################
def parseTerm(tokens):

    node = parseFactor(tokens)

    while tokens and tokens[0].category in ("MUL", "DIV", "MOD"):
        op_tok = expect(tokens, ("MUL", "DIV", "MOD"), group_mode=True, return_tok_obj=True)

        right = parseFactor(tokens)

        node = TermNode(op_tok.value, [node, right], source_span=op_tok.source_span)

    return node

#####################################################################################

#############################################################################
# Function name:        parseFactor                                         #
# Description:          Parses a factor (literal, identifier, unary, group) #
# Parameters:    list – tokens: remaining tokens to be parsed               #
# Return Value:  Node – parsed factor node                                  #
#############################################################################
def parseFactor(tokens):

    if tokens[0].category == "SUB":
        op_tok = expect(tokens, "SUB", return_tok_obj=True)
        operand = parseFactor(tokens)
        return UnaryNode(op_tok.value, [operand], source_span=op_tok.source_span)

    if (tokens[0].category in LITERALS):
        tok = expect(tokens, LITERALS, group_mode=True, return_tok_obj=True)
        n = LiteralNode(tok.value, source_span=tok.source_span)
        n.operator = tok.category
        return n
    
    elif (tokens[0].category == "IDENTIFIER"):
        tok = expect(tokens, "IDENTIFIER", return_tok_obj=True)
        return IdentifierNode(tok.value, source_span=tok.source_span)
    
    elif tokens[0].category == "LPAREN":
        expect(tokens, "LPAREN")
        expr = parseExpression(tokens)
        expect(tokens, "RPAREN")
        return FactorNode(children=[expr], source_span=expr.source_span)
    
    else:
        raise SyntaxError(f"Unexpected token in factor: {tokens[0].value}")

######################################################################################

#############################################################################
# Function name:        parseExprStmt                                       #
# Description:          Parses an expression statement ending in semicolon  #
# Parameters:    list – tokens: remaining tokens to be parsed               #
# Return Value:  Node – parsed expression node                              #
#############################################################################
def parseExprStmt(tokens):
    node = parseExpression(tokens)
    expect(tokens, "SCOLON")
    return node

#####################################################################################

#############################################################################
# Function name:        expect                                              #
# Description:          Validates and consumes the next token from input    #
# Parameters:    list – tokens: remaining tokens to be parsed               #
#                str/tuple – expected_category: expected token type(s)      #
#                bool – return_token: return token value if True            #
#                bool – group_mode: allow multiple valid categories         #
#                bool – return_tok_obj: return full token object if True    #
# Return Value: varies – token value or token object if requested           #
#############################################################################
def expect(tokens, expected_category, return_token=False, group_mode=False, return_tok_obj=False):
    if not tokens:
        raise SyntaxError(f"Unexpected end of input, expected {expected_category}")

    if group_mode:
        if tokens[0].category not in expected_category:
            raise SyntaxError(f"Expected {expected_category}, but found {tokens[0].category} ({tokens[0].value})")
    else:
        if tokens[0].category != expected_category:
            raise SyntaxError(f"Expected {expected_category}, but found {tokens[0].category} ({tokens[0].value})")
    
    token = tokens.pop(0)

    if return_tok_obj:
        return token
    if return_token:
        return token.value