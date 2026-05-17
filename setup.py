from setuptools import setup, find_packages

setup(
    name="minicompiler",
    version="0.4.0",
    packages=find_packages(include=['src', 'src.*']),
    install_requires=[],
    extras_require={
        'dev': ['pytest>=6.0', 'pytest-cov'],
    },
    entry_points={
        'console_scripts': [
            'compiler=src.main:main',
        ],
    },
    python_requires='>=3.9',
)