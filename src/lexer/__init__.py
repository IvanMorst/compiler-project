"""
MiniCompiler - A simplified C-like language compiler.
Sprint 1: Lexical Analysis
"""

__version__ = "0.1.0"
__author__ = "Your Team"
__email__ = "team@example.com"

from src.lexer.token import Token, TokenType
from src.lexer.scanner import Scanner
from src.lexer.error import LexicalError

__all__ = [
    "Token",
    "TokenType",
    "Scanner",
    "LexicalError",
    "__version__",
]