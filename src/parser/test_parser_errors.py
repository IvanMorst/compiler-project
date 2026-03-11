import pytest
from src.parser.parser import Parser, ParseError


class TestParserErrors:
    """Тесты для обработки синтаксических ошибок."""

    def test_error_missing_semicolon(self, get_parser):
        """Тест ошибки: пропущена точка с запятой."""
        source = "int x = 5"
        parser = get_parser(source)

        with pytest.raises(ParseError) as excinfo:
            parser.parse()

        assert "Expected ';'" in str(excinfo.value)
        assert excinfo.value.token.line == 1

    def test_error_missing_parenthesis(self, get_parser):
        """Тест ошибки: пропущена скобка."""
        source = "if (x > 0 { y = 1; }"
        parser = get_parser(source)

        with pytest.raises(ParseError) as excinfo:
            parser.parse()

        assert "Expected ')'" in str(excinfo.value)

    def test_error_missing_expression(self, get_parser):
        """Тест ошибки: ожидалось выражение."""
        source = "int x = ;"
        parser = get_parser(source)

        with pytest.raises(ParseError) as excinfo:
            parser.parse()

        assert "Expected expression" in str(excinfo.value)

    def test_error_unexpected_token(self, get_parser):
        """Тест ошибки: неожиданный токен."""
        source = "int x = 5 @ 3;"
        parser = get_parser(source)

        # Парсер должен выбросить ошибку при обработке '@'
        with pytest.raises(ParseError):
            parser.parse()

    def test_error_missing_function_name(self, get_parser):
        """Тест ошибки: пропущено имя функции."""
        source = "fn () {}"
        parser = get_parser(source)

        with pytest.raises(ParseError) as excinfo:
            parser.parse()

        assert "Expected function name" in str(excinfo.value)

    def test_error_missing_parameter_name(self, get_parser):
        """Тест ошибки: пропущено имя параметра."""
        source = "fn foo(int) {}"
        parser = get_parser(source)

        with pytest.raises(ParseError) as excinfo:
            parser.parse()

        assert "Expected parameter name" in str(excinfo.value)

    def test_error_missing_brace(self, get_parser):
        """Тест ошибки: пропущена закрывающая скобка."""
        source = "fn foo() { int x = 5; "
        parser = get_parser(source)

        with pytest.raises(ParseError) as excinfo:
            parser.parse()

        assert "Expected '}'" in str(excinfo.value)

    def test_error_multiple_errors_recovery(self, get_parser):
        """Тест восстановления после нескольких ошибок."""
        source = """
        int x = ;
        int y = 5
        fn foo() {
            return
        }
        """
        parser = get_parser(source)

        # Парсер должен попытаться восстановиться и найти несколько ошибок
        program = parser.parse()

        # Проверяем, что ошибки были записаны
        assert len(parser.errors) > 0

        # Несмотря на ошибки, парсер должен вернуть какой-то AST
        assert program is not None

    def test_error_in_expression_precedence(self, get_parser):
        """Тест ошибки в выражении с приоритетами."""
        source = "x = 5 + * 3;"
        parser = get_parser(source)

        with pytest.raises(ParseError):
            parser.parse()

    def test_error_unclosed_string(self, scan_tokens, get_parser):
        """Тест ошибки: незакрытая строка (должна быть обнаружена лексером)."""
        source = '"hello;'
        tokens = scan_tokens(source)
        parser = Parser(tokens)

        # Лексер должен создать ERROR токен для незакрытой строки
        error_tokens = [t for t in tokens if t.type.name == "ERROR"]
        assert len(error_tokens) > 0

        # Парсер должен обработать ERROR токен
        with pytest.raises(ParseError):
            parser.parse()

    def test_error_empty_program(self, get_parser):
        """Тест: пустая программа допустима."""
        source = ""
        parser = get_parser(source)
        program = parser.parse()

        assert program is not None
        assert len(program.declarations) == 0
        assert len(parser.errors) == 0

    def test_error_only_comments(self, parse_source):
        """Тест: программа только с комментариями."""
        source = """
        // Это комментарий
        /* Многострочный
           комментарий */
        """
        program = parse_source(source)

        assert len(program.declarations) == 0