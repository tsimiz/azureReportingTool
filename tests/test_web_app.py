"""Tests for the web GUI application."""

import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_web_app_import():
    """Test that web_app module can be imported."""
    try:
        from azure_reporter import web_app
        assert hasattr(web_app, 'app')
        assert hasattr(web_app, 'main')
        print("✓ web_app module imports successfully")
        return True
    except Exception as e:
        print(f"✗ web_app import failed: {e}")
        return False


def test_flask_app_creation():
    """Test that Flask app is created correctly."""
    try:
        from azure_reporter.web_app import app
        assert app is not None
        assert app.name == 'azure_reporter.web_app'
        print("✓ Flask app created successfully")
        return True
    except Exception as e:
        print(f"✗ Flask app creation failed: {e}")
        return False


def test_routes_exist():
    """Test that all expected routes exist."""
    try:
        from azure_reporter.web_app import app
        
        # Get list of registered rules
        rules = {rule.rule for rule in app.url_map.iter_rules()}
        
        expected_routes = [
            '/',
            '/api/login-status',
            '/api/subscriptions',
            '/api/set-subscription',
            '/api/run-analysis',
            '/api/download/<format>'
        ]
        
        all_found = True
        for route in expected_routes:
            found = route in rules
            symbol = "✓" if found else "✗"
            print(f"  {symbol} Route: {route}")
            all_found = all_found and found
        
        return all_found
    except Exception as e:
        print(f"✗ Route check failed: {e}")
        return False


def test_index_page():
    """Test that the index page renders correctly."""
    try:
        from azure_reporter.web_app import app
        
        with app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            # Check that the HTML contains expected elements
            html = response.data.decode('utf-8')
            
            checks = [
                ('Azure Reporting Tool' in html, 'Title'),
                ('subscriptionSelect' in html, 'Subscription selector'),
                ('runAnalysisBtn' in html, 'Run analysis button'),
                ('azure-blue' in html, 'Azure styling'),
                ('Login' in html or 'login' in html, 'Login status section')
            ]
            
            all_passed = True
            for check, name in checks:
                symbol = "✓" if check else "✗"
                print(f"  {symbol} {name}")
                all_passed = all_passed and check
            
            return all_passed
    except Exception as e:
        print(f"✗ Index page test failed: {e}")
        return False


def test_login_status_api():
    """Test the login status API endpoint."""
    try:
        from azure_reporter.web_app import app
        
        with patch('azure_reporter.web_app.get_azure_login_status') as mock_status:
            # Test when logged in
            mock_status.return_value = {
                'logged_in': True,
                'user': 'test@example.com',
                'tenant': 'test-tenant',
                'subscription_id': 'test-sub-id',
                'subscription_name': 'Test Subscription'
            }
            
            with app.test_client() as client:
                response = client.get('/api/login-status')
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['logged_in'] == True
                assert data['user'] == 'test@example.com'
                print("✓ Login status API works when logged in")
            
            # Test when logged out
            mock_status.return_value = {'logged_in': False}
            
            with app.test_client() as client:
                response = client.get('/api/login-status')
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['logged_in'] == False
                print("✓ Login status API works when logged out")
            
            return True
    except Exception as e:
        print(f"✗ Login status API test failed: {e}")
        return False


def test_subscriptions_api():
    """Test the subscriptions API endpoint."""
    try:
        from azure_reporter.web_app import app
        
        with patch('azure_reporter.web_app.get_subscriptions') as mock_subs:
            mock_subs.return_value = [
                {'id': 'sub-1', 'name': 'Subscription 1', 'is_default': True},
                {'id': 'sub-2', 'name': 'Subscription 2', 'is_default': False}
            ]
            
            with app.test_client() as client:
                response = client.get('/api/subscriptions')
                assert response.status_code == 200
                data = json.loads(response.data)
                assert len(data) == 2
                assert data[0]['name'] == 'Subscription 1'
                print("✓ Subscriptions API works correctly")
            
            return True
    except Exception as e:
        print(f"✗ Subscriptions API test failed: {e}")
        return False


def test_set_subscription_api():
    """Test the set subscription API endpoint."""
    try:
        from azure_reporter.web_app import app
        
        with patch('azure_reporter.web_app.set_subscription') as mock_set:
            mock_set.return_value = True
            
            with app.test_client() as client:
                response = client.post(
                    '/api/set-subscription',
                    json={'subscription_id': 'test-sub-id'},
                    content_type='application/json'
                )
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] == True
                print("✓ Set subscription API works correctly")
            
            return True
    except Exception as e:
        print(f"✗ Set subscription API test failed: {e}")
        return False


