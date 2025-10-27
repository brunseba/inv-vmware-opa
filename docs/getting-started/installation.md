# Installation

## Requirements

- Python 3.10 or higher
- `uv` or `pipx` package manager

## Using pipx (Recommended)

```bash
pipx install inv-vmware-opa
```

## Using uv

```bash
uv pip install inv-vmware-opa
```

## From Source

```bash
# Clone the repository
git clone https://github.com/brun_s/inv-vmware-opa.git
cd inv-vmware-opa

# Install with uv
uv sync

# Verify installation
uv run python -m src.cli --version
```

## Development Installation

For development, install with dev dependencies:

```bash
# Clone repository
git clone https://github.com/brun_s/inv-vmware-opa.git
cd inv-vmware-opa

# Install dependencies
uv sync

# Install pre-commit hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

## Verify Installation

```bash
# Check CLI is available
uv run python -m src.cli --help

# Should display:
# Usage: python -m src.cli [OPTIONS] COMMAND [ARGS]...
#
#   VMware inventory management CLI.
#
# Options:
#   --version  Show the version and exit.
#   --help     Show this message and exit.
#
# Commands:
#   list   List virtual machines from the inventory.
#   load   Load VMware inventory from Excel file into database.
#   stats  Show statistics about the inventory database.
```
