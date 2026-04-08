from .symbol_class import Symbol

class ScopeStack:
    def __init__(self):
        self.stack: list[dict[str, Symbol]] = []

    # Scope management
    def push(self) -> None:
        self.stack.append({})

    def pop(self) -> dict[str, Symbol]:
        if not self.stack:
            raise RuntimeError("pop from empty scope stack")
        return self.stack.pop()
    

    @property
    def depth(self) -> int:
        return len(self.stack)
    
    def current_scope(self) -> dict[str, Symbol]:
        if not self.stack:
            raise RuntimeError("No active scope. Check global")
        return self.stack[-1]
    

    # symbol operations
    def declare(self, sym: Symbol) -> None:
        scope = self.current_scope()
        if sym.name in scope:
            raise ValueError(f"Redeclaration in same scope: {sym.name}")
        scope[sym.name] = sym
        
    def lookup(self, name: str):
        for scope in reversed(self.stack):
            sym = scope.get(name)
            if sym is not None:
                return sym
        return None