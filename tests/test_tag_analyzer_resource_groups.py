"""Tests for tag analysis with resource groups."""

import unittest
from azure_reporter.modules.tag_analyzer import TagAnalyzer


class TestTagAnalyzerResourceGroups(unittest.TestCase):
    """Test cases for resource group tag compliance."""

    def test_resource_group_compliance_with_resources(self):
        """Test that RG compliance includes both RG tags and resources within."""
        required_tags = ['Environment', 'Owner']
        analyzer = TagAnalyzer(required_tags=required_tags)
        
        resources = {
            'resource_groups': [
                {
                    'name': 'rg1',
                    'tags': {'Environment': 'prod', 'Owner': 'team1'}  # 100% compliant
                }
            ],
            'virtual_machines': [
                {
                    'name': 'vm1',
                    'id': '/subs/1/rg1/vm1',
                    'resource_group': 'rg1',
                    'tags': {'Environment': 'prod'}  # 50% compliant (missing Owner)
                },
                {
                    'name': 'vm2',
                    'id': '/subs/1/rg1/vm2',
                    'resource_group': 'rg1',
                    'tags': {}  # 0% compliant
                }
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # Check resource group details
        rg_details = result['resource_groups_details']
        self.assertEqual(len(rg_details), 1)
        
        rg1 = rg_details[0]
        self.assertEqual(rg1['name'], 'rg1')
        self.assertEqual(rg1['total_resources'], 2)
        self.assertEqual(rg1['non_compliant_resources'], 2)
        
        # RG's own tags are 100% compliant
        # Resources: vm1 is 50% compliant, vm2 is 0% compliant
        # Average resource compliance: (50 + 0) / 2 = 25%
        # Overall RG compliance: (100 + 25) / 2 = 62.5%
        self.assertAlmostEqual(rg1['compliance_rate'], 62.5, delta=0.1)
        
        # Check that resources are listed
        self.assertEqual(len(rg1['resources']), 2)
        
        # Find vm1 and vm2
        vm1 = next(r for r in rg1['resources'] if r['resource_name'] == 'vm1')
        vm2 = next(r for r in rg1['resources'] if r['resource_name'] == 'vm2')
        
        self.assertEqual(vm1['compliance_rate'], 50.0)
        self.assertIn('Owner', vm1['missing_tags'])
        
        self.assertEqual(vm2['compliance_rate'], 0.0)
        self.assertIn('Environment', vm2['missing_tags'])
        self.assertIn('Owner', vm2['missing_tags'])

    def test_resource_group_fully_compliant_with_noncompliant_resources(self):
        """Test that even if RG is 100% compliant, it shows less if resources aren't."""
        required_tags = ['Environment']
        analyzer = TagAnalyzer(required_tags=required_tags)
        
        resources = {
            'resource_groups': [
                {
                    'name': 'rg1',
                    'tags': {'Environment': 'prod'}  # 100% compliant
                }
            ],
            'virtual_machines': [
                {
                    'name': 'vm1',
                    'id': '/subs/1/rg1/vm1',
                    'resource_group': 'rg1',
                    'tags': {}  # 0% compliant
                }
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        rg_details = result['resource_groups_details']
        rg1 = rg_details[0]
        
        # RG compliance should be (100 + 0) / 2 = 50%, not 100%
        self.assertEqual(rg1['compliance_rate'], 50.0)

    def test_overall_compliance_includes_resource_groups(self):
        """Test that overall compliance includes resource groups as items."""
        required_tags = ['Environment']
        analyzer = TagAnalyzer(required_tags=required_tags)
        
        resources = {
            'resource_groups': [
                {
                    'name': 'rg1',
                    'tags': {'Environment': 'prod'}  # 100% compliant
                }
            ],
            'virtual_machines': [
                {
                    'name': 'vm1',
                    'id': '/subs/1/rg1/vm1',
                    'resource_group': 'rg1',
                    'tags': {}  # 0% compliant
                }
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # We have:
        # - 1 resource group with 50% compliance (RG tags 100%, resource 0%, avg = 50%)
        # - 1 resource with 0% compliance
        # Overall: (50 + 0) / 2 = 25%
        self.assertEqual(result['summary']['overall_compliance_rate'], 25.0)

    def test_multiple_resource_groups_with_different_compliance(self):
        """Test multiple resource groups with varying compliance levels."""
        required_tags = ['Environment', 'Owner']
        analyzer = TagAnalyzer(required_tags=required_tags)
        
        resources = {
            'resource_groups': [
                {
                    'name': 'rg1',
                    'tags': {'Environment': 'prod', 'Owner': 'team1'}  # 100% compliant
                },
                {
                    'name': 'rg2',
                    'tags': {'Environment': 'dev'}  # 50% compliant
                }
            ],
            'virtual_machines': [
                {
                    'name': 'vm1',
                    'id': '/subs/1/rg1/vm1',
                    'resource_group': 'rg1',
                    'tags': {'Environment': 'prod', 'Owner': 'team1'}  # 100% compliant
                },
                {
                    'name': 'vm2',
                    'id': '/subs/1/rg2/vm2',
                    'resource_group': 'rg2',
                    'tags': {}  # 0% compliant
                }
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        rg_details = result['resource_groups_details']
        self.assertEqual(len(rg_details), 2)
        
        # Find rg1 and rg2
        rg1 = next(r for r in rg_details if r['name'] == 'rg1')
        rg2 = next(r for r in rg_details if r['name'] == 'rg2')
        
        # rg1: (100 + 100) / 2 = 100%
        self.assertEqual(rg1['compliance_rate'], 100.0)
        self.assertEqual(rg1['non_compliant_resources'], 0)
        
        # rg2: (50 + 0) / 2 = 25%
        self.assertEqual(rg2['compliance_rate'], 25.0)
        self.assertEqual(rg2['non_compliant_resources'], 1)

    def test_resource_group_without_resources(self):
        """Test that resource group without resources shows only its own compliance."""
        required_tags = ['Environment']
        analyzer = TagAnalyzer(required_tags=required_tags)
        
        resources = {
            'resource_groups': [
                {
                    'name': 'empty-rg',
                    'tags': {'Environment': 'prod'}  # 100% compliant
                }
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        rg_details = result['resource_groups_details']
        self.assertEqual(len(rg_details), 1)
        
        rg = rg_details[0]
        self.assertEqual(rg['name'], 'empty-rg')
        self.assertEqual(rg['total_resources'], 0)
        self.assertEqual(rg['compliance_rate'], 100.0)  # Only RG's own compliance

    def test_resource_group_with_invalid_tag_values(self):
        """Test resource group with invalid tag values affects compliance."""
        required_tags = ['Environment']
        invalid_values = ['none', 'na']
        analyzer = TagAnalyzer(required_tags=required_tags, invalid_tag_values=invalid_values)
        
        resources = {
            'resource_groups': [
                {
                    'name': 'rg1',
                    'tags': {'Environment': 'none'}  # 0% compliant (invalid value)
                }
            ],
            'virtual_machines': [
                {
                    'name': 'vm1',
                    'id': '/subs/1/rg1/vm1',
                    'resource_group': 'rg1',
                    'tags': {'Environment': 'prod'}  # 100% compliant
                }
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        rg_details = result['resource_groups_details']
        rg1 = rg_details[0]
        
        # RG has invalid value: 0%, resource is 100%
        # Overall RG compliance: (0 + 100) / 2 = 50%
        self.assertEqual(rg1['compliance_rate'], 50.0)
        
        # Check that invalid value is reported
        self.assertEqual(len(rg1['invalid_value_tags']), 1)
        self.assertEqual(rg1['invalid_value_tags'][0]['tag_name'], 'Environment')

    def test_resources_shown_in_rg_details(self):
        """Test that resources are visible in resource group details."""
        required_tags = ['Environment']
        analyzer = TagAnalyzer(required_tags=required_tags)
        
        resources = {
            'resource_groups': [
                {
                    'name': 'rg1',
                    'tags': {'Environment': 'prod'}
                }
            ],
            'virtual_machines': [
                {
                    'name': 'vm1',
                    'id': '/subs/1/rg1/vm1',
                    'resource_group': 'rg1',
                    'tags': {'Environment': 'prod'}
                },
                {
                    'name': 'vm2',
                    'id': '/subs/1/rg1/vm2',
                    'resource_group': 'rg1',
                    'tags': {}
                }
            ],
            'storage_accounts': [
                {
                    'name': 'storage1',
                    'id': '/subs/1/rg1/storage1',
                    'resource_group': 'rg1',
                    'tags': {'Environment': 'prod'}
                }
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        rg_details = result['resource_groups_details']
        rg1 = rg_details[0]
        
        # Should have all 3 resources listed
        self.assertEqual(rg1['total_resources'], 3)
        self.assertEqual(len(rg1['resources']), 3)
        
        # Check resource names are present
        resource_names = [r['resource_name'] for r in rg1['resources']]
        self.assertIn('vm1', resource_names)
        self.assertIn('vm2', resource_names)
        self.assertIn('storage1', resource_names)
        
        # Check which resources are non-compliant
        self.assertEqual(rg1['non_compliant_resources'], 1)
        
        non_compliant_res = [r for r in rg1['resources'] 
                            if r.get('missing_tags') and len(r['missing_tags']) > 0]
        self.assertEqual(len(non_compliant_res), 1)
        self.assertEqual(non_compliant_res[0]['resource_name'], 'vm2')


if __name__ == '__main__':
    unittest.main()