def test_helper_functions():
    """Test helper functions."""
    try:
        from azure_reporter.web_app import get_azure_login_status, get_subscriptions, set_subscription
        
        # These functions use subprocess, so we test with mocking
        with patch('subprocess.run') as mock_run:
            # Test get_azure_login_status with failed command
            mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='Not logged in')
            result = get_azure_login_status()
            assert result['logged_in'] == False
            print("✓ get_azure_login_status handles non-logged-in state")
            
            # Test get_subscriptions with empty response
            mock_run.return_value = MagicMock(returncode=0, stdout='[]')
            result = get_subscriptions()
            assert result == []
            print("✓ get_subscriptions handles empty subscription list")
            
            # Test set_subscription
            mock_run.return_value = MagicMock(returncode=0)
            result = set_subscription('test-sub-id')
            assert result == True
            print("✓ set_subscription returns success on valid input")
        
        return True
    except Exception as e:
        print(f"✗ Helper functions test failed: {e}")
        return False


def test_ensure_file_extension():
    """Test the ensure_file_extension helper function."""
    try:
        from azure_reporter.web_app import ensure_file_extension
        
        # Test adding extension when missing
        assert ensure_file_extension('report', '.pdf') == 'report.pdf'
        print("✓ Adds extension when missing")
        
        # Test keeping existing correct extension
        assert ensure_file_extension('report.pdf', '.pdf') == 'report.pdf'
        print("✓ Keeps existing correct extension")
        
        # Test replacing incorrect extension
        assert ensure_file_extension('report.pptx', '.pdf') == 'report.pdf'
        print("✓ Replaces incorrect extension")
        
        # Test without leading dot in extension
        assert ensure_file_extension('report', 'pdf') == 'report.pdf'
        print("✓ Works without leading dot in extension")
        
        # Test complex filename
        assert ensure_file_extension('my.report.name', '.pptx') == 'my.report.pptx'
        print("✓ Handles complex filenames with dots")
        
        return True
    except Exception as e:
        print(f"✗ ensure_file_extension test failed: {e}")
        return False


def test_env_vars_routes_exist():
    """Test that environment variables API routes exist."""
    try:
        from azure_reporter.web_app import app
        
        # Get list of registered rules
        rules = {rule.rule for rule in app.url_map.iter_rules()}
        
        expected_routes = [
            '/api/env-vars'
        ]
        
        all_found = True
        for route in expected_routes:
            found = route in rules
            symbol = "✓" if found else "✗"
            print(f"  {symbol} Route: {route}")
            all_found = all_found and found
        
        return all_found
    except Exception as e:
        print(f"✗ Environment variables route check failed: {e}")
        return False


def test_env_vars_api():
    """Test the environment variables API endpoints."""
    try:
        from azure_reporter.web_app import app, current_state
        
        with app.test_client() as client:
            # Test GET endpoint - should return empty/masked values initially
            response = client.get('/api/env-vars')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'openai_api_key' in data
            assert 'openai_model' in data
            assert 'azure_openai_endpoint' in data
            print("✓ GET /api/env-vars returns expected fields")
            
            # Test POST endpoint - setting environment variables
            response = client.post(
                '/api/env-vars',
                json={
                    'openai_api_key': 'sk-test-key-12345',
                    'openai_model': 'gpt-4',
                    'azure_openai_endpoint': 'https://test.openai.azure.com/',
                    'azure_openai_key': 'azure-test-key-12345',
                    'azure_openai_deployment': 'test-deployment'
                },
                content_type='application/json'
            )
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
            print("✓ POST /api/env-vars saves environment variables")
            
            # Verify values were stored in current_state
            assert current_state['env_vars'].get('openai_api_key') == 'sk-test-key-12345'
            assert current_state['env_vars'].get('openai_model') == 'gpt-4'
            print("✓ Environment variables stored in session state")
            
            # Test that masked values are not overwritten
            response = client.post(
                '/api/env-vars',
                json={
                    'openai_api_key': '***masked***',  # Should be ignored
                    'openai_model': 'gpt-3.5-turbo'  # Should be updated
                },
                content_type='application/json'
            )
            assert response.status_code == 200
            assert current_state['env_vars'].get('openai_api_key') == 'sk-test-key-12345'  # Unchanged
            assert current_state['env_vars'].get('openai_model') == 'gpt-3.5-turbo'  # Updated
            print("✓ Masked values are not overwritten")
            
            # Clean up
            current_state['env_vars'] = {}
            
            return True
    except Exception as e:
        print(f"✗ Environment variables API test failed: {e}")
        return False


