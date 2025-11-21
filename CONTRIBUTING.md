# Contributing to Azure Reporting Tool

Thank you for your interest in contributing to the Azure Reporting Tool! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful and inclusive. We're all here to build something useful together.

## How to Contribute

### Reporting Issues

1. Check if the issue already exists
2. Use the issue template if available
3. Provide detailed information:
   - Python version
   - Operating system
   - Error messages and logs
   - Steps to reproduce

### Suggesting Enhancements

1. Open an issue with the "enhancement" label
2. Describe the feature and its benefits
3. Provide examples of how it would work

### Contributing Code

1. **Fork the repository**

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add docstrings to functions and classes
   - Keep functions focused and small
   - Add comments for complex logic

4. **Test your changes**
   - Ensure existing functionality still works
   - Test with real Azure resources if possible
   - Verify the generated reports

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: brief description of changes"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request**
   - Describe what changes you made and why
   - Reference any related issues
   - Wait for review and address feedback

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/azureReportingTool.git
cd azureReportingTool

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Install development dependencies (if added)
pip install -r requirements-dev.txt
```

## Code Style Guidelines

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add type hints where appropriate
- Keep lines under 100 characters when reasonable
- Use docstrings for all public functions and classes

### Example Function

```python
def analyze_resource(resource_data: Dict[str, Any], 
                     best_practices: List[str]) -> Dict[str, Any]:
    """Analyze a resource against best practices.
    
    Args:
        resource_data: Dictionary containing resource information
        best_practices: List of best practices to check against
        
    Returns:
        Dictionary with analysis results including findings and score
        
    Raises:
        ValueError: If resource_data is empty or invalid
    """
    if not resource_data:
        raise ValueError("Resource data cannot be empty")
    
    # Implementation here
    pass
```

## Project Structure

```
src/azure_reporter/
├── main.py              # Main orchestration
├── modules/             # Core functionality modules
│   ├── azure_fetcher.py
│   ├── ai_analyzer.py
│   ├── powerpoint_generator.py
│   └── backlog_generator.py
└── utils/               # Utility functions
    ├── config_loader.py
    └── logger.py
```

## Adding New Features

### Adding a New Azure Resource Type

1. Update `azure_fetcher.py`:
   - Add a new `fetch_X()` method
   - Include the new resource in `fetch_all_resources()`

2. Update `ai_analyzer.py`:
   - Add an `analyze_X()` method
   - Include in `analyze_all_resources()`

3. Update `powerpoint_generator.py`:
   - Add slides for the new resource type

4. Update `backlog_generator.py`:
   - Ensure it handles the new resource findings

5. Update configuration:
   - Add option in `config.example.yaml`
   - Update `config_loader.py` if needed

### Adding New Export Formats

1. Create a new generator module in `modules/`
2. Implement the export logic
3. Integrate it into `main.py`
4. Update configuration and documentation

## Testing

Currently, the project uses manual testing. When adding features:

1. Test with a real Azure subscription
2. Verify all output formats generate correctly
3. Check that AI analysis produces reasonable results
4. Ensure no regressions in existing functionality

## Documentation

- Update README.md for significant changes
- Update QUICKSTART.md if setup changes
- Add inline comments for complex logic
- Update docstrings when changing function signatures

## Pull Request Process

1. Ensure your code follows the style guidelines
2. Update documentation as needed
3. Test thoroughly
4. Ensure your branch is up to date with main:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```
5. Submit the PR with a clear description

## Questions?

Open an issue with the "question" label if you need help or clarification.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
