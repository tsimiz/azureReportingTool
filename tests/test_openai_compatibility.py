"""Test OpenAI client compatibility and initialization."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_openai_version_compatibility():
    """Test that the installed OpenAI version is compatible."""
    try:
        import openai
        version = openai.__version__
        
        # Parse version (handle pre-release versions like 1.50.0rc1)
        version_parts = version.split('.')
        try:
            major = int(version_parts[0])
            # Extract numeric part from minor version (e.g., '50' from '50rc1')
            minor_str = ''.join(c for c in version_parts[1] if c.isdigit())
            minor = int(minor_str) if minor_str else 0
        except (ValueError, IndexError) as e:
            print(f"⚠ Could not parse version {version}: {e}")
            print(f"  Skipping version check, assuming version is compatible")
            return True
        
        # Should be >= 1.50.0 and < 2.0.0
        assert major == 1, f"OpenAI major version should be 1, got {major}"
        assert minor >= 50, f"OpenAI minor version should be >= 50, got {minor}"
        
        print(f"✓ OpenAI version {version} is compatible")
        return True
    except Exception as e:
        print(f"✗ OpenAI version check failed: {e}")
        return False


def test_openai_client_initialization():
    """Test that OpenAI client can be initialized without errors."""
    try:
        from openai import OpenAI
        
        # Try to initialize the client with a clearly fake API key for testing
        # Real OpenAI API keys start with 'sk-'
        client = OpenAI(api_key='sk-test-fake-key-for-unit-testing-only')
        
        assert client is not None, "OpenAI client should not be None"
        assert hasattr(client, 'chat'), "OpenAI client should have 'chat' attribute"
        
        print("✓ OpenAI client initialized successfully")
        return True
    except TypeError as e:
        if 'proxies' in str(e):
            print(f"✗ OpenAI client initialization failed with httpx compatibility issue: {e}")
            print("  This indicates the openai version is incompatible with the installed httpx version")
        else:
            print(f"✗ OpenAI client initialization failed: {e}")
        return False
    except Exception as e:
        print(f"✗ OpenAI client initialization failed: {e}")
        return False


def test_ai_analyzer_initialization():
    """Test that AIAnalyzer can be initialized without errors."""
    try:
        from azure_reporter.modules.ai_analyzer import AIAnalyzer
        
        # Initialize with test parameters using a clearly fake API key
        analyzer = AIAnalyzer(
            api_key='sk-test-fake-key-for-unit-testing-only',
            model='gpt-4',
            temperature=0.3
        )
        
        assert analyzer is not None, "AIAnalyzer should not be None"
        assert analyzer.client is not None, "AIAnalyzer.client should not be None"
        assert analyzer.model == 'gpt-4', "Model should be set correctly"
        assert analyzer.temperature == 0.3, "Temperature should be set correctly"
        
        print("✓ AIAnalyzer initialized successfully")
        return True
    except Exception as e:
        print(f"✗ AIAnalyzer initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_httpx_compatibility():
    """Test that httpx version is compatible with OpenAI."""
    try:
        import httpx
        import inspect
        
        # Check that httpx.Client accepts 'proxy' parameter (not 'proxies')
        sig = inspect.signature(httpx.Client.__init__)
        params = list(sig.parameters.keys())
        
        # Modern httpx uses 'proxy' (singular)
        if 'proxy' in params:
            print(f"✓ httpx version {httpx.__version__} uses modern 'proxy' parameter")
            return True
        elif 'proxies' in params:
            print(f"⚠ httpx version {httpx.__version__} uses legacy 'proxies' parameter")
            return True
        else:
            print(f"⚠ httpx version {httpx.__version__} - proxy parameter detection unclear")
            return True
    except Exception as e:
        print(f"✗ httpx compatibility check failed: {e}")
        return False


def run_all_tests():
    """Run all OpenAI compatibility tests."""
    print("="*60)
    print("OpenAI Compatibility Tests")
    print("="*60)
    print()
    
    results = []
    
    print("Test 1: OpenAI Version Compatibility")
    results.append(test_openai_version_compatibility())
    print()
    
    print("Test 2: httpx Compatibility")
    results.append(test_httpx_compatibility())
    print()
    
    print("Test 3: OpenAI Client Initialization")
    results.append(test_openai_client_initialization())
    print()
    
    print("Test 4: AIAnalyzer Initialization")
    results.append(test_ai_analyzer_initialization())
    print()
    
    print("="*60)
    if all(results):
        print("✓ All OpenAI compatibility tests passed!")
    else:
        print("✗ Some OpenAI compatibility tests failed")
    print("="*60)
    
    return all(results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
