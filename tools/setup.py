"""Setup configuration for screenshot-cli tool."""

from setuptools import setup, find_packages
from pathlib import Path

# Read requirements
requirements = Path("requirements-screenshots.txt").read_text().strip().split("\n")

setup(
    name="screenshot-cli",
    version="0.7.0",
    description="Screenshot automation tool for VMware Inventory Dashboard",
    author="Sebastien Brun",
    author_email="brun_s@example.com",
    py_modules=["screenshot_cli", "screenshot_dashboard"],
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "screenshot-cli=screenshot_cli:cli",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
