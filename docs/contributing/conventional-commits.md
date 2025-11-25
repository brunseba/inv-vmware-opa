# Conventional Commits Guide

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages.

## Why Conventional Commits?

- Automatically generate CHANGELOGs
- Automatically determine semantic version bumps
- Communicate the nature of changes to teammates and stakeholders
- Trigger build and publish processes
- Make it easier for people to contribute by allowing them to explore a more structured commit history

## Commit Message Format

Each commit message consists of a **header**, an optional **body**, and an optional **footer**:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Type

Must be one of the following:

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **chore**: Changes to the build process or auxiliary tools and libraries such as documentation generation
- **ci**: Changes to CI configuration files and scripts
- **revert**: Reverts a previous commit

### Scope (Optional)

A scope provides additional contextual information and is contained within parentheses:

```
feat(api): add endpoint for user profile
fix(auth): resolve token expiration issue
docs(readme): update installation instructions
```

### Description

A short summary of the code changes:

- Use the imperative, present tense: "change" not "changed" nor "changes"
- Don't capitalize the first letter
- No period (.) at the end

### Body (Optional)

Provide additional context about the code changes. Use the body to explain:

- What was the motivation for the change?
- How does it differ from the previous implementation?

### Footer (Optional)

The footer should contain:

- **Breaking Changes**: Start with `BREAKING CHANGE:` followed by a description
- **Issue References**: e.g., `Closes #123`, `Fixes #456`

## Examples

### Simple feature commit
```
feat: add user authentication
```

### Feature with scope
```
feat(api): implement REST endpoint for inventory
```

### Bug fix with issue reference
```
fix(parser): handle null values in JSON response

Closes #42
```

### Breaking change
```
feat(api): change authentication method

BREAKING CHANGE: JWT tokens now require expiration field.
All existing tokens will be invalidated.
```

### Documentation update
```
docs: update API documentation with examples
```

### Refactor with detailed body
```
refactor(database): optimize query performance

Replaced multiple database calls with a single batch query.
This reduces latency by approximately 40%.
```

## Pre-commit Validation

This repository uses `pre-commit` hooks to validate commit messages. The conventional commit format is automatically checked before each commit.

### Setup Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

### Testing Your Commit Message

You can test your commit message format without making a commit:

```bash
echo "feat: my new feature" | pre-commit run --hook-stage commit-msg conventional-pre-commit
```

## Automatic Changelog Generation

When you create a new tag (e.g., `v1.0.0`), the following happens automatically:

1. **Changelog Generation**: A new CHANGELOG.md is generated based on all conventional commits
2. **Documentation Update**: The version is updated in `mkdocs.yml` and `docs/index.md`
3. **GitHub Release**: A GitHub release is created with the changelog

### Creating a Release

```bash
# Create and push a tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Best Practices

1. **Keep commits atomic**: Each commit should represent a single logical change
2. **Write clear descriptions**: Future you (and your teammates) will thank you
3. **Use scopes consistently**: Establish common scopes for your project
4. **Reference issues**: Link commits to issues when applicable
5. **Break down large changes**: Use multiple commits to tell the story of your changes

## Common Mistakes to Avoid

❌ **Bad**: `updated stuff`
✅ **Good**: `fix(api): resolve timeout issue in data fetching`

❌ **Bad**: `Fixed bug.`
✅ **Good**: `fix: resolve memory leak in background worker`

❌ **Bad**: `FEAT: NEW FEATURE`
✅ **Good**: `feat: add export functionality`

❌ **Bad**: `feat: Added new feature.`
✅ **Good**: `feat: add new feature`

## Tools & Resources

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [git-cliff](https://git-cliff.org/) - Changelog generator
- [conventional-pre-commit](https://github.com/compilerla/conventional-pre-commit) - Pre-commit hook
- [commitizen](https://commitizen-tools.github.io/commitizen/) - Interactive commit helper

## Getting Help

If you're unsure about how to format a commit message, feel free to ask in pull request reviews or discussions.
