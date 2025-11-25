# Conventional Commits Cheat Sheet

## Quick Format
```
<type>(<scope>): <subject>
```

## Common Types

| Type | Usage | Example |
|------|-------|---------|
| `feat` | New feature | `feat(api): add user profile endpoint` |
| `fix` | Bug fix | `fix(auth): resolve login timeout` |
| `docs` | Documentation | `docs: update installation guide` |
| `style` | Code style/formatting | `style: format code with black` |
| `refactor` | Code refactoring | `refactor(parser): simplify JSON handling` |
| `perf` | Performance improvement | `perf(db): optimize query execution` |
| `test` | Add/update tests | `test(api): add integration tests` |
| `chore` | Maintenance tasks | `chore: update dependencies` |
| `ci` | CI/CD changes | `ci: add GitHub Actions workflow` |
| `revert` | Revert previous commit | `revert: undo feature X` |

## Quick Examples

### Feature
```bash
git commit -m "feat: add export to CSV functionality"
git commit -m "feat(inventory): add filtering by date range"
```

### Bug Fix
```bash
git commit -m "fix: resolve null pointer exception"
git commit -m "fix(api): handle empty response gracefully"
```

### Documentation
```bash
git commit -m "docs: add API usage examples"
git commit -m "docs(readme): update installation steps"
```

### Breaking Change
```bash
git commit -m "feat!: change API authentication method

BREAKING CHANGE: API now requires OAuth2 tokens"
```

## Pre-commit Setup
```bash
# One-time setup
pre-commit install
pre-commit install --hook-type commit-msg
```

## Creating a Release
```bash
# Tag and push
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3

# Triggers automatic:
# - Changelog generation
# - Documentation update
# - GitHub release creation
```

## Validation Test
```bash
# Test if your commit message is valid
echo "feat: my feature" | pre-commit run --hook-stage commit-msg conventional-pre-commit
```

## Common Scopes (Project-specific)

- `api`: API endpoints
- `auth`: Authentication/Authorization
- `db`: Database operations
- `parser`: Data parsing
- `inventory`: Inventory management
- `ui`: User interface
- `cli`: Command-line interface
- `config`: Configuration
- `deps`: Dependencies

## Rules to Remember

1. ✅ Lowercase type and description
2. ✅ Imperative mood ("add" not "added")
3. ✅ No period at end
4. ✅ Scope in parentheses (optional)
5. ❌ No capital letter after colon
6. ❌ Don't use past tense

## Multi-line Commits
```bash
git commit -m "feat(api): add new endpoint" -m "
This endpoint allows users to fetch inventory data
with advanced filtering options.

Closes #123"
```

## Useful Aliases
Add to your `~/.gitconfig`:
```ini
[alias]
    feat = "!f() { git commit -m \"feat: $*\"; }; f"
    fix = "!f() { git commit -m \"fix: $*\"; }; f"
    docs = "!f() { git commit -m \"docs: $*\"; }; f"
    chore = "!f() { git commit -m \"chore: $*\"; }; f"
```

Then use:
```bash
git feat add new dashboard
git fix resolve memory leak
```
