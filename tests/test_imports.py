"""Basic tests to verify package structure and imports."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_package_import():
    """Test that the main package can be imported."""
    try:
        import azure_reporter
        # Check version exists and is a string
        assert hasattr(azure_reporter, '__version__')
        assert isinstance(azure_reporter.__version__, str)
        print(f"✓ Package import successful (version: {azure_reporter.__version__})")
        return True
    except Exception as e:
        print(f"✗ Package import failed: {e}")
        return False


def test_module_imports():
    """Test that all modules can be imported."""
    modules = [
        'azure_reporter.modules.azure_fetcher',
        'azure_reporter.modules.ai_analyzer',
        'azure_reporter.modules.powerpoint_generator',
        'azure_reporter.modules.pdf_generator',
        'azure_reporter.modules.backlog_generator',
        'azure_reporter.utils.config_loader',
        'azure_reporter.utils.logger',
        'azure_reporter.main',
        'azure_reporter.web_app'
    ]
    
    all_success = True
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except Exception as e:
            print(f"✗ {module_name}: {e}")
            all_success = False
    
    return all_success


def test_class_instantiation():
    """Test that key classes can be instantiated (without credentials)."""
    from azure_reporter.modules.powerpoint_generator import PowerPointGenerator
    from azure_reporter.modules.pdf_generator import PDFGenerator
    from azure_reporter.modules.backlog_generator import BacklogGenerator
    from azure_reporter.utils.logger import setup_logger
    
    try:
        # Test PowerPoint generator
        ppt_gen = PowerPointGenerator()
        assert ppt_gen is not None
        print("✓ PowerPointGenerator instantiation")
        
        # Test PDF generator
        pdf_gen = PDFGenerator()
        assert pdf_gen is not None
        print("✓ PDFGenerator instantiation")
        
        # Test Backlog generator
        backlog_gen = BacklogGenerator()
        assert backlog_gen is not None
        print("✓ BacklogGenerator instantiation")
        
        # Test logger setup
        logger = setup_logger('test')
        assert logger is not None
        print("✓ Logger setup")
        
        return True
    except Exception as e:
        print(f"✗ Class instantiation failed: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("Running Azure Reporting Tool Tests")
    print("="*60)
    print()
    
    results = []
    
    print("Test 1: Package Import")
    results.append(test_package_import())
    print()
    
    print("Test 2: Module Imports")
    results.append(test_module_imports())
    print()
    
    print("Test 3: Class Instantiation")
    results.append(test_class_instantiation())
    print()
    
    print("="*60)
    if all(results):
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("="*60)
    
    return all(results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
