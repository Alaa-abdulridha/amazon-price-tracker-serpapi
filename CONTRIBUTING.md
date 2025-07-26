# Contributing to Amazon Price Tracker with SerpApi

Thank you for your interest in contributing to this project! We welcome all contributions that help improve the Amazon Price Tracker.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/amazon-price-tracker-serpapi.git
   cd amazon-price-tracker-serpapi
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🛠️ Development Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your SerpApi key for testing
   ```

3. **Run tests**:
   ```bash
   python -m pytest tests/ -v
   ```

## 📝 Code Guidelines

### Python Style
- Follow [PEP 8](https://pep8.org/) style guidelines
- Use type hints where possible
- Write docstrings for all functions and classes
- Keep line length under 79 characters

### Code Quality
- **Linting**: Run `flake8 amazontracker/` before committing
- **Formatting**: Use `black amazontracker/` for consistent formatting
- **Testing**: Add tests for new features in the `tests/` directory
- **Documentation**: Update README and docstrings as needed

### Testing
- Write unit tests for all new functionality
- Ensure test coverage remains above 85%
- Mock external dependencies (SerpApi, email, etc.)
- Test both success and error scenarios

Example test structure:
```python
def test_your_feature():
    """Test description"""
    # Arrange
    setup_test_data()
    
    # Act
    result = your_function()
    
    # Assert
    assert result == expected_value
```

## 🎯 Types of Contributions

### 🐛 Bug Reports
- Use the issue template
- Include steps to reproduce
- Provide error messages and logs
- Mention your OS and Python version

### ✨ Feature Requests
- Describe the feature and its benefits
- Explain the use case
- Consider backward compatibility
- Discuss implementation approach

### 🔧 Code Contributions
- **Bug fixes**: Reference the issue number
- **New features**: Discuss in an issue first
- **Documentation**: Always welcome!
- **Tests**: Help improve coverage

## 📋 Pull Request Process

1. **Create an issue** first (for features/major changes)
2. **Fork and create a branch** from `main`
3. **Make your changes** with tests
4. **Update documentation** if needed
5. **Run the test suite**:
   ```bash
   python -m pytest tests/ --cov=amazontracker
   flake8 amazontracker/
   black --check amazontracker/
   ```
6. **Submit a pull request** with:
   - Clear description of changes
   - Reference to related issues
   - Screenshots/examples if applicable

### PR Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No sensitive data (API keys, etc.)
- [ ] Commit messages are clear

## 🏗️ Architecture Guidelines

### Project Structure
```
amazontracker/
├── core/          # Core business logic
├── services/      # External service integrations
├── ai/            # Machine learning components
├── web/           # FastAPI web interface
├── database/      # Data models and migrations
├── notifications/ # Alert systems
└── utils/         # Shared utilities
```

### Best Practices
- **Single Responsibility**: Each class/function has one purpose
- **Dependency Injection**: Use dependency injection for testability
- **Error Handling**: Comprehensive error handling with logging
- **Configuration**: Use environment variables for configuration
- **Async/Await**: Use async operations for I/O-bound tasks

## 🔒 Security Guidelines

- **Never commit secrets** (API keys, passwords, etc.)
- **Validate all inputs** to prevent injection attacks
- **Use secure defaults** in configuration
- **Review dependencies** for known vulnerabilities
- **Follow OWASP guidelines** for web security

## 📚 Resources

### SerpApi Integration
- [SerpApi Documentation](https://serpapi.com/search-api)
- [Python SerpApi Client](https://github.com/serpapi/google-search-results-python)

### Development Tools
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## 🤝 Community

- **Be respectful** and inclusive
- **Help others** learn and contribute
- **Share knowledge** through documentation
- **Give constructive feedback** in reviews

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion  
- **Email**: alaa@serpapi.com for direct support
- **Documentation**: Check the docs first
- **Code Comments**: Look for inline documentation

## 🎉 Recognition

Contributors will be:
- Listed in the README contributors section
- Mentioned in release notes
- Invited to join the maintainers team (for regular contributors)

Thank you for contributing to make Amazon price tracking better for everyone! 🚀

---

**Project maintained by [Alaa Abdulridha](https://github.com/Alaa-abdulridha) for [SerpApi, LLC](https://serpapi.com/)**
