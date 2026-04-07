#Token class that contains:
#   Category of token
#   Value associated
#   Line and Column token is in
class Token:
    def __init__(self, category, value, source_span=None):
        self.category = category
        self.value = value
        self.source_span = source_span

    @property
    def line(self):
        return self.source_span.line if self.source_span else None
    
    @property
    def start_col(self):
        return self.source_span.start_col if self.source_span else None
    
    @property
    def end_col(self):
        return self.source_span.end_col if self.source_span else None

    def __repr__(self):
        return (
            f"Token(category = {self.category}, "
            f"value = {self.value}, "
            f"span={self.source_span})"
        )