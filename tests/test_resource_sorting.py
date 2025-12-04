"""Tests for resource sorting in tag compliance details."""

import unittest
from azure_reporter.modules.tag_analyzer import TagAnalyzer


class TestResourceSorting(unittest.TestCase):
    """Test cases for resource sorting within resource groups."""

    def test_resources_sorted_non_compliant_first(self):
        """Test that non-compliant resources appear before compliant ones."""
        required_tags = ['Environment', 'Owner']
        analyzer = TagAnalyzer(required_tags=required_tags)
        
        resources = {
            'resource_groups': [
                {
                    'name': 'rg1',
                    'tags': {'Environment': 'prod', 'Owner': 'team1'}
                }
            ],
            'virtual_machines': [
                # Mix of compliant and non-compliant resources
                {
                    'name': 'vm-compliant-1',
                    'id': '/subs/1/rg1/vm1',
                    'resource_group': 'rg1',
                    'tags': {'Environment': 'prod', 'Owner': 'team1'}  # 100% compliant
                },
                {
                    'name': 'vm-non-compliant-1',
                    'id': '/subs/1/rg1/vm2',
                    'resource_group': 'rg1',
                    'tags': {'Environment': 'prod'}  # 50% compliant - missing Owner
                },
                {
                    'name': 'vm-compliant-2',
                    'id': '/subs/1/rg1/vm3',
                    'resource_group': 'rg1',
                    'tags': {'Environment': 'dev', 'Owner': 'team2'}  # 100% compliant
                },
                {
                    'name': 'vm-non-compliant-2',
                    'id': '/subs/1/rg1/vm4',
                    'resource_group': 'rg1',
                    'tags': {}  # 0% compliant - missing both tags
                }
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # Get the resource group details
        rg_details = result['resource_groups_details']
        self.assertEqual(len(rg_details), 1)
        
        rg1 = rg_details[0]
        resources_list = rg1['resources']
        
        # Should have 4 resources
        self.assertEqual(len(resources_list), 4)
        
        # First two should be non-compliant (less than 100%)
        self.assertLess(resources_list[0]['compliance_rate'], 100.0)
        self.assertLess(resources_list[1]['compliance_rate'], 100.0)
        
        # Last two should be compliant (100%)
        self.assertEqual(resources_list[2]['compliance_rate'], 100.0)
        self.assertEqual(resources_list[3]['compliance_rate'], 100.0)
        
        # The most non-compliant (0%) should be first among non-compliant
        self.assertEqual(resources_list[0]['resource_name'], 'vm-non-compliant-2')
        self.assertEqual(resources_list[0]['compliance_rate'], 0.0)

    def test_resources_have_tags_field(self):
        """Test that resources include their actual tags in the result."""
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
                    'tags': {'Environment': 'prod', 'Owner': 'team1', 'CostCenter': 'cc1'}
                }
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        rg_details = result['resource_groups_details']
        rg1 = rg_details[0]
        resources_list = rg1['resources']
        
        # Check that the resource has the 'tags' field
        self.assertIn('tags', resources_list[0])
        
        # Verify the tags are correct
        tags = resources_list[0]['tags']
        self.assertEqual(tags['Environment'], 'prod')
        self.assertEqual(tags['Owner'], 'team1')
        self.assertEqual(tags['CostCenter'], 'cc1')

    def test_sorting_with_invalid_values(self):
        """Test that resources with invalid tag values are sorted as non-compliant."""
        required_tags = ['Environment']
        invalid_values = ['none', 'na']
        analyzer = TagAnalyzer(required_tags=required_tags, invalid_tag_values=invalid_values)
        
        resources = {
            'resource_groups': [
                {
                    'name': 'rg1',
                    'tags': {'Environment': 'prod'}
                }
            ],
            'virtual_machines': [
                {
                    'name': 'vm-compliant',
                    'id': '/subs/1/rg1/vm1',
                    'resource_group': 'rg1',
                    'tags': {'Environment': 'prod'}  # Valid value
                },
                {
                    'name': 'vm-invalid-value',
                    'id': '/subs/1/rg1/vm2',
                    'resource_group': 'rg1',
                    'tags': {'Environment': 'none'}  # Invalid value
                }
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        rg_details = result['resource_groups_details']
        rg1 = rg_details[0]
        resources_list = rg1['resources']
        
        # Non-compliant (invalid value) should be first
        self.assertEqual(resources_list[0]['resource_name'], 'vm-invalid-value')
        self.assertEqual(resources_list[0]['compliance_rate'], 0.0)
        
        # Compliant should be second
        self.assertEqual(resources_list[1]['resource_name'], 'vm-compliant')
        self.assertEqual(resources_list[1]['compliance_rate'], 100.0)

    def test_multiple_resource_groups_with_sorted_resources(self):
        """Test that each resource group has its resources sorted independently."""
        required_tags = ['Environment']
        analyzer = TagAnalyzer(required_tags=required_tags)
        
        resources = {
            'resource_groups': [
                {'name': 'rg1', 'tags': {'Environment': 'prod'}},
                {'name': 'rg2', 'tags': {'Environment': 'dev'}}
            ],
            'virtual_machines': [
                # RG1 resources
                {
                    'name': 'rg1-compliant',
                    'id': '/subs/1/rg1/vm1',
                    'resource_group': 'rg1',
                    'tags': {'Environment': 'prod'}
                },
                {
                    'name': 'rg1-non-compliant',
                    'id': '/subs/1/rg1/vm2',
                    'resource_group': 'rg1',
                    'tags': {}
                },
                # RG2 resources
                {
                    'name': 'rg2-non-compliant',
                    'id': '/subs/1/rg2/vm3',
                    'resource_group': 'rg2',
                    'tags': {}
                },
                {
                    'name': 'rg2-compliant',
                    'id': '/subs/1/rg2/vm4',
                    'resource_group': 'rg2',
                    'tags': {'Environment': 'dev'}
                }
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        rg_details = result['resource_groups_details']
        
        # Find each resource group
        rg1 = next(rg for rg in rg_details if rg['name'] == 'rg1')
        rg2 = next(rg for rg in rg_details if rg['name'] == 'rg2')
        
        # RG1: non-compliant first
        self.assertEqual(rg1['resources'][0]['resource_name'], 'rg1-non-compliant')
        self.assertEqual(rg1['resources'][1]['resource_name'], 'rg1-compliant')
        
        # RG2: non-compliant first
        self.assertEqual(rg2['resources'][0]['resource_name'], 'rg2-non-compliant')
        self.assertEqual(rg2['resources'][1]['resource_name'], 'rg2-compliant')


if __name__ == '__main__':
    unittest.main()
