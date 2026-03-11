from typing import List, Optional, Union
from src.lexer.token import Token, TokenType
from src.parser.ast import *


class ParseError(Exception):
    """Ошибка синтаксического анализа."""

    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"[{token.line}:{token.column}] {message}")


class Parser:
    """
    Рекурсивный нисходящий парсер для грамматики MiniCompiler.
    Использует один токен предпросмотра (LL(1)).
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.errors: List[ParseError] = []

    def parse(self) -> ProgramNode:
        """Основной метод парсинга. Возвращает корень AST."""
        try:
            return self.parse_program()
        except ParseError as e:
            self.errors.append(e)
            return ProgramNode([])

    # ---- Вспомогательные методы ----

    def is_at_end(self) -> bool:
        """Проверка, достигнут ли конец потока токенов."""
        return self.current >= len(self.tokens) or self.tokens[self.current].type == TokenType.END_OF_FILE

    def peek(self) -> Token:
        """Возвращает текущий токен без потребления."""
        if self.is_at_end():
            return self.tokens[-1]
        return self.tokens[self.current]

    def previous(self) -> Token:
        """Возвращает предыдущий потреблённый токен."""
        return self.tokens[self.current - 1]

    def advance(self) -> Token:
        """Потребляет и возвращает текущий токен."""
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def check(self, token_type: TokenType) -> bool:
        """Проверяет, является ли текущий токен заданного типа."""
        if self.is_at_end():
            return False
        return self.peek().type == token_type

    def match(self, *token_types: TokenType) -> bool:
        """Потребляет текущий токен, если он одного из заданных типов."""
        for token_type in token_types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def consume(self, token_type: TokenType, message: str) -> Token:
        """Потребляет токен заданного типа или выбрасывает ошибку."""
        if self.check(token_type):
            return self.advance()

        error_token = self.peek()
        raise ParseError(message, error_token)

    def synchronize(self):
        """Восстановление после ошибки."""
        self.advance()

        while not self.is_at_end():
            if self.previous().type == TokenType.SEMICOLON:
                return

            token_type = self.peek().type
            if token_type in (TokenType.KW_FN, TokenType.KW_STRUCT, TokenType.KW_IF,
                              TokenType.KW_WHILE, TokenType.KW_FOR, TokenType.KW_RETURN,
                              TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL,
                              TokenType.KW_VOID, TokenType.RBRACE):
                return

            self.advance()

    # ---- Парсинг программы ----

    def parse_program(self) -> ProgramNode:
        """Program ::= { Declaration } EOF"""
        declarations = []

        while not self.is_at_end() and self.peek().type != TokenType.END_OF_FILE:
            try:
                if self.check(TokenType.KW_FN):
                    self.advance()
                    declarations.append(self.parse_function_decl())
                elif self.check(TokenType.KW_STRUCT):
                    self.advance()
                    declarations.append(self.parse_struct_decl())
                else:
                    # На верхнем уровне может быть любая инструкция
                    stmt = self.parse_statement()
                    if stmt:
                        declarations.append(stmt)
            except ParseError as e:
                self.errors.append(e)
                self.synchronize()

        return ProgramNode(declarations)

    # ---- Парсинг функций ----

    def parse_function_decl(self) -> FunctionDeclNode:
        """FunctionDecl ::= "fn" IDENTIFIER "(" [ Parameters ] ")" [ "->" Type ] Block"""
        fn_token = self.previous()
        name_token = self.consume(TokenType.IDENTIFIER, "Expected function name.")
        name = name_token.lexeme

        self.consume(TokenType.LPAREN, "Expected '(' after function name.")

        parameters = []
        if not self.check(TokenType.RPAREN):
            try:
                parameters = self.parse_parameters()
            except ParseError as e:
                self.errors.append(e)
                # Пропускаем до закрывающей скобки
                while not self.check(TokenType.RPAREN) and not self.is_at_end():
                    self.advance()

        self.consume(TokenType.RPAREN, "Expected ')' after parameters.")

        return_type = "void"
        if self.match(TokenType.ARROW):
            try:
                return_type = self.parse_type()
            except ParseError as e:
                self.errors.append(e)

        # Парсим тело функции
        body = self.parse_block_stmt()

        return FunctionDeclNode(fn_token.line, fn_token.column,
                                name, parameters, return_type, body)

    def parse_parameters(self) -> List[ParamNode]:
        """Parameters ::= Parameter { "," Parameter }"""
        parameters = [self.parse_parameter()]

        while self.match(TokenType.COMMA):
            parameters.append(self.parse_parameter())

        return parameters

    def parse_parameter(self) -> ParamNode:
        """Parameter ::= Type [":"] IDENTIFIER"""
        # Сохраняем позицию перед парсингом
        saved_pos = self.current

        try:
            # Парсим тип
            type_name = self.parse_type()

            # Проверяем наличие двоеточия (опционально)
            if self.match(TokenType.COLON):
                pass

            # Проверяем наличие идентификатора
            if not self.check(TokenType.IDENTIFIER):
                # Если нет идентификатора, восстанавливаем позицию и пробуем другой путь
                self.current = saved_pos
                raise ParseError("Expected parameter name.", self.peek())

            name_token = self.consume(TokenType.IDENTIFIER, "Expected parameter name.")
            return ParamNode(name_token.line, name_token.column, type_name, name_token.lexeme)
        except ParseError:
            # В случае ошибки, восстанавливаем позицию и пробуем другой путь
            self.current = saved_pos
            raise

    # ---- Парсинг структур ----

    def parse_struct_decl(self) -> StructDeclNode:
        """StructDecl ::= "struct" IDENTIFIER "{" { VarDecl } "}"""
        struct_token = self.previous()
        name_token = self.consume(TokenType.IDENTIFIER, "Expected struct name.")

        self.consume(TokenType.LBRACE, "Expected '{' after struct name.")

        fields = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            if self.is_type_start():
                field = self.parse_var_decl(is_global=False)
                if field:
                    fields.append(field)
            else:
                self.advance()

        self.consume(TokenType.RBRACE, "Expected '}' after struct fields.")

        return StructDeclNode(struct_token.line, struct_token.column,
                              name_token.lexeme, fields)

    # ---- Парсинг объявлений переменных ----

    def parse_var_decl(self, is_global: bool = False) -> Optional[VarDeclStmtNode]:
        """VarDecl ::= Type IDENTIFIER [ "=" Expression ] ";" """
        if not self.is_type_start():
            return None

        type_name = self.parse_type()

        if not self.check(TokenType.IDENTIFIER):
            return None

        name_token = self.consume(TokenType.IDENTIFIER, "Expected variable name.")

        initializer = None
        if self.match(TokenType.ASSIGN):
            initializer = self.parse_expression()

        if not self.check(TokenType.SEMICOLON):
            return None

        self.consume(TokenType.SEMICOLON, "Expected ';' after variable declaration.")

        return VarDeclStmtNode(name_token.line, name_token.column,
                               type_name, name_token.lexeme, initializer)

    def parse_type(self) -> str:
        """Type ::= "int" | "float" | "bool" | "void" | IDENTIFIER"""
        if self.match(TokenType.KW_INT):
            return "int"
        elif self.match(TokenType.KW_FLOAT):
            return "float"
        elif self.match(TokenType.KW_BOOL):
            return "bool"
        elif self.match(TokenType.KW_VOID):
            return "void"
        elif self.check(TokenType.IDENTIFIER):
            token = self.consume(TokenType.IDENTIFIER, "Expected type name.")
            return token.lexeme
        else:
            token = self.peek()
            raise ParseError(f"Expected type, got {token.type.name}", token)

    # ---- Парсинг инструкций ----

    def parse_statement(self) -> Optional[StatementNode]:
        """Statement ::= Block | IfStmt | WhileStmt | ForStmt | ReturnStmt | ExprStmt | VarDecl | ";" """

        if self.check(TokenType.LBRACE):
            self.advance()
            return self.parse_block_stmt(already_consumed=True)
        elif self.check(TokenType.KW_IF):
            self.advance()
            return self.parse_if_stmt()
        elif self.check(TokenType.KW_WHILE):
            self.advance()
            return self.parse_while_stmt()
        elif self.check(TokenType.KW_FOR):
            self.advance()
            return self.parse_for_stmt()
        elif self.check(TokenType.KW_RETURN):
            self.advance()
            return self.parse_return_stmt()
        elif self.check(TokenType.SEMICOLON):
            token = self.advance()
            return EmptyStmtNode(token.line, token.column)
        elif self.is_type_start():
            # Пытаемся распарсить как объявление переменной
            saved_position = self.current
            try:
                var_decl = self.parse_var_decl(is_global=False)
                if var_decl:
                    return var_decl
            except ParseError:
                pass
            # Если не получилось, восстанавливаем позицию и парсим как выражение
            self.current = saved_position
            return self.parse_expr_stmt()
        else:
            return self.parse_expr_stmt()

    def is_type_start(self) -> bool:
        """Проверяет, начинается ли текущая конструкция с типа."""
        return (self.check(TokenType.KW_INT) or
                self.check(TokenType.KW_FLOAT) or
                self.check(TokenType.KW_BOOL) or
                self.check(TokenType.KW_VOID) or
                self.check(TokenType.IDENTIFIER))

    def parse_block_stmt(self, already_consumed: bool = False) -> BlockStmtNode:
        """Block ::= "{" { Statement } "}"""
        if not already_consumed:
            self.consume(TokenType.LBRACE, "Expected '{' to begin block.")
            opening_brace = self.previous()
        else:
            opening_brace = self.previous()

        statements = []

        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            try:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            except ParseError as e:
                self.errors.append(e)
                # Пропускаем до следующей точки с запятой или закрывающей скобки
                while not self.check(TokenType.SEMICOLON) and not self.check(TokenType.RBRACE) and not self.is_at_end():
                    self.advance()
                if self.check(TokenType.SEMICOLON):
                    self.advance()

        self.consume(TokenType.RBRACE, "Expected '}' after block.")

        return BlockStmtNode(opening_brace.line, opening_brace.column, statements)

    def parse_if_stmt(self) -> IfStmtNode:
        """IfStmt ::= "if" "(" Expression ")" Statement [ "else" Statement ]"""
        if_token = self.previous()

        self.consume(TokenType.LPAREN, "Expected '(' after 'if'.")
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition.")

        then_branch = self.parse_statement()
        if then_branch is None:
            then_branch = EmptyStmtNode(self.peek().line, self.peek().column)

        else_branch = None
        if self.match(TokenType.KW_ELSE):
            else_branch = self.parse_statement()
            if else_branch is None:
                else_branch = EmptyStmtNode(self.peek().line, self.peek().column)

        return IfStmtNode(if_token.line, if_token.column,
                          condition, then_branch, else_branch)

    def parse_while_stmt(self) -> WhileStmtNode:
        """WhileStmt ::= "while" "(" Expression ")" Statement"""
        while_token = self.previous()

        self.consume(TokenType.LPAREN, "Expected '(' after 'while'.")
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition.")

        body = self.parse_statement()
        if body is None:
            body = EmptyStmtNode(self.peek().line, self.peek().column)

        return WhileStmtNode(while_token.line, while_token.column, condition, body)

    def parse_for_stmt(self) -> ForStmtNode:
        """ForStmt ::= "for" "(" [ ExprStmt ] ";" [ Expression ] ";" [ Expression ] ")" Statement"""
        for_token = self.previous()

        self.consume(TokenType.LPAREN, "Expected '(' after 'for'.")

        # Инициализация
        init = None
        if not self.check(TokenType.SEMICOLON):
            try:
                expr = self.parse_expression()
                if self.check(TokenType.SEMICOLON):
                    init = ExprStmtNode(expr.line, expr.column, expr)
            except ParseError:
                # Если ошибка, пропускаем до точки с запятой
                while not self.check(TokenType.SEMICOLON) and not self.is_at_end():
                    self.advance()

        self.consume(TokenType.SEMICOLON, "Expected ';' after for init.")

        # Условие
        condition = None
        if not self.check(TokenType.SEMICOLON):
            try:
                condition = self.parse_expression()
            except ParseError:
                # Если ошибка, пропускаем до точки с запятой
                while not self.check(TokenType.SEMICOLON) and not self.is_at_end():
                    self.advance()

        self.consume(TokenType.SEMICOLON, "Expected ';' after loop condition.")

        # Обновление
        update = None
        if not self.check(TokenType.RPAREN):
            try:
                update = self.parse_expression()
            except ParseError:
                # Если ошибка, пропускаем до закрывающей скобки
                while not self.check(TokenType.RPAREN) and not self.is_at_end():
                    self.advance()

        self.consume(TokenType.RPAREN, "Expected ')' after for clauses.")

        body = self.parse_statement()
        if body is None:
            body = EmptyStmtNode(self.peek().line, self.peek().column)

        return ForStmtNode(for_token.line, for_token.column,
                           init, condition, update, body)

    def parse_return_stmt(self) -> ReturnStmtNode:
        """ReturnStmt ::= "return" [ Expression ] ";" """
        return_token = self.previous()

        value = None
        if not self.check(TokenType.SEMICOLON):
            try:
                value = self.parse_expression()
            except ParseError as e:
                self.errors.append(e)
                # Пропускаем до точки с запятой
                while not self.check(TokenType.SEMICOLON) and not self.is_at_end():
                    self.advance()

        # Проверяем наличие точки с запятой
        if self.check(TokenType.SEMICOLON):
            self.advance()
        else:
            self.errors.append(ParseError("Expected ';' after return statement.", self.peek()))

        return ReturnStmtNode(return_token.line, return_token.column, value)

    def parse_expr_stmt(self) -> ExprStmtNode:
        """ExprStmt ::= Expression ";" """
        expr = self.parse_expression()

        # Проверяем наличие точки с запятой
        if self.check(TokenType.SEMICOLON):
            self.advance()

        return ExprStmtNode(expr.line, expr.column, expr)

    # ---- Парсинг выражений ----

    def parse_expression(self) -> ExpressionNode:
        """Expression ::= Assignment"""
        return self.parse_assignment()

    def parse_assignment(self) -> ExpressionNode:
        """Assignment ::= LogicalOr { ("=" | "+=" | "-=" | "*=" | "/=" | "%=") Assignment }"""
        expr = self.parse_logical_or()

        # Проверяем все возможные операторы присваивания
        if self.check(TokenType.ASSIGN) or self.check(TokenType.PLUS_ASSIGN) or \
                self.check(TokenType.MINUS_ASSIGN) or self.check(TokenType.STAR_ASSIGN) or \
                self.check(TokenType.SLASH_ASSIGN) or self.check(TokenType.PERCENT_ASSIGN):
            operator_token = self.advance()
            operator = operator_token.lexeme
            right = self.parse_assignment()
            return AssignmentExprNode(expr.line, expr.column, expr, operator, right)

        return expr

    def parse_logical_or(self) -> ExpressionNode:
        """LogicalOr ::= LogicalAnd { "||" LogicalAnd }"""
        expr = self.parse_logical_and()

        while self.check(TokenType.OR):
            operator_token = self.advance()
            operator = operator_token.lexeme
            right = self.parse_logical_and()
            expr = BinaryExprNode(expr.line, expr.column, expr, operator, right)

        return expr

    def parse_logical_and(self) -> ExpressionNode:
        """LogicalAnd ::= Equality { "&&" Equality }"""
        expr = self.parse_equality()

        while self.check(TokenType.AND):
            operator_token = self.advance()
            operator = operator_token.lexeme
            right = self.parse_equality()
            expr = BinaryExprNode(expr.line, expr.column, expr, operator, right)

        return expr

    def parse_equality(self) -> ExpressionNode:
        """Equality ::= Relational { ("==" | "!=") Relational }"""
        expr = self.parse_relational()

        while self.check(TokenType.EQ) or self.check(TokenType.NE):
            operator_token = self.advance()
            operator = operator_token.lexeme
            right = self.parse_relational()
            expr = BinaryExprNode(expr.line, expr.column, expr, operator, right)

        return expr

    def parse_relational(self) -> ExpressionNode:
        """Relational ::= Additive { ("<" | "<=" | ">" | ">=") Additive }"""
        expr = self.parse_additive()

        while self.check(TokenType.LT) or self.check(TokenType.LE) or \
                self.check(TokenType.GT) or self.check(TokenType.GE):
            operator_token = self.advance()
            operator = operator_token.lexeme
            right = self.parse_additive()
            expr = BinaryExprNode(expr.line, expr.column, expr, operator, right)

        return expr

    def parse_additive(self) -> ExpressionNode:
        """Additive ::= Multiplicative { ("+" | "-") Multiplicative }"""
        expr = self.parse_multiplicative()

        while self.check(TokenType.PLUS) or self.check(TokenType.MINUS):
            operator_token = self.advance()
            operator = operator_token.lexeme
            right = self.parse_multiplicative()
            expr = BinaryExprNode(expr.line, expr.column, expr, operator, right)

        return expr

    def parse_multiplicative(self) -> ExpressionNode:
        """Multiplicative ::= Unary { ("*" | "/" | "%") Unary }"""
        expr = self.parse_unary()

        while self.check(TokenType.STAR) or self.check(TokenType.SLASH) or self.check(TokenType.PERCENT):
            operator_token = self.advance()
            operator = operator_token.lexeme
            right = self.parse_unary()
            expr = BinaryExprNode(expr.line, expr.column, expr, operator, right)

        return expr

    def parse_unary(self) -> ExpressionNode:
        """Unary ::= ("-" | "!") Unary | Primary"""
        if self.check(TokenType.MINUS) or self.check(TokenType.NOT):
            operator_token = self.advance()
            operator = operator_token.lexeme
            operand = self.parse_unary()
            return UnaryExprNode(operator_token.line, operator_token.column, operator, operand)

        return self.parse_primary()

    def parse_primary(self) -> ExpressionNode:
        """Primary ::= Literal | IDENTIFIER | "(" Expression ")" | Call"""

        if self.check(TokenType.INT_LITERAL):
            token = self.advance()
            return LiteralExprNode(token.line, token.column, token.literal, token.type)

        if self.check(TokenType.FLOAT_LITERAL):
            token = self.advance()
            return LiteralExprNode(token.line, token.column, token.literal, token.type)

        if self.check(TokenType.STRING_LITERAL):
            token = self.advance()
            return LiteralExprNode(token.line, token.column, token.literal, token.type)

        if self.check(TokenType.KW_TRUE) or self.check(TokenType.KW_FALSE):
            token = self.advance()
            value = token.type == TokenType.KW_TRUE
            return LiteralExprNode(token.line, token.column, value, token.type)

        if self.check(TokenType.IDENTIFIER):
            token = self.advance()
            # Проверяем, является ли это вызовом функции
            if self.check(TokenType.LPAREN):
                return self.parse_call(token)
            return IdentifierExprNode(token.line, token.column, token.lexeme)

        if self.check(TokenType.LPAREN):
            self.advance()  # consume '('
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression.")
            return expr

        token = self.peek()
        raise ParseError(f"Expected expression, got {token.type.name}", token)

    def parse_call(self, callee_token: Token) -> CallExprNode:
        """Call ::= IDENTIFIER "(" [ Arguments ] ")" """
        self.consume(TokenType.LPAREN, "Expected '(' after function name.")

        arguments = []
        if not self.check(TokenType.RPAREN):
            arguments = self.parse_arguments()

        self.consume(TokenType.RPAREN, "Expected ')' after arguments.")

        callee = IdentifierExprNode(callee_token.line, callee_token.column, callee_token.lexeme)
        return CallExprNode(callee_token.line, callee_token.column, callee, arguments)

    def parse_arguments(self) -> List[ExpressionNode]:
        """Arguments ::= Expression { "," Expression }"""
        arguments = [self.parse_expression()]

        while self.check(TokenType.COMMA):
            self.advance()  # consume ','
            arguments.append(self.parse_expression())

        return arguments