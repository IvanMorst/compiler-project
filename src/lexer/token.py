from enum import Enum, auto
from typing import Union, Optional

class TokenType(Enum):
    # Keywords
    KW_IF = auto()
    KW_ELSE = auto()
    KW_WHILE = auto()
    KW_FOR = auto()
    KW_INT = auto()
    KW_FLOAT = auto()
    KW_BOOL = auto()
    KW_RETURN = auto()
    KW_TRUE = auto()
    KW_FALSE = auto()
    KW_VOID = auto()
    KW_STRUCT = auto()
    KW_FN = auto()

    # Identifiers & literals
    IDENTIFIER = auto()
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()
    BOOL_LITERAL = auto()

    # Operators
    PLUS = auto()          # +
    MINUS = auto()         # -
    STAR = auto()          # *
    SLASH = auto()         # /
    PERCENT = auto()       # %
    ASSIGN = auto()        # =
    EQ = auto()            # ==
    NE = auto()            # !=
    LT = auto()            # <
    LE = auto()            # <=
    GT = auto()            # >
    GE = auto()            # >=
    AND = auto()           # &&
    OR = auto()            # ||
    NOT = auto()           # !
    PLUS_ASSIGN = auto()   # +=
    MINUS_ASSIGN = auto()  # -=
    STAR_ASSIGN = auto()   # *=
    SLASH_ASSIGN = auto()  # /=
    PERCENT_ASSIGN = auto()# %=

    # Delimiters
    LPAREN = auto()        # (
    RPAREN = auto()        # )
    LBRACE = auto()        # {
    RBRACE = auto()        # }
    LBRACKET = auto()      # [
    RBRACKET = auto()      # ]
    SEMICOLON = auto()     # ;
    COMMA = auto()         # ,
    DOT = auto()           # .

    # Special
    END_OF_FILE = auto()
    ERROR = auto()

class Token:
    def __init__(self, type: TokenType, lexeme: str, line: int, column: int,
                 literal: Optional[Union[int, float, str, bool]] = None):
        self.type = type
        self.lexeme = lexeme
        self.line = line
        self.column = column
        self.literal = literal

    def __repr__(self):
        return f"Token({self.type}, '{self.lexeme}', {self.line}:{self.column}, {self.literal})"

    def format(self) -> str:
        """Return the token in the required test output format."""
        lit = f" {self.literal}" if self.literal is not None else ""
        return f"{self.line}:{self.column} {self.type.name} \"{self.lexeme}\"{lit}"