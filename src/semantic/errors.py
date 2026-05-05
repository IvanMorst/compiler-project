class SemanticError(Exception):
    """Semantic analysis error with location information."""
    def __init__(self, message: str, line: int, column: int, context: str = ""):
        self.message = message
        self.line = line
        self.column = column
        self.context = context
        super().__init__(f"[{line}:{column}] {message}" + (f" (in {context})" if context else ""))