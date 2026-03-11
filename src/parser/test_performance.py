import pytest
import time
from src.lexer.scanner import Scanner
from src.parser.parser import Parser


@pytest.mark.slow
class TestParserPerformance:
    """Тесты производительности парсера."""

    def generate_large_program(self, size: int) -> str:
        """Генерирует большую программу для тестирования."""
        lines = ["fn main() {"]

        # Генерируем много объявлений переменных
        for i in range(size):
            lines.append(f"    int x{i} = {i};")

        # Генерируем сложные выражения
        expr = " + ".join(f"x{i}" for i in range(min(100, size)))
        lines.append(f"    int sum = {expr};")

        # Генерируем вложенные if
        for i in range(min(10, size // 10)):
            lines.append(f"    if (x{i} > 0) {{")
            lines.append(f"        x{i} = x{i} - 1;")
            lines.append("    }")

        lines.append("    return 0;")
        lines.append("}")

        return "\n".join(lines)

    def test_parse_time_linear(self):
        """Тест: время парсинга должно расти линейно с размером входа."""
        sizes = [100, 200, 500, 1000]
        times = []

        for size in sizes:
            source = self.generate_large_program(size)

            # Лексический анализ
            scanner = Scanner(source)
            tokens = []
            while not scanner.is_at_end():
                tokens.append(scanner.next_token())

            # Замер времени парсинга
            start = time.time()
            parser = Parser(tokens)
            ast = parser.parse()
            end = time.time()

            times.append(end - start)

            # Проверяем, что AST построен
            assert ast is not None

        # Проверяем, что время растёт примерно линейно
        # Отношение времени к размеру не должно сильно расти
        ratios = [t / s for t, s in zip(times, sizes)]
        avg_ratio = sum(ratios) / len(ratios)

        for ratio in ratios:
            assert ratio < avg_ratio * 2  # Допускаем отклонение в 2 раза

    def test_memory_usage(self):
        """Тест использования памяти."""
        import tracemalloc

        source = self.generate_large_program(1000)

        # Лексический анализ
        scanner = Scanner(source)
        tokens = []
        while not scanner.is_at_end():
            tokens.append(scanner.next_token())

        # Замер памяти до парсинга
        tracemalloc.start()
        before = tracemalloc.get_traced_memory()

        # Парсинг
        parser = Parser(tokens)
        ast = parser.parse()

        # Замер памяти после парсинга
        after = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Проверяем, что память используется эффективно
        # Размер AST не должен превышать размер исходного кода более чем в 10 раз
        source_size = len(source)
        ast_size = after[0] - before[0]

        assert ast_size < source_size * 10

    @pytest.mark.parametrize("nesting_level", [10, 50, 100])
    def test_deep_nesting(self, nesting_level):
        """Тест глубокой вложенности (проверка на переполнение стека)."""
        # Генерируем глубоко вложенные выражения
        expr = "1"
        for _ in range(nesting_level):
            expr = f"({expr} + 1)"

        source = f"int x = {expr};"

        scanner = Scanner(source)
        tokens = []
        while not scanner.is_at_end():
            tokens.append(scanner.next_token())

        # Парсинг не должен упасть с переполнением стека
        parser = Parser(tokens)
        ast = parser.parse()

        assert ast is not None
        assert len(parser.errors) == 0