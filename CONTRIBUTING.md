# Contributing to Interactive Course TSS

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/interactive-course-tss.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests and linting
6. Commit your changes
7. Push to your fork
8. Create a Pull Request

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip

### Install Dependencies

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8 pre-commit
```

### Install Pre-commit Hooks

```bash
pre-commit install
```

This will automatically run code formatting and linting checks before each commit.

## Code Style

We follow PEP 8 with some modifications:

- Maximum line length: 88 characters (Black default)
- Use Black for automatic code formatting
- Use type hints for function signatures
- Write docstrings for public functions and classes

### Running Black

```bash
black .
```

### Running Flake8

```bash
flake8 . --max-line-length=127
```

## Testing

### Running Tests

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_smoke.py
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files with `test_` prefix
- Name test functions with `test_` prefix
- Use descriptive test names
- Add docstrings to explain what each test does
- Mock external dependencies when appropriate

## Pull Request Guidelines

### Before Submitting

1. Ensure all tests pass: `pytest`
2. Format code: `black .`
3. Check linting: `flake8 .`
4. Update documentation if needed
5. Add tests for new features
6. Update CHANGELOG.md

### PR Description

Include in your PR description:

- **What**: Brief description of changes
- **Why**: Motivation for changes
- **How**: Implementation approach
- **Testing**: How you tested the changes
- **Breaking Changes**: Any backward-incompatible changes

### Commit Messages

Write clear, descriptive commit messages:

```
Add user authentication endpoint

- Implement JWT token generation
- Add password hashing with bcrypt
- Include login and logout endpoints
- Add tests for auth flow
```

## Code Review Process

1. A maintainer will review your PR
2. Address any feedback or requested changes
3. Once approved, a maintainer will merge your PR

## Reporting Issues

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)

### Feature Requests

Include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (if any)

## Questions?

Feel free to open an issue for questions or discussions.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
