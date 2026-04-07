token_specs = {
    # Keywords
    "if": "IF",
    "elif": "ELIF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "def": "DEF",
    "return": "RETURN",
    "break": "BREAK",
    "continue": "CONTINUE",
    "AND": "AND",
    "NOT": "NOT",
    "OR": "OR",
    "True": "BOOL_TRUE",
    "False": "BOOL_FALSE",

    # Types
    "int": "INT",
    "float": "FLOAT",
    "bool": "BOOLEAN",
    "char": "CHAR_TYPE",

    # Comments
    "//": "COMMENT",

    # Multi-Char Ops
    "==": "EQ",
    "!=": "NEQ",
    "<=": "LE",
    ">=": "GE",
    "+=": "PLUSEQ",
    "-=": "MINUSEQ",
    "++": "INCR",
    "--": "DECR",

    # Declaration
    "=": "ASSIGN",
    
    # Operators
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
    "%": "MOD",
    "<": "LT",
    ">": "GT",

    # Punctuation
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    ";": "SCOLON",

    # Commas
    ",": "COMMA"

}

MULTICHAR_OPS = {"++", "--", "+=", "-=", "==", "!=", "<=", ">="}