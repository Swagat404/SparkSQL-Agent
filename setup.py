"""
Setup script for Spark PostgreSQL Agent

This setup script installs the Spark PostgreSQL Agent package and its dependencies.
"""

import os
from setuptools import setup, find_packages

# Read version from __init__.py
with open("__init__.py", "r") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break
    else:
        version = "0.2.0"

# Read long description from README.md
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

# Define required packages
required_packages = [
    "pyspark>=3.1.0",
    "psycopg2-binary>=2.9.0",
    "openai>=1.0.0",
    "anthropic>=0.5.0",
    "click>=8.0.0",
    "pydantic>=1.8.0,<2.0.0",  # Using Pydantic v1 for compatibility
    "python-dotenv>=0.19.0",
    "rich>=12.0.0",
    "matplotlib>=3.5.0",
    "numpy>=1.20.0",
]

# Define development dependencies
dev_packages = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "isort>=5.0.0",
    "mypy>=1.0.0",
]

# Define entry points for CLI tools
entry_points = {
    "console_scripts": [
        "spark-pg-agent=spark_pg_agent_formal.cli.cli:main",
    ],
}

setup(
    name="spark-pg-agent-formal",
    version=version,
    description="An autonomous agent for natural language transformations on PostgreSQL databases using Apache Spark",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TensorStax",
    author_email="info@tensorstax.com",
    url="https://github.com/tensorstax/spark-pg-agent-formal",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=required_packages,
    extras_require={
        "dev": dev_packages,
    },
    entry_points=entry_points,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
) 