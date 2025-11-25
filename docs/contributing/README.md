# Contributing Guide

Welcome to the contributing guide! This section contains everything you need to know about contributing to this project.

## Documentation

- **[Conventional Commits Guide](conventional-commits.md)** - Complete guide to using conventional commits in this project
- **[Commit Cheat Sheet](commit-cheatsheet.md)** - Quick reference for commit formats

## Quick Start

### 1. Setup Pre-commit Hooks

Pre-commit hooks ensure your commits follow the project standards:

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install the git hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

### 2. Make Your Changes

Follow the project coding standards and make your changes.

### 3. Write Conventional Commits

Use the conventional commit format for all commits:

```bash
# Format: <type>(<scope>): <description>
git commit -m "feat: add new inventory filter"
git commit -m "fix(api): resolve timeout issue"
git commit -m "docs: update installation guide"
```

See the [Commit Cheat Sheet](commit-cheatsheet.md) for quick examples.

### 4. Test Your Changes

Ensure all tests pass before submitting:

```bash
# Run tests
pytest

# Run linting
pre-commit run --all-files
```

## Commit Types

| Type | When to Use |
|------|-------------|
| `feat` | Adding a new feature |
| `fix` | Fixing a bug |
| `docs` | Documentation changes only |
| `style` | Code formatting (no logic change) |
| `refactor` | Code restructuring (no feature/fix) |
| `perf` | Performance improvements |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks, dependencies |
| `ci` | CI/CD changes |

## Automated Processes

### Changelog Generation

When you create a new version tag, the following happens automatically via GitHub Actions:

1. **Changelog Generation** - `CHANGELOG.md` is updated with all commits since the last tag
2. **Documentation Update** - Version number is updated in `mkdocs.yml` and `docs/index.md`
3. **GitHub Release** - A release is created with the changelog as the description

To create a release:

```bash
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3
```

### Pre-commit Validation

Every commit is automatically validated for:

- ✅ Conventional commit format
- ✅ Code formatting (Black)
- ✅ Code quality (Flake8)
- ✅ Security issues (Bandit)
- ✅ YAML syntax
- ✅ No secrets in code

## Need Help?

- See the [Conventional Commits Guide](conventional-commits.md) for detailed examples
- Check the [Commit Cheat Sheet](commit-cheatsheet.md) for quick reference
- Ask questions in pull request discussions

## Resources

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
