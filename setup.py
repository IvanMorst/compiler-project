#!/usr/bin/env python3
"""
Setup script for MiniCompiler.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="minicompiler",
    version="0.1.0",
    author="Your Team",
    author_email="team@example.com",
    description="A simplified C-like compiler (Sprint 1: Lexical Analysis)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/minicompiler",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Compilers",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "compiler=src.lexer.cli:main",
        ],
    },
    include_package_data=True,
)