import pytest
import subprocess
import tempfile
import os
from pathlib import Path


class TestIntegration:
    """Интеграционные тесты для полного цикла компиляции."""

    @pytest.fixture
    def compiler_cli(self):
        """Возвращает путь к CLI компилятора."""
        return Path(__file__).parent.parent.parent / "src" / "main.py"

    def test_full_pipeline(self, compiler_cli):
        """Тест полного конвейера: лексер -> парсер -> вывод."""
        source = """
        fn main() {
            int x = 42;
            return x;
        }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.src', delete=False) as f:
            f.write(source)
            src_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            out_file = f.name

        try:
            # Запускаем компилятор
            result = subprocess.run(
                ['python', str(compiler_cli), 'parse', '--input', src_file, '--output', out_file],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0

            # Проверяем вывод
            with open(out_file, 'r') as f:
                output = f.read()

            assert "Program" in output
            assert "FunctionDecl: main" in output
            assert "VarDecl: int x = 42" in output
            assert "Return: x" in output

        finally:
            os.unlink(src_file)
            os.unlink(out_file)

    def test_dot_generation(self, compiler_cli):
        """Тест генерации DOT и конвертации в PNG (если установлен graphviz)."""
        source = "fn main() { return 0; }"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.src', delete=False) as f:
            f.write(source)
            src_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            dot_file = f.name

        try:
            # Генерируем DOT
            result = subprocess.run(
                ['python', str(compiler_cli), 'parse', '--input', src_file,
                 '--format', 'dot', '--output', dot_file],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0

            # Проверяем наличие DOT
            with open(dot_file, 'r') as f:
                dot_content = f.read()

            assert "digraph AST" in dot_content

            # Проверяем, что dot может быть сконвертирован (опционально)
            png_file = dot_file.replace('.dot', '.png')
            try:
                subprocess.run(['dot', '-Tpng', dot_file, '-o', png_file],
                               check=True, capture_output=True)
                assert os.path.exists(png_file)
            except (subprocess.CalledProcessError, FileNotFoundError):
                pytest.skip("Graphviz not installed")

        finally:
            os.unlink(src_file)
            os.unlink(dot_file)
            if os.path.exists(png_file):
                os.unlink(png_file)

    def test_json_output(self, compiler_cli):
        """Тест JSON вывода."""
        source = "fn main() { return 42; }"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.src', delete=False) as f:
            f.write(source)
            src_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_file = f.name

        try:
            result = subprocess.run(
                ['python', str(compiler_cli), 'parse', '--input', src_file,
                 '--format', 'json', '--output', json_file],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0

            # Проверяем валидность JSON
            import json
            with open(json_file, 'r') as f:
                data = json.load(f)

            assert data["node_type"] == "Program"
            assert data["declarations"][0]["name"] == "main"

        finally:
            os.unlink(src_file)
            os.unlink(json_file)

    def test_error_reporting(self, compiler_cli):
        """Тест отчёта об ошибках."""
        source = """
        fn main() {
            int x = 
            return x;
        }
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.src', delete=False) as f:
            f.write(source)
            src_file = f.name

        try:
            result = subprocess.run(
                ['python', str(compiler_cli), 'parse', '--input', src_file, '--verbose'],
                capture_output=True,
                text=True
            )

            # Должен быть ненулевой код возврата
            assert result.returncode != 0

            # Должны быть сообщения об ошибках
            assert "error" in result.stderr.lower() or "Error" in result.stderr

        finally:
            os.unlink(src_file)