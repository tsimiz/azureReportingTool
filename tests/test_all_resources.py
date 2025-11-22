"""Tests for all resources functionality."""

import json
import unittest
from unittest.mock import Mock, MagicMock, patch
from azure_reporter.modules.azure_fetcher import AzureFetcher
from azure_reporter.modules.ai_analyzer import AIAnalyzer
from azure_reporter.modules.backlog_generator import BacklogGenerator
from azure_reporter.modules.powerpoint_generator import PowerPointGenerator


class TestAllResourcesFunctionality(unittest.TestCase):
    """Test that all resources can be fetched and analyzed."""

    def test_fetch_generic_resources_exists(self):
        """Test that fetch_generic_resources method exists."""
        # Mock the Azure clients
        with patch('azure_reporter.modules.azure_fetcher.ResourceManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.ComputeManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.NetworkManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.StorageManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.ClientSecretCredential'):
            
            fetcher = AzureFetcher(
                subscription_id='test-subscription',
                tenant_id='test-tenant',
                client_id='test-client',
                client_secret='test-secret'
            )
            
            # Verify the method exists
            self.assertTrue(hasattr(fetcher, 'fetch_generic_resources'))
            self.assertTrue(callable(getattr(fetcher, 'fetch_generic_resources')))

    def test_fetch_all_resources_includes_generic(self):
        """Test that fetch_all_resources includes all_resources key."""
        with patch('azure_reporter.modules.azure_fetcher.ResourceManagementClient') as mock_rm, \
             patch('azure_reporter.modules.azure_fetcher.ComputeManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.NetworkManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.StorageManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.ClientSecretCredential'):
            
            # Mock the resource client's resources.list() method
            mock_resource = Mock()
            mock_resource.name = 'test-resource'
            mock_resource.type = 'Microsoft.Test/resources'
            mock_resource.location = 'eastus'
            mock_resource.id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Test/resources/test-resource'
            mock_resource.tags = {}
            
            mock_rm.return_value.resources.list.return_value = [mock_resource]
            mock_rm.return_value.resource_groups.list.return_value = []
            
            fetcher = AzureFetcher(
                subscription_id='test-subscription',
                tenant_id='test-tenant',
                client_id='test-client',
                client_secret='test-secret'
            )
            
            # Mock all fetch methods to return empty lists
            fetcher.fetch_virtual_machines = Mock(return_value=[])
            fetcher.fetch_storage_accounts = Mock(return_value=[])
            fetcher.fetch_network_security_groups = Mock(return_value=[])
            fetcher.fetch_virtual_networks = Mock(return_value=[])
            fetcher.fetch_resource_groups = Mock(return_value=[])
            
            resources = fetcher.fetch_all_resources()
            
            # Verify all_resources key exists
            self.assertIn('all_resources', resources)
            self.assertIsInstance(resources['all_resources'], list)

    def test_analyze_generic_resources_exists(self):
        """Test that analyze_generic_resources method exists."""
        with patch('azure_reporter.modules.ai_analyzer.OpenAI'):
            analyzer = AIAnalyzer(api_key='test-key')
            
            # Verify the method exists
            self.assertTrue(hasattr(analyzer, 'analyze_generic_resources'))
            self.assertTrue(callable(getattr(analyzer, 'analyze_generic_resources')))

    def test_analyze_generic_resources_groups_by_type(self):
        """Test that analyze_generic_resources groups resources by type."""
        with patch('azure_reporter.modules.ai_analyzer.OpenAI') as mock_openai:
            analyzer = AIAnalyzer(api_key='test-key')
            
            # Mock the API response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '{"overall_score": 8, "findings": [], "best_practices_met": [], "summary": "Good"}'
            mock_openai.return_value.chat.completions.create.return_value = mock_response
            
            test_resources = [
                {'name': 'res1', 'type': 'Microsoft.Compute/virtualMachines'},
                {'name': 'res2', 'type': 'Microsoft.Compute/virtualMachines'},
                {'name': 'res3', 'type': 'Microsoft.Storage/storageAccounts'}
            ]
            
            result = analyzer.analyze_generic_resources(test_resources)
            
            # Verify the result structure
            self.assertIn('resource_types', result)
            self.assertEqual(result['total_resource_types'], 2)
            self.assertEqual(result['total_resources'], 3)

    def test_backlog_generator_handles_generic_resources(self):
        """Test that backlog generator can handle generic resources."""
        generator = BacklogGenerator()
        
        test_analyses = {
            'generic_resources': {
                'resource_types': {
                    'Microsoft.Test/resources': {
                        'findings': [
                            {
                                'resource': 'test-resource',
                                'category': 'security',
                                'severity': 'high',
                                'issue': 'Test issue',
                                'recommendation': 'Test recommendation'
                            }
                        ]
                    }
                }
            }
        }
        
        generator.extract_backlog_items(test_analyses)
        
        # Verify backlog items were created
        self.assertGreater(len(generator.backlog_items), 0)
        self.assertEqual(generator.backlog_items[0]['resource_type'], 'resources')

    def test_powerpoint_includes_generic_resources(self):
        """Test that PowerPoint generator includes generic resources in overview."""
        ppt_gen = PowerPointGenerator()
        
        test_resources = {
            'resource_groups': [],
            'virtual_machines': [],
            'storage_accounts': [],
            'network_security_groups': [],
            'virtual_networks': [],
            'all_resources': [
                {'name': 'res1', 'type': 'Microsoft.Test/resources'}
            ]
        }
        
        # This should not raise an error
        ppt_gen.add_resource_overview_slide(test_resources)
        
        # Verify a slide was added
        self.assertEqual(len(ppt_gen.prs.slides), 1)

    def test_fetch_generic_resources_with_sku_serialization(self):
        """Test that resources with Sku objects can be JSON serialized."""
        with patch('azure_reporter.modules.azure_fetcher.ResourceManagementClient') as mock_rm, \
             patch('azure_reporter.modules.azure_fetcher.ComputeManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.NetworkManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.StorageManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.ClientSecretCredential'):
            
            # Create a mock Sku object that mimics Azure SDK's Sku
            mock_sku = Mock()
            mock_sku.name = 'Standard_LRS'
            mock_sku.tier = 'Standard'
            mock_sku.as_dict.return_value = {'name': 'Standard_LRS', 'tier': 'Standard'}
            
            # Mock the resource with a Sku object
            mock_resource = Mock()
            mock_resource.name = 'test-storage'
            mock_resource.type = 'Microsoft.Storage/storageAccounts'
            mock_resource.location = 'eastus'
            mock_resource.id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/test-storage'
            mock_resource.tags = {}
            mock_resource.kind = 'StorageV2'
            mock_resource.sku = mock_sku
            
            mock_rm.return_value.resources.list.return_value = [mock_resource]
            
            fetcher = AzureFetcher(
                subscription_id='test-subscription',
                tenant_id='test-tenant',
                client_id='test-client',
                client_secret='test-secret'
            )
            
            # Fetch generic resources
            resources = fetcher.fetch_generic_resources()
            
            # Verify resource was fetched
            self.assertEqual(len(resources), 1)
            self.assertEqual(resources[0]['name'], 'test-storage')
            
            # Verify sku is a dictionary
            self.assertIsInstance(resources[0]['sku'], dict)
            self.assertEqual(resources[0]['sku']['name'], 'Standard_LRS')
            self.assertEqual(resources[0]['sku']['tier'], 'Standard')
            
            # Verify the resource can be JSON serialized (this is the key test)
            try:
                json_str = json.dumps(resources)
                self.assertIsInstance(json_str, str)
                
                # Verify we can parse it back
                parsed = json.loads(json_str)
                self.assertEqual(len(parsed), 1)
                self.assertEqual(parsed[0]['sku']['name'], 'Standard_LRS')
            except TypeError as e:
                self.fail(f"Resources should be JSON serializable but got: {e}")

    def test_fetch_generic_resources_without_sku(self):
        """Test that resources without Sku don't cause issues."""
        with patch('azure_reporter.modules.azure_fetcher.ResourceManagementClient') as mock_rm, \
             patch('azure_reporter.modules.azure_fetcher.ComputeManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.NetworkManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.StorageManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.ClientSecretCredential'):
            
            # Mock a resource without a sku attribute
            mock_resource = Mock()
            mock_resource.name = 'test-vm'
            mock_resource.type = 'Microsoft.Compute/virtualMachines'
            mock_resource.location = 'westus'
            mock_resource.id = '/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/test-vm'
            mock_resource.tags = {'env': 'prod'}
            mock_resource.kind = None
            # Simulate resource without sku attribute
            del mock_resource.sku
            
            mock_rm.return_value.resources.list.return_value = [mock_resource]
            
            fetcher = AzureFetcher(
                subscription_id='test-subscription',
                tenant_id='test-tenant',
                client_id='test-client',
                client_secret='test-secret'
            )
            
            # Fetch generic resources
            resources = fetcher.fetch_generic_resources()
            
            # Verify resource was fetched
            self.assertEqual(len(resources), 1)
            self.assertEqual(resources[0]['name'], 'test-vm')
            
            # Verify sku is None
            self.assertIsNone(resources[0]['sku'])
            
            # Verify the resource can be JSON serialized
            try:
                json_str = json.dumps(resources)
                self.assertIsInstance(json_str, str)
            except TypeError as e:
                self.fail(f"Resources should be JSON serializable but got: {e}")

    def test_convert_sku_to_dict_helper(self):
        """Test the _convert_sku_to_dict helper method."""
        with patch('azure_reporter.modules.azure_fetcher.ResourceManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.ComputeManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.NetworkManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.StorageManagementClient'), \
             patch('azure_reporter.modules.azure_fetcher.ClientSecretCredential'):
            
            fetcher = AzureFetcher(
                subscription_id='test-subscription',
                tenant_id='test-tenant',
                client_id='test-client',
                client_secret='test-secret'
            )
            
            # Test with None
            result = fetcher._convert_sku_to_dict(None)
            self.assertIsNone(result)
            
            # Test with object that has as_dict method
            mock_sku = Mock()
            mock_sku.as_dict.return_value = {'name': 'Standard', 'tier': 'Standard'}
            result = fetcher._convert_sku_to_dict(mock_sku)
            self.assertEqual(result, {'name': 'Standard', 'tier': 'Standard'})
            
            # Test with dict input (should return as-is)
            dict_sku = {'name': 'Premium', 'tier': 'Premium'}
            result = fetcher._convert_sku_to_dict(dict_sku)
            self.assertEqual(result, dict_sku)
            
            # Test with object without as_dict method
            class InvalidSku:
                pass
            
            invalid_sku = InvalidSku()
            result = fetcher._convert_sku_to_dict(invalid_sku)
            self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
