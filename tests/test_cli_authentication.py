"""Tests for Azure CLI authentication fallback."""

import sys
import os
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from azure_reporter.modules.azure_fetcher import AzureFetcher
from azure_reporter.utils.config_loader import ConfigLoader


class TestCLIAuthentication:
    """Test CLI authentication fallback functionality."""
    
    def test_azure_fetcher_with_service_principal(self):
        """Test that AzureFetcher uses ClientSecretCredential when SP credentials are provided."""
        subscription_id = "test-subscription-id"
        tenant_id = "test-tenant-id"
        client_id = "test-client-id"
        client_secret = "test-client-secret"
        
        with patch('azure_reporter.modules.azure_fetcher.ClientSecretCredential') as mock_sp_cred, \
             patch('azure_reporter.modules.azure_fetcher.ResourceManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.ComputeManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.NetworkManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.StorageManagementClient'):
            
            fetcher = AzureFetcher(
                subscription_id=subscription_id,
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            
            # Verify ClientSecretCredential was called with correct parameters
            mock_sp_cred.assert_called_once_with(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            
            # Verify the credential is set to the ClientSecretCredential instance
            assert fetcher.credential == mock_sp_cred.return_value
    
    def test_azure_fetcher_without_service_principal(self):
        """Test that AzureFetcher uses DefaultAzureCredential when SP credentials are not provided."""
        subscription_id = "test-subscription-id"
        
        with patch('azure_reporter.modules.azure_fetcher.DefaultAzureCredential') as mock_default_cred, \
             patch('azure_reporter.modules.azure_fetcher.ResourceManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.ComputeManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.NetworkManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.StorageManagementClient'):
            
            # Test with no SP credentials
            fetcher = AzureFetcher(subscription_id=subscription_id)
            
            # Verify DefaultAzureCredential was called
            mock_default_cred.assert_called_once()
            
            # Verify the credential is set to the DefaultAzureCredential instance
            assert fetcher.credential == mock_default_cred.return_value
    
    def test_azure_fetcher_with_partial_service_principal(self):
        """Test that AzureFetcher uses DefaultAzureCredential when SP credentials are partial."""
        subscription_id = "test-subscription-id"
        
        with patch('azure_reporter.modules.azure_fetcher.DefaultAzureCredential') as mock_default_cred, \
             patch('azure_reporter.modules.azure_fetcher.ResourceManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.ComputeManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.NetworkManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.StorageManagementClient'):
            
            # Test with partial SP credentials (only tenant_id)
            fetcher = AzureFetcher(
                subscription_id=subscription_id,
                tenant_id="test-tenant-id",
                client_id=None,
                client_secret=None
            )
            
            # Verify DefaultAzureCredential was called (not ClientSecretCredential)
            mock_default_cred.assert_called_once()
            
            # Verify the credential is set to the DefaultAzureCredential instance
            assert fetcher.credential == mock_default_cred.return_value


class TestConfigLoaderValidation:
    """Test ConfigLoader validation for CLI authentication."""
    
    def test_config_validation_with_subscription_id_only(self):
        """Test that validation passes with only subscription ID (CLI auth)."""
        with patch.dict(os.environ, {
            'AZURE_SUBSCRIPTION_ID': 'test-subscription-id'
        }, clear=True):
            config_loader = ConfigLoader()
            
            # Disable AI analysis for this test to focus on Azure auth
            config_loader.config['ai_analysis']['enabled'] = False
            
            # Should pass validation with just subscription ID
            assert config_loader.validate_config() is True
    
    def test_config_validation_with_full_service_principal(self):
        """Test that validation passes with full Service Principal credentials."""
        with patch.dict(os.environ, {
            'AZURE_SUBSCRIPTION_ID': 'test-subscription-id',
            'AZURE_TENANT_ID': 'test-tenant-id',
            'AZURE_CLIENT_ID': 'test-client-id',
            'AZURE_CLIENT_SECRET': 'test-client-secret'
        }, clear=True):
            config_loader = ConfigLoader()
            
            # Disable AI analysis for this test
            config_loader.config['ai_analysis']['enabled'] = False
            
            # Should pass validation with full SP credentials
            assert config_loader.validate_config() is True
    
    def test_config_validation_warns_on_partial_service_principal(self):
        """Test that validation warns when SP credentials are partially provided."""
        with patch.dict(os.environ, {
            'AZURE_SUBSCRIPTION_ID': 'test-subscription-id',
            'AZURE_TENANT_ID': 'test-tenant-id',
            # Missing CLIENT_ID and CLIENT_SECRET
        }, clear=True):
            config_loader = ConfigLoader()
            
            # Disable AI analysis for this test
            config_loader.config['ai_analysis']['enabled'] = False
            
            # Should still pass validation but with warning
            with patch('azure_reporter.utils.config_loader.logger') as mock_logger:
                result = config_loader.validate_config()
                
                # Should pass validation
                assert result is True
                
                # Should have logged a warning about partial SP configuration
                warning_calls = [call for call in mock_logger.warning.call_args_list 
                               if 'Service Principal partially configured' in str(call)]
                assert len(warning_calls) > 0
    
    def test_config_validation_requires_subscription_id(self):
        """Test that validation fails without subscription ID."""
        with patch.dict(os.environ, {}, clear=True):
            config_loader = ConfigLoader()
            
            # Disable AI analysis for this test
            config_loader.config['ai_analysis']['enabled'] = False
            
            # Should fail validation without subscription ID
            assert config_loader.validate_config() is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