def test_mask_secret_function():
    """Test the secret masking helper function."""
    try:
        from azure_reporter.web_app import _mask_secret
        
        # Test empty string
        assert _mask_secret('') == ''
        print("✓ Empty string returns empty")
        
        # Test short secret
        assert _mask_secret('short') == '***'
        print("✓ Short secrets are fully masked")
        
        # Test normal secret
        result = _mask_secret('sk-testkey12345678')
        assert result.startswith('sk-t')
        assert result.endswith('5678')
        assert '***' in result
        print("✓ Normal secrets show first and last 4 characters")
        
        return True
    except Exception as e:
        print(f"✗ _mask_secret test failed: {e}")
        return False


def test_index_page_has_env_vars_section():
    """Test that the index page includes environment variables section."""
    try:
        from azure_reporter.web_app import app
        
        with app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            html = response.data.decode('utf-8')
            
            checks = [
                ('Environment Variables' in html, 'Environment Variables section header'),
                ('openaiApiKey' in html, 'OpenAI API Key input field'),
                ('azureOpenaiEndpoint' in html, 'Azure OpenAI Endpoint input field'),
                ('saveEnvVars' in html, 'Save Environment Variables function'),
            ]
            
            all_passed = True
            for check, name in checks:
                symbol = "✓" if check else "✗"
                print(f"  {symbol} {name}")
                all_passed = all_passed and check
            
            return all_passed
    except Exception as e:
        print(f"✗ Index page environment variables section test failed: {e}")
        return False


def test_index_page_has_backlog_section():
    """Test that the index page includes backlog section."""
    try:
        from azure_reporter.web_app import app
        
        with app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            html = response.data.decode('utf-8')
            
            checks = [
                ('Improvement Backlog' in html, 'Improvement Backlog section header'),
                ('backlogCard' in html, 'Backlog card container'),
                ('backlogTable' in html, 'Backlog table'),
                ('backlogSeverityFilter' in html, 'Severity filter'),
                ('backlogCategoryFilter' in html, 'Category filter'),
                ('filterBacklog' in html, 'Filter backlog function'),
            ]
            
            all_passed = True
            for check, name in checks:
                symbol = "✓" if check else "✗"
                print(f"  {symbol} {name}")
                all_passed = all_passed and check
            
            return all_passed
    except Exception as e:
        print(f"✗ Index page backlog section test failed: {e}")
        return False


def run_all_tests():
    """Run all web app tests."""
    print("="*60)
    print("Azure Reporting Tool - Web App Tests")
    print("="*60)
    print()
    
    results = []
    
    print("Test 1: Web App Import")
    print("-" * 60)
    results.append(test_web_app_import())
    print()
    
    print("Test 2: Flask App Creation")
    print("-" * 60)
    results.append(test_flask_app_creation())
    print()
    
    print("Test 3: Routes Exist")
    print("-" * 60)
    results.append(test_routes_exist())
    print()
    
    print("Test 4: Index Page")
    print("-" * 60)
    results.append(test_index_page())
    print()
    
    print("Test 5: Login Status API")
    print("-" * 60)
    results.append(test_login_status_api())
    print()
    
    print("Test 6: Subscriptions API")
    print("-" * 60)
    results.append(test_subscriptions_api())
    print()
    
    print("Test 7: Set Subscription API")
    print("-" * 60)
    results.append(test_set_subscription_api())
    print()
    
    print("Test 8: Helper Functions")
    print("-" * 60)
    results.append(test_helper_functions())
    print()
    
    print("Test 9: ensure_file_extension Helper")
    print("-" * 60)
    results.append(test_ensure_file_extension())
    print()
    
    print("Test 10: Environment Variables Routes")
    print("-" * 60)
    results.append(test_env_vars_routes_exist())
    print()
    
    print("Test 11: Environment Variables API")
    print("-" * 60)
    results.append(test_env_vars_api())
    print()
    
    print("Test 12: Mask Secret Function")
    print("-" * 60)
    results.append(test_mask_secret_function())
    print()
    
    print("Test 13: Index Page Environment Variables Section")
    print("-" * 60)
    results.append(test_index_page_has_env_vars_section())
    print()
    
    print("Test 14: Index Page Backlog Section")
    print("-" * 60)
    results.append(test_index_page_has_backlog_section())
    print()
    
    print("="*60)
    if all(results):
        print("✓ All web app tests passed!")
    else:
        print("✗ Some web app tests failed")
    print("="*60)
    
    return all(results)


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
