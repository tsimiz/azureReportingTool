"""Tests for cost analysis functionality."""

import unittest
from azure_reporter.modules.cost_analyzer import CostAnalyzer


class TestCostAnalyzer(unittest.TestCase):
    """Test cases for CostAnalyzer class."""

    def test_cost_analyzer_initialization(self):
        """Test that CostAnalyzer can be initialized."""
        analyzer = CostAnalyzer()
        self.assertIsNotNone(analyzer)
        self.assertEqual(analyzer.cost_data, {})

    def test_cost_analyzer_with_cost_data(self):
        """Test CostAnalyzer initialization with cost data."""
        cost_data = {'monthly_cost': 1000}
        analyzer = CostAnalyzer(cost_data=cost_data)
        self.assertEqual(analyzer.cost_data, cost_data)

    def test_analyze_empty_resources(self):
        """Test analyzing empty resources."""
        analyzer = CostAnalyzer()
        result = analyzer.analyze_costs({})
        
        self.assertIn('summary', result)
        self.assertIn('findings', result)
        self.assertIn('recommendations', result)
        self.assertEqual(result['summary']['total_resources_analyzed'], 0)
        self.assertEqual(result['summary']['total_findings'], 0)

    def test_analyze_vm_stopped_not_deallocated(self):
        """Test that stopped VMs (not deallocated) are flagged as high severity."""
        analyzer = CostAnalyzer()
        resources = {
            'virtual_machines': [
                {
                    'name': 'test-vm',
                    'vm_size': 'Standard_D2s_v3',
                    'statuses': ['PowerState/stopped']
                }
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        # Should find the stopped VM issue (stopped but not deallocated)
        findings = result.get('findings', [])
        stopped_vm_findings = [f for f in findings if f.get('optimization_type') == 'stopped_vm']
        self.assertGreater(len(stopped_vm_findings), 0)
        self.assertEqual(stopped_vm_findings[0]['severity'], 'high')

    def test_analyze_vm_deallocated(self):
        """Test that deallocated VMs are flagged for storage costs."""
        analyzer = CostAnalyzer()
        resources = {
            'virtual_machines': [
                {
                    'name': 'deallocated-vm',
                    'vm_size': 'Standard_D2s_v3',
                    'statuses': ['PowerState/deallocated']
                }
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        findings = result.get('findings', [])
        deallocated_findings = [f for f in findings if 'deallocated' in f.get('issue', '').lower()]
        self.assertGreater(len(deallocated_findings), 0)

    def test_analyze_gpu_vm(self):
        """Test that GPU VMs are flagged for review."""
        analyzer = CostAnalyzer()
        resources = {
            'virtual_machines': [
                {
                    'name': 'gpu-vm',
                    'vm_size': 'Standard_NC6',
                    'statuses': ['PowerState/running']
                }
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        findings = result.get('findings', [])
        gpu_findings = [f for f in findings if 'GPU' in f.get('issue', '')]
        self.assertGreater(len(gpu_findings), 0)

    def test_analyze_running_vm_reserved_instance(self):
        """Test that running VMs get Reserved Instance recommendation."""
        analyzer = CostAnalyzer()
        resources = {
            'virtual_machines': [
                {
                    'name': 'running-vm',
                    'vm_size': 'Standard_D2s_v3',
                    'statuses': ['PowerState/running']
                }
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        findings = result.get('findings', [])
        ri_findings = [f for f in findings if 'Reserved Instance' in f.get('issue', '')]
        self.assertGreater(len(ri_findings), 0)

    def test_analyze_premium_storage(self):
        """Test that premium storage is flagged for review."""
        analyzer = CostAnalyzer()
        resources = {
            'storage_accounts': [
                {
                    'name': 'premiumstorage',
                    'sku': 'Premium_LRS',
                    'kind': 'StorageV2'
                }
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        findings = result.get('findings', [])
        premium_findings = [f for f in findings if 'Premium' in f.get('issue', '')]
        self.assertGreater(len(premium_findings), 0)

    def test_analyze_geo_redundant_storage(self):
        """Test that geo-redundant storage is flagged."""
        analyzer = CostAnalyzer()
        resources = {
            'storage_accounts': [
                {
                    'name': 'grs-storage',
                    'sku': 'Standard_GRS',
                    'kind': 'StorageV2'
                }
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        findings = result.get('findings', [])
        grs_findings = [f for f in findings if 'geo-redundant' in f.get('issue', '').lower()]
        self.assertGreater(len(grs_findings), 0)

    def test_analyze_legacy_blob_storage(self):
        """Test that legacy BlobStorage kind is flagged."""
        analyzer = CostAnalyzer()
        resources = {
            'storage_accounts': [
                {
                    'name': 'legacy-storage',
                    'sku': 'Standard_LRS',
                    'kind': 'BlobStorage'
                }
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        findings = result.get('findings', [])
        legacy_findings = [f for f in findings if 'legacy' in f.get('issue', '').lower()]
        self.assertGreater(len(legacy_findings), 0)

    def test_analyze_untagged_resources(self):
        """Test that resources without cost allocation tags are flagged."""
        analyzer = CostAnalyzer()
        resources = {
            'all_resources': [
                {'name': 'res1', 'type': 'Microsoft.Web/sites', 'tags': None},
                {'name': 'res2', 'type': 'Microsoft.Web/sites', 'tags': {}},
                {'name': 'res3', 'type': 'Microsoft.Web/sites', 'tags': {'CostCenter': 'IT'}}
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        findings = result.get('findings', [])
        tag_findings = [f for f in findings if 'tag' in f.get('issue', '').lower()]
        self.assertGreater(len(tag_findings), 0)

    def test_analyze_disk_resources(self):
        """Test that disk resources are flagged for review."""
        analyzer = CostAnalyzer()
        resources = {
            'all_resources': [
                {
                    'name': 'test-disk',
                    'type': 'Microsoft.Compute/disks',
                    'tags': {}
                }
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        findings = result.get('findings', [])
        disk_findings = [f for f in findings if 'disk' in f.get('issue', '').lower()]
        self.assertGreater(len(disk_findings), 0)

    def test_analyze_public_ip_resources(self):
        """Test that public IP resources are flagged for review."""
        analyzer = CostAnalyzer()
        resources = {
            'all_resources': [
                {
                    'name': 'test-public-ip',
                    'type': 'Microsoft.Network/publicIPAddresses',
                    'tags': {}
                }
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        findings = result.get('findings', [])
        # Check for public IP findings by optimization type
        ip_findings = [f for f in findings if f.get('optimization_type') == 'orphaned_ip_review']
        self.assertGreater(len(ip_findings), 0)

    def test_summary_generation(self):
        """Test that summary is correctly generated."""
        analyzer = CostAnalyzer()
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'vm_size': 'Standard_D2s_v3', 'statuses': ['PowerState/running']},
                {'name': 'vm2', 'vm_size': 'Standard_D2s_v3', 'statuses': ['PowerState/deallocated']}
            ],
            'storage_accounts': [
                {'name': 'storage1', 'sku': 'Standard_LRS', 'kind': 'StorageV2'}
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        summary = result.get('summary', {})
        
        self.assertIn('total_resources_analyzed', summary)
        self.assertIn('total_findings', summary)
        self.assertIn('findings_by_severity', summary)
        self.assertIn('optimization_opportunities', summary)

    def test_recommendations_prioritization(self):
        """Test that recommendations are prioritized correctly."""
        analyzer = CostAnalyzer()
        resources = {
            'virtual_machines': [
                {'name': 'stopped-vm', 'vm_size': 'Standard_D2s_v3', 'statuses': ['PowerState/stopped']},
                {'name': 'running-vm', 'vm_size': 'Standard_D2s_v3', 'statuses': ['PowerState/running']}
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        recommendations = result.get('recommendations', [])
        
        # Recommendations should be present
        self.assertGreater(len(recommendations), 0)
        
        # Each recommendation should have required fields
        for rec in recommendations:
            self.assertIn('type', rec)
            self.assertIn('priority', rec)
            self.assertIn('affected_resources', rec)
            self.assertIn('summary', rec)
            self.assertIn('action', rec)

    def test_opportunity_counts(self):
        """Test that opportunity counts are correctly calculated."""
        analyzer = CostAnalyzer()
        resources = {
            'virtual_machines': [
                {'name': 'stopped-vm', 'vm_size': 'Standard_D2s_v3', 'statuses': ['PowerState/stopped']},
                {'name': 'running-vm', 'vm_size': 'Standard_D2s_v3', 'statuses': ['PowerState/running']}
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        opportunities = result.get('optimization_opportunities', {})
        
        self.assertIn('immediate_actions', opportunities)
        self.assertIn('review_needed', opportunities)
        self.assertIn('best_practices', opportunities)

    def test_findings_have_required_fields(self):
        """Test that all findings have required fields."""
        analyzer = CostAnalyzer()
        resources = {
            'virtual_machines': [
                {'name': 'test-vm', 'vm_size': 'Standard_NC6', 'statuses': ['PowerState/running']}
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        findings = result.get('findings', [])
        
        required_fields = ['resource', 'resource_type', 'category', 'severity', 
                          'issue', 'recommendation', 'optimization_type']
        
        for finding in findings:
            for field in required_fields:
                self.assertIn(field, finding, f"Finding missing required field: {field}")

    def test_analyze_multiple_resource_types(self):
        """Test analyzing multiple resource types together."""
        analyzer = CostAnalyzer()
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'vm_size': 'Standard_D2s_v3', 'statuses': ['PowerState/running']}
            ],
            'storage_accounts': [
                {'name': 'storage1', 'sku': 'Premium_LRS', 'kind': 'StorageV2'}
            ],
            'all_resources': [
                {'name': 'disk1', 'type': 'Microsoft.Compute/disks', 'tags': {}}
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        # Should have findings from multiple resource types
        findings = result.get('findings', [])
        resource_types = set(f.get('resource_type', '') for f in findings)
        self.assertGreater(len(resource_types), 1)


class TestCostAnalyzerEdgeCases(unittest.TestCase):
    """Test edge cases for CostAnalyzer."""

    def test_empty_vm_statuses(self):
        """Test handling of VMs with empty statuses."""
        analyzer = CostAnalyzer()
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'vm_size': 'Standard_D2s_v3', 'statuses': []}
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        # Should not crash, analysis should complete
        self.assertIn('summary', result)
        self.assertIn('findings', result)

    def test_missing_vm_size(self):
        """Test handling of VMs with missing vm_size."""
        analyzer = CostAnalyzer()
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'statuses': ['PowerState/running']}
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        # Should not crash
        self.assertIn('summary', result)

    def test_missing_storage_sku(self):
        """Test handling of storage accounts with missing SKU."""
        analyzer = CostAnalyzer()
        resources = {
            'storage_accounts': [
                {'name': 'storage1', 'kind': 'StorageV2'}
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        # Should not crash
        self.assertIn('summary', result)

    def test_resource_consolidation_detection(self):
        """Test detection of many similar resources for consolidation."""
        analyzer = CostAnalyzer()
        resources = {
            'all_resources': [
                {'name': f'webapp{i}', 'type': 'Microsoft.Web/sites', 'tags': {'Env': 'prod'}}
                for i in range(15)
            ]
        }
        
        result = analyzer.analyze_costs(resources)
        
        findings = result.get('findings', [])
        consolidation_findings = [f for f in findings if 'consolidation' in f.get('optimization_type', '')]
        self.assertGreater(len(consolidation_findings), 0)

    def test_analysis_date_included(self):
        """Test that analysis date is included in results."""
        analyzer = CostAnalyzer()
        result = analyzer.analyze_costs({})
        
        self.assertIn('analysis_date', result)
        self.assertIsNotNone(result['analysis_date'])


if __name__ == '__main__':
    unittest.main()
