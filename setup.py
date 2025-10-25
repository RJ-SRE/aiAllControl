"""
MacMind 安装配置文件
"""

from setuptools import setup, find_packages

setup(
    name="macmind",
    version="0.1.0",
    description="AI 驱动的自学习电脑操作管家",
    author="RJ-SRE",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "anthropic>=0.40.0",
        "openai>=1.50.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=6.0.0",
            "pytest-mock>=3.14.0",
            "black>=24.0.0",
            "flake8>=7.0.0",
            "mypy>=1.13.0",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
