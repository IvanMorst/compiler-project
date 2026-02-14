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
    }

    def __init__(self, source: str):
        self.source = source
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.errors: List[LexicalError] = []
        self._eof_returned = False

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def get_line(self) -> int:
        return self.line

    def get_column(self) -> int:
        return self.column

    def advance(self) -> str:
        ch = self.source[self.current]
        self.current += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        elif ch == '\r':
            # Для Windows \r\n, пропускаем \r, обработаем \n позже
            pass
        else:
            self.column += 1
        return ch

    def peek(self) -> str:
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def match(self, expected: str) -> bool:
        if self.is_at_end() or self.source[self.current] != expected:
            return False
        self.advance()
        return True

    def skip_whitespace(self):
        while not self.is_at_end():
            ch = self.peek()
            if ch in ' \t\r\n':
                self.advance()
            else:
                break

    def skip_comment(self) -> bool:
        if self.peek() == '/' and self.peek_next() == '/':
            # single-line comment
            self.advance()  # consume '/'
            self.advance()  # consume '/'
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
                self.errors.append(LexicalError("Unterminated multi-line comment", self.line, self.column))
            return True
        return False

    def next_token(self) -> Token:
        if self.is_at_end() and self._eof_returned:
            return self.make_token(TokenType.END_OF_FILE, "")

        self.skip_whitespace()
        self.start = self.current

        if self.is_at_end():
            self._eof_returned = True
            return self.make_token(TokenType.END_OF_FILE, "")

        if self.skip_comment():
            return self.next_token()

        ch = self.peek()

        if ch.isalpha() or ch == '_':
            return self.identifier()

        if ch.isdigit():
            return self.number()

        if ch == '"':
            return self.string()

        if ch in '=!<>+-*/%&|':
            two_char = ch + self.peek_next() if not self.is_at_end() else ''
            if two_char in self.operators:
                self.advance()
                self.advance()
                return self.make_token(self.operators[two_char], two_char)
            if ch in self.operators:
                self.advance()
                return self.make_token(self.operators[ch], ch)

        if ch in self.delimiters:
            self.advance()
            return self.make_token(self.delimiters[ch], ch)

        self.advance()
        err = LexicalError(f"Unexpected character '{ch}'", self.line, self.column)
        self.errors.append(err)
        return self.make_token(TokenType.ERROR, ch)

    def peek_token(self) -> Token:
        saved_start = self.start
        saved_current = self.current
        saved_line = self.line
        saved_column = self.column
        saved_eof_returned = self._eof_returned
        saved_errors_len = len(self.errors)

        token = self.next_token()

        self.start = saved_start
        self.current = saved_current
        self.line = saved_line
        self.column = saved_column
        self._eof_returned = saved_eof_returned
        del self.errors[saved_errors_len:]

        return token

    def make_token(self, token_type: TokenType, lexeme: str,
                   literal: Optional[Union[int, float, str, bool]] = None) -> Token:
        if token_type == TokenType.END_OF_FILE:
            return Token(token_type, lexeme, self.line, self.column, literal)
        # Для обычных токенов колонка - это позиция начала лексемы
        return Token(token_type, lexeme, self.line, self.column - len(lexeme), literal)

    def identifier(self):
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
        text = self.source[self.start:self.current]
        token_type = self.keywords.get(text, TokenType.IDENTIFIER)
        return self.make_token(token_type, text)

    def number(self):
        is_float = False
        while self.peek().isdigit():
            self.advance()
        if self.peek() == '.' and self.peek_next().isdigit():
            is_float = True
            self.advance()
            while self.peek().isdigit():
                self.advance()
        text = self.source[self.start:self.current]
        if is_float:
            return self.make_token(TokenType.FLOAT_LITERAL, text, float(text))
        else:
            return self.make_token(TokenType.INT_LITERAL, text, int(text))

    def string(self):
        self.advance()
        start_line = self.line
        start_column = self.column - 1
        while not self.is_at_end() and self.peek() != '"':
            self.advance()
        if self.is_at_end():
            self.errors.append(LexicalError("Unterminated string", start_line, start_column))
            return self.make_token(TokenType.ERROR, self.source[self.start:self.current])
        self.advance()
        value = self.source[self.start + 1:self.current - 1]
        return self.make_token(TokenType.STRING_LITERAL, self.source[self.start:self.current], value)