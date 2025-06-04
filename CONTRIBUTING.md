# Contributing to FS-MCP

Thank you for your interest in contributing to FS-MCP! This document provides guidelines and information about contributing to this project.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/fs-mcp.git
   cd fs-mcp
   ```
3. **Install dependencies**:
   ```bash
   uv sync --group dev
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🛠️ Development Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Git

### Environment Setup

1. **Copy environment template**:
   ```bash
   cp env.example .env
   ```

2. **Edit `.env`** with your configuration

3. **Install development dependencies**:
   ```bash
   uv sync --group dev
   ```

4. **Run tests** to verify setup:
   ```bash
   pytest
   ```

## 📝 Development Guidelines

### Code Style

- **Follow PEP 8** Python style guidelines
- **Use Black** for code formatting:
  ```bash
  black src/ tests/
  ```
- **Use flake8** for linting:
  ```bash
  flake8 src/ tests/
  ```
- **Use mypy** for type checking:
  ```bash
  mypy src/
  ```

### Code Organization

- **Core logic** goes in `src/` directory
- **Tests** go in `tests/` directory
- **Documentation** updates go in `README.md` or new files in `docs/`

### Commit Messages

Use conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Examples:
- `feat(search): add hybrid search functionality`
- `fix(reader): handle encoding detection errors`
- `docs(readme): update installation instructions`
- `test(indexer): add vector search tests`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_file_reader.py

# Run tests with verbose output
pytest -v

# Run tests for specific function
pytest tests/test_file_reader.py::test_read_file_basic
```

### Writing Tests

- **Write tests** for all new functionality
- **Maintain coverage** above 80%
- **Use descriptive test names** that explain what is being tested
- **Follow AAA pattern**: Arrange, Act, Assert

Example test structure:
```python
def test_read_file_with_line_range():
    # Arrange
    file_reader = UniversalFileReader()
    test_file = "test_file.py"
    
    # Act
    result = file_reader.read_file(test_file, start_line=1, end_line=10)
    
    # Assert
    assert result is not None
    assert len(result.split('\n')) <= 10
```

## 🔧 Types of Contributions

### 🐛 Bug Reports

When filing a bug report, please include:

- **Clear description** of the issue
- **Steps to reproduce** the problem
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Log files** or error messages
- **Minimal code example** if applicable

### ✨ Feature Requests

For feature requests, please include:

- **Use case description** - why is this needed?
- **Proposed solution** - how should it work?
- **Alternative solutions** - what other approaches did you consider?
- **Additional context** - mockups, examples, etc.

### 🔧 Code Contributions

We welcome contributions in these areas:

#### High Priority
- **Performance improvements** for large file processing
- **Enhanced PDF processing** with better table extraction
- **Real-time file monitoring** for auto-indexing
- **Security enhancements** and vulnerability fixes

#### Medium Priority
- **New file format support** (e.g., more document types)
- **Advanced search features** (regex, faceted search)
- **Better error handling** and user feedback
- **Documentation improvements**

#### Nice to Have
- **Web interface** for management
- **Plugin system** for custom handlers
- **Additional embedding models** support
- **Performance monitoring** and metrics

## 📋 Pull Request Process

### Before Submitting

1. **Ensure tests pass**:
   ```bash
   pytest
   ```

2. **Check code quality**:
   ```bash
   black --check src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

3. **Update documentation** if needed

4. **Add tests** for new functionality

### Submitting PR

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create pull request** on GitHub

3. **Fill out PR template** with:
   - Description of changes
   - Type of change (bug fix, feature, etc.)
   - Testing performed
   - Related issues

### PR Review Process

- **Automated checks** must pass (tests, linting, etc.)
- **Code review** by maintainers
- **Changes requested** may need to be addressed
- **Approval and merge** once ready

## 🚀 Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backward-compatible functionality additions
- **PATCH** version for backward-compatible bug fixes

### Release Workflow

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG** with release notes
3. **Create release tag**:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```
4. **GitHub Actions** will handle the rest

## 🏗️ Architecture Guidelines

### Project Structure

```
fs-mcp/
├── src/                    # Core application code
│   ├── __init__.py        # Package initialization
│   ├── file_reader.py     # File reading logic
│   ├── security_validator.py  # Security validation
│   └── ...                # Other modules
├── tests/                 # Test suite
├── docs/                  # Documentation (future)
├── main.py               # Application entry point
└── pyproject.toml        # Project configuration
```

### Design Principles

- **Security First**: All file access must go through security validation
- **Performance**: Optimize for large file processing and caching
- **Extensibility**: Design for easy addition of new file formats
- **Error Handling**: Graceful degradation with informative messages
- **Testability**: Write code that is easy to test

### Adding New Features

When adding new features:

1. **Design first** - consider the API and user experience
2. **Security review** - ensure no security vulnerabilities
3. **Performance impact** - consider memory and processing requirements
4. **Backward compatibility** - avoid breaking existing functionality
5. **Documentation** - update README and add docstrings

## 📞 Getting Help

- **GitHub Issues** - for bug reports and feature requests
- **GitHub Discussions** - for questions and community discussion
- **Code Review** - tag maintainers for review help

## 🙏 Recognition

Contributors will be:
- **Listed in README** acknowledgments
- **Credited in release notes** for significant contributions
- **Invited as collaborator** for sustained contributions

## 📄 License

By contributing to FS-MCP, you agree that your contributions will be licensed under the same MIT License that covers the project. 