import json
import os

#JSON OUTPUT HELPER
def writeTokensToFile(tokens, filename="tokens.json", verbose=False):
    filepath = os.path.join(os.path.dirname(__file__), filename)

    token_dicts = []
    for token in tokens:
        token_dicts.appent({
            "type": token.type,
            "value": token.value,
            "line": token.line,
            "column": token.column
        })

    with open(filepath, "w") as f:
        json.dump(token_dicts, f, indent=4)
    
    if verbose:
        print(f"Tokens written to {filepath}")

###########################################################################

def loadTokensFromFile(filename="tokens.json"):
    script_dir=os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, "output", filename)

    with open(filepath, "r", encoding="utf-8") as f:
        tokenData = json.load(f)
    
    tokens = [
        Token(
            t["category"],
            t["value"],
            t["line"],
            t["start_col"],
            t["end_col"]
        )
        for t in tokenData
    ]
    print(f"Loaded {len(tokens)} tokens from {filepath}")
    return tokens

############################################################################

def printAST(node, indent=0):
    spacer = "  " * indent

    # Safety check: if somehow a non-node slipped in (like a stray string)
    if not isinstance(node, Node):
        print(f"{spacer}{node}")
        return

    # Print the current node’s details
    print(f"{spacer}{node.kind}", end="")

    # Only print operator/value if they exist
    if node.operator is not None:
        print(f" (operator='{node.operator}')", end="")
    if node.value is not None:
        print(f" (value='{node.value}')", end="")

    print()  # newline

    # Recurse for each child
    for child in node.children:
        printAST(child, indent + 1)

###############################################################

if __name__ == "__main__":
    tokens = loadTokensFromFile()
    ast = parseProgram(tokens)
    printAST(ast)

###############################################################