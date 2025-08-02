#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for FastCentrik to WooCommerce transformer
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="fastcentrik-woocommerce",
    version="2.0.0",
    author="FastCentrik Migration Tool",
    author_email="",
    description="Nástroj pro převod dat z FastCentrik exportu do formátu kompatibilního s WooCommerce",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/fastcentrik-to-woocommerce",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "fastcentrik-transform=fastcentrik_woocommerce.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "fastcentrik_woocommerce": ["*.json", "*.yaml", "*.yml"],
    },
)