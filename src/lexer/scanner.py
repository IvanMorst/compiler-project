from .token import Token, TokenType
from .error import LexicalError
from typing import List, Optional, Union


class Scanner:
    keywords = {
        "if": TokenType.KW_IF,
        "else": TokenType.KW_ELSE,
        "while": TokenType.KW_WHILE,
        "for": TokenType.KW_FOR,
        "int": TokenType.KW_INT,
        "float": TokenType.KW_FLOAT,
        "bool": TokenType.KW_BOOL,
        "return": TokenType.KW_RETURN,
        "true": TokenType.KW_TRUE,
        "false": TokenType.KW_FALSE,
        "void": TokenType.KW_VOID,
        "struct": TokenType.KW_STRUCT,
        "fn": TokenType.KW_FN,
    }

    # Multi-character operators (longest first)
    operators = {
        "==": TokenType.EQ,
        "!=": TokenType.NE,
        "<=": TokenType.LE,
        ">=": TokenType.GE,
        "&&": TokenType.AND,
        "||": TokenType.OR,
        "+=": TokenType.PLUS_ASSIGN,
        "-=": TokenType.MINUS_ASSIGN,
        "*=": TokenType.STAR_ASSIGN,
        "/=": TokenType.SLASH_ASSIGN,
        "%=": TokenType.PERCENT_ASSIGN,
        "->": TokenType.ARROW,
        "=": TokenType.ASSIGN,
        "+": TokenType.PLUS,
        "-": TokenType.MINUS,
        "*": TokenType.STAR,
        "/": TokenType.SLASH,
        "%": TokenType.PERCENT,
        "<": TokenType.LT,
        ">": TokenType.GT,
        "!": TokenType.NOT,
    }

    delimiters = {
        "(": TokenType.LPAREN,
        ")": TokenType.RPAREN,
        "{": TokenType.LBRACE,
        "}": TokenType.RBRACE,
        "[": TokenType.LBRACKET,
        "]": TokenType.RBRACKET,
        ";": TokenType.SEMICOLON,
        ",": TokenType.COMMA,
        ".": TokenType.DOT,
        ":": TokenType.COLON,  # <--- ДОБАВЛЯЕМ!
    }
    def __init__(self, source: str):
        self.source = source
        self.start = 0  # start of current lexeme
        self.current = 0  # current position in source
        self.line = 1
        self.column = 1
        self.errors: List[LexicalError] = []  # collected errors for recovery

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def get_line(self) -> int:
        return self.line

    def get_column(self) -> int:
        return self.column

    def advance(self) -> str:
        """Consume the next character and return it."""
        ch = self.source[self.current]
        self.current += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def peek(self) -> str:
        """Look at the current character without consuming."""
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def peek_next(self) -> str:
        """Look at the next character (for multi-character operators)."""
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def peek_next_two(self) -> str:
        """Look at the next two characters (for three-character operators)."""
        if self.current + 2 >= len(self.source):
            return '\0'
        return self.source[self.current] + self.source[self.current + 1] + self.source[self.current + 2]

    def match(self, expected: str) -> bool:
        """Conditionally consume the next character if it matches expected."""
        if self.is_at_end() or self.source[self.current] != expected:
            return False
        self.advance()
        return True

    def skip_whitespace(self):
        """Skip spaces, tabs, and newlines."""
        while not self.is_at_end():
            ch = self.peek()
            if ch in ' \t\r':
                self.advance()
            elif ch == '\n':
                self.advance()
            else:
                break

    def skip_comment(self):
        """Skip single-line or multi-line comment. Return True if comment skipped."""
        if self.peek() == '/' and self.peek_next() == '/':
            # single-line comment
            while not self.is_at_end() and self.peek() != '\n':
                self.advance()
            return True
        elif self.peek() == '/' and self.peek_next() == '*':
            # multi-line comment
            self.advance()  # consume '/'
            self.advance()  # consume '*'
            while not self.is_at_end():
                if self.peek() == '*' and self.peek_next() == '/':
                    self.advance()  # consume '*'
                    self.advance()  # consume '/'
                    break
                self.advance()
            else:
                # Unterminated comment
                self.errors.append(LexicalError("Unterminated multi-line comment", self.line, self.column))
            return True
        return False

    def next_token(self) -> Token:
        """Scan and return the next token."""
        self.skip_whitespace()
        self.start = self.current
        if self.is_at_end():
            return self.make_token(TokenType.END_OF_FILE, "")

        # Check for comments before other tokens
        if self.skip_comment():
            return self.next_token()  # comments produce no token

        ch = self.peek()

        # Identifiers and keywords
        if ch.isalpha() or ch == '_':
            return self.identifier()

        # Numbers
        if ch.isdigit():
            return self.number()

        # Strings
        if ch == '"':
            return self.string()

        # Operators and delimiters
        # First try three-character operators
        three_char = self.peek_next_two()
        if three_char in self.operators:
            self.advance()  # consume first
            self.advance()  # consume second
            self.advance()  # consume third
            return self.make_token(self.operators[three_char], three_char)

        # Then try two-character operators
        two_char = ch + self.peek_next() if not self.is_at_end() else ''
        if two_char in self.operators:
            self.advance()  # consume first
            self.advance()  # consume second
            return self.make_token(self.operators[two_char], two_char)

        # Single-character operator
        if ch in self.operators:
            self.advance()
            return self.make_token(self.operators[ch], ch)

        # Delimiters
        if ch in self.delimiters:
            self.advance()
            return self.make_token(self.delimiters[ch], ch)

        # Unexpected character
        self.advance()
        err = LexicalError(f"Unexpected character '{ch}'", self.line, self.column)
        self.errors.append(err)
        # Return an error token so that parsing can continue
        return self.make_token(TokenType.ERROR, ch)

    def peek_token(self) -> Token:
        """Look at the next token without consuming it."""
        # Save state
        saved_start = self.start
        saved_current = self.current
        saved_line = self.line
        saved_column = self.column
        saved_errors_len = len(self.errors)

        token = self.next_token()

        # Restore state
        self.start = saved_start
        self.current = saved_current
        self.line = saved_line
        self.column = saved_column
        # Errors may have been added during peek; we should remove them
        del self.errors[saved_errors_len:]

        return token

    def make_token(self, token_type: TokenType, lexeme: str,
                   literal: Optional[Union[int, float, str, bool]] = None) -> Token:
        return Token(token_type, lexeme, self.line, self.column - len(lexeme), literal)

    def identifier(self):
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
        text = self.source[self.start:self.current]
        # Check if it's a keyword
        token_type = self.keywords.get(text, TokenType.IDENTIFIER)
        return self.make_token(token_type, text)

    def number(self):
        """Parse integer or float."""
        is_float = False
        while self.peek().isdigit():
            self.advance()
        if self.peek() == '.' and self.peek_next().isdigit():
            is_float = True
            self.advance()  # consume '.'
            while self.peek().isdigit():
                self.advance()
        text = self.source[self.start:self.current]
        if is_float:
            return self.make_token(TokenType.FLOAT_LITERAL, text, float(text))
        else:
            # Convert to int, but check range? We'll assume it fits for Sprint 1
            return self.make_token(TokenType.INT_LITERAL, text, int(text))

    def string(self):
        self.advance()  # consume opening "
        while not self.is_at_end() and self.peek() != '"':

            self.advance()
        if self.is_at_end():
            self.errors.append(LexicalError("Unterminated string", self.line, self.column))
            return self.make_token(TokenType.ERROR, self.source[self.start:self.current])
        self.advance()  # consume closing "
        value = self.source[self.start + 1:self.current - 1]  # exclude quotes
        return self.make_token(TokenType.STRING_LITERAL, self.source[self.start:self.current], value)