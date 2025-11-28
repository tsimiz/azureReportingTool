"""Tests to verify project structure and file organization."""

import os
import sys


def test_project_structure():
    """Test that all required files and directories exist."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    required_files = [
        'README.md',
        'LICENSE',
        'requirements.txt',
        'setup.py',
        '.gitignore',
        '.env.example',
        'config.example.yaml',
        'QUICKSTART.md',
        'CONTRIBUTING.md',
        'example_usage.py'
    ]
    
    required_dirs = [
        'src',
        'src/azure_reporter',
        'src/azure_reporter/modules',
        'src/azure_reporter/utils',
        'output',
        'tests'
    ]
    
    required_python_files = [
        'src/azure_reporter/__init__.py',
        'src/azure_reporter/main.py',
        'src/azure_reporter/modules/__init__.py',
        'src/azure_reporter/modules/azure_fetcher.py',
        'src/azure_reporter/modules/ai_analyzer.py',
        'src/azure_reporter/modules/powerpoint_generator.py',
        'src/azure_reporter/modules/pdf_generator.py',
        'src/azure_reporter/modules/backlog_generator.py',
        'src/azure_reporter/utils/__init__.py',
        'src/azure_reporter/utils/config_loader.py',
        'src/azure_reporter/utils/logger.py'
    ]
    
    print("Checking project structure...")
    print()
    
    all_exist = True
    
    # Check files
    print("Required files:")
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        exists = os.path.isfile(full_path)
        symbol = "✓" if exists else "✗"
        print(f"  {symbol} {file_path}")
        all_exist = all_exist and exists
    
    print()
    
    # Check directories
    print("Required directories:")
    for dir_path in required_dirs:
        full_path = os.path.join(base_dir, dir_path)
        exists = os.path.isdir(full_path)
        symbol = "✓" if exists else "✗"
        print(f"  {symbol} {dir_path}")
        all_exist = all_exist and exists
    
    print()
    
    # Check Python files
    print("Required Python files:")
    for file_path in required_python_files:
        full_path = os.path.join(base_dir, file_path)
        exists = os.path.isfile(full_path)
        symbol = "✓" if exists else "✗"
        print(f"  {symbol} {file_path}")
        all_exist = all_exist and exists
    
    return all_exist


def test_dependencies_defined():
    """Test that dependencies are properly defined."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    requirements_path = os.path.join(base_dir, 'requirements.txt')
    
    print("Checking dependencies...")
    print()
    
    required_packages = [
        'azure-identity',
        'azure-mgmt-resource',
        'azure-mgmt-compute',
        'azure-mgmt-network',
        'azure-mgmt-storage',
        'openai',
        'python-pptx',
        'fpdf2',
        'python-dotenv',
        'pyyaml',
        'pandas'
    ]
    
    try:
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        all_found = True
        for package in required_packages:
            found = package in content
            symbol = "✓" if found else "✗"
            print(f"  {symbol} {package}")
            all_found = all_found and found
        
        return all_found
    except Exception as e:
        print(f"✗ Error reading requirements.txt: {e}")
        return False


def test_documentation_exists():
    """Test that documentation files exist and have content."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    docs = {
        'README.md': 5000,  # Should have at least 5000 characters
        'QUICKSTART.md': 2000,
        'CONTRIBUTING.md': 3000
    }
    
    print("Checking documentation...")
    print()
    
    all_good = True
    for doc, min_size in docs.items():
        path = os.path.join(base_dir, doc)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            if size >= min_size:
                print(f"  ✓ {doc} ({size} bytes)")
            else:
                print(f"  ✗ {doc} ({size} bytes, expected at least {min_size})")
                all_good = False
        else:
            print(f"  ✗ {doc} (not found)")
            all_good = False
    
    return all_good


def test_python_syntax():
    """Test that all Python files have valid syntax."""
    import ast
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    src_dir = os.path.join(base_dir, 'src')
    
    print("Checking Python syntax...")
    print()
    
    all_valid = True
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, base_dir)
                
                try:
                    with open(file_path, 'r') as f:
                        ast.parse(f.read())
                    print(f"  ✓ {relative_path}")
                except SyntaxError as e:
                    print(f"  ✗ {relative_path}: {e}")
                    all_valid = False
    
    return all_valid


def run_all_tests():
    """Run all structure tests."""
    print("="*60)
    print("Azure Reporting Tool - Structure Tests")
    print("="*60)
    print()
    
    results = []
    
    print("Test 1: Project Structure")
    print("-" * 60)
    results.append(test_project_structure())
    print()
    
    print("Test 2: Dependencies Defined")
    print("-" * 60)
    results.append(test_dependencies_defined())
    print()
    
    print("Test 3: Documentation Exists")
    print("-" * 60)
    results.append(test_documentation_exists())
    print()
    
    print("Test 4: Python Syntax")
    print("-" * 60)
    results.append(test_python_syntax())
    print()
    
    print("="*60)
    if all(results):
        print("✓ All structure tests passed!")
        print("="*60)
        return True
    else:
        print("✗ Some structure tests failed")
        print("="*60)
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
