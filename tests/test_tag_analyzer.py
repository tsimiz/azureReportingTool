"""Tests for tag analysis functionality."""

import unittest
from azure_reporter.modules.tag_analyzer import TagAnalyzer


class TestTagAnalyzer(unittest.TestCase):
    """Test cases for TagAnalyzer class."""

    def test_tag_analyzer_initialization(self):
        """Test that TagAnalyzer can be initialized."""
        analyzer = TagAnalyzer()
        self.assertIsNotNone(analyzer)
        self.assertEqual(len(analyzer.required_tags), 0)

    def test_tag_analyzer_with_required_tags(self):
        """Test TagAnalyzer initialization with required tags."""
        required_tags = ['Environment', 'Owner', 'CostCenter']
        analyzer = TagAnalyzer(required_tags=required_tags)
        self.assertEqual(len(analyzer.required_tags), 3)
        self.assertIn('Environment', analyzer.required_tags)
        self.assertIn('Owner', analyzer.required_tags)
        self.assertIn('CostCenter', analyzer.required_tags)

    def test_analyze_empty_resources(self):
        """Test analyzing empty resources."""
        analyzer = TagAnalyzer()
        result = analyzer.analyze_resource_tags({})
        
        self.assertIn('summary', result)
        self.assertEqual(result['summary']['total_resources'], 0)
        self.assertEqual(result['summary']['resources_with_tags'], 0)
        self.assertEqual(result['summary']['resources_without_tags'], 0)

    def test_analyze_resources_with_tags(self):
        """Test analyzing resources that have tags."""
        analyzer = TagAnalyzer()
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Environment': 'prod', 'Owner': 'team1'}},
                {'name': 'vm2', 'id': '/subs/1/vm2', 'tags': {'Environment': 'dev'}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        self.assertEqual(result['summary']['total_resources'], 2)
        self.assertEqual(result['summary']['resources_with_tags'], 2)
        self.assertEqual(result['summary']['resources_without_tags'], 0)
        self.assertEqual(result['summary']['unique_tags_found'], 2)  # Environment and Owner

    def test_analyze_resources_without_tags(self):
        """Test analyzing resources that have no tags."""
        analyzer = TagAnalyzer()
        resources = {
            'storage_accounts': [
                {'name': 'storage1', 'id': '/subs/1/storage1', 'tags': {}},
                {'name': 'storage2', 'id': '/subs/1/storage2', 'tags': None}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        self.assertEqual(result['summary']['total_resources'], 2)
        self.assertEqual(result['summary']['resources_with_tags'], 0)
        self.assertEqual(result['summary']['resources_without_tags'], 2)

    def test_tag_compliance_all_compliant(self):
        """Test compliance when all resources have required tags."""
        required_tags = ['Environment', 'Owner']
        analyzer = TagAnalyzer(required_tags=required_tags)
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Environment': 'prod', 'Owner': 'team1'}},
                {'name': 'vm2', 'id': '/subs/1/vm2', 'tags': {'Environment': 'dev', 'Owner': 'team2'}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        self.assertEqual(result['summary']['overall_compliance_rate'], 100.0)
        self.assertEqual(len(result['non_compliant_resources']), 0)

    def test_tag_compliance_partial(self):
        """Test compliance when some resources are missing required tags."""
        required_tags = ['Environment', 'Owner', 'CostCenter']
        analyzer = TagAnalyzer(required_tags=required_tags)
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Environment': 'prod', 'Owner': 'team1'}},
                {'name': 'vm2', 'id': '/subs/1/vm2', 'tags': {'Environment': 'dev'}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # Both resources are missing CostCenter
        self.assertLess(result['summary']['overall_compliance_rate'], 100.0)
        self.assertGreater(len(result['non_compliant_resources']), 0)

    def test_tag_compliance_none_compliant(self):
        """Test compliance when no resources have required tags."""
        required_tags = ['CostCenter', 'Project']
        analyzer = TagAnalyzer(required_tags=required_tags)
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Environment': 'prod'}},
                {'name': 'vm2', 'id': '/subs/1/vm2', 'tags': {}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        self.assertLess(result['summary']['overall_compliance_rate'], 50.0)
        self.assertEqual(len(result['non_compliant_resources']), 2)

    def test_non_compliant_resources_details(self):
        """Test that non-compliant resources include correct details."""
        required_tags = ['Environment', 'Owner']
        analyzer = TagAnalyzer(required_tags=required_tags)
        resources = {
            'virtual_machines': [
                {
                    'name': 'vm1', 
                    'id': '/subs/1/resourceGroups/rg1/vm1', 
                    'resource_group': 'rg1',
                    'tags': {'Environment': 'prod'}
                }
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        self.assertEqual(len(result['non_compliant_resources']), 1)
        non_compliant = result['non_compliant_resources'][0]
        self.assertEqual(non_compliant['resource_name'], 'vm1')
        self.assertEqual(non_compliant['resource_group'], 'rg1')
        self.assertIn('Owner', non_compliant['missing_tags'])
        self.assertNotIn('Environment', non_compliant['missing_tags'])

    def test_required_tags_compliance_summary(self):
        """Test the required tags compliance summary."""
        required_tags = ['Environment', 'Owner']
        analyzer = TagAnalyzer(required_tags=required_tags)
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Environment': 'prod', 'Owner': 'team1'}},
                {'name': 'vm2', 'id': '/subs/1/vm2', 'tags': {'Environment': 'dev'}},
                {'name': 'vm3', 'id': '/subs/1/vm3', 'tags': {}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # Environment is on 2 of 3 resources
        # Owner is on 1 of 3 resources
        req_compliance = {item['tag_name']: item for item in result['required_tags_compliance']}
        
        self.assertEqual(req_compliance['Environment']['compliant_resources'], 2)
        self.assertEqual(req_compliance['Environment']['non_compliant_resources'], 1)
        self.assertEqual(req_compliance['Owner']['compliant_resources'], 1)
        self.assertEqual(req_compliance['Owner']['non_compliant_resources'], 2)

    def test_tag_usage_summary(self):
        """Test the tag usage summary."""
        analyzer = TagAnalyzer()
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Environment': 'prod', 'Owner': 'team1'}},
                {'name': 'vm2', 'id': '/subs/1/vm2', 'tags': {'Environment': 'dev', 'CostCenter': 'cc1'}},
                {'name': 'vm3', 'id': '/subs/1/vm3', 'tags': {'Environment': 'prod'}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # Environment appears 3 times, Owner 1 time, CostCenter 1 time
        tag_usage = {item['tag_name']: item for item in result['tag_usage']}
        
        self.assertEqual(tag_usage['Environment']['usage_count'], 3)
        self.assertEqual(tag_usage['Owner']['usage_count'], 1)
        self.assertEqual(tag_usage['CostCenter']['usage_count'], 1)

    def test_findings_generation(self):
        """Test that findings are generated for compliance issues."""
        required_tags = ['Environment', 'Owner']
        analyzer = TagAnalyzer(required_tags=required_tags)
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {}},
                {'name': 'vm2', 'id': '/subs/1/vm2', 'tags': {}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # Should have findings for low compliance and resources without tags
        self.assertGreater(len(result['findings']), 0)
        
        # Check findings have required structure
        for finding in result['findings']:
            self.assertIn('resource', finding)
            self.assertIn('category', finding)
            self.assertIn('severity', finding)
            self.assertIn('issue', finding)
            self.assertIn('recommendation', finding)

    def test_findings_severity_levels(self):
        """Test that findings have appropriate severity based on compliance level."""
        required_tags = ['Environment']
        analyzer = TagAnalyzer(required_tags=required_tags)
        
        # Low compliance should generate high severity
        resources = {
            'virtual_machines': [
                {'name': f'vm{i}', 'id': f'/subs/1/vm{i}', 'tags': {}} 
                for i in range(10)
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # Should have high severity findings for very low compliance
        severities = [f['severity'] for f in result['findings']]
        self.assertTrue(any(s in ['high', 'critical'] for s in severities))

    def test_multiple_resource_types(self):
        """Test analyzing multiple resource types."""
        analyzer = TagAnalyzer(required_tags=['Environment'])
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Environment': 'prod'}}
            ],
            'storage_accounts': [
                {'name': 'storage1', 'id': '/subs/1/storage1', 'tags': {}}
            ],
            'virtual_networks': [
                {'name': 'vnet1', 'id': '/subs/1/vnet1', 'tags': {'Environment': 'dev'}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        self.assertEqual(result['summary']['total_resources'], 3)
        self.assertEqual(result['summary']['resources_with_tags'], 2)
        self.assertEqual(len(result['non_compliant_resources']), 1)

    def test_all_resources_integration(self):
        """Test with all_resources key (generic resources)."""
        analyzer = TagAnalyzer(required_tags=['Owner'])
        resources = {
            'all_resources': [
                {'name': 'res1', 'id': '/subs/1/res1', 'type': 'Microsoft.Web/sites', 'tags': {'Owner': 'team1'}},
                {'name': 'res2', 'id': '/subs/1/res2', 'type': 'Microsoft.Sql/servers', 'tags': {}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        self.assertEqual(result['summary']['total_resources'], 2)
        self.assertEqual(len(result['non_compliant_resources']), 1)


class TestTagAnalyzerEdgeCases(unittest.TestCase):
    """Test edge cases for TagAnalyzer."""

    def test_none_tags_value(self):
        """Test handling of None tags value."""
        analyzer = TagAnalyzer()
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': None}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        self.assertEqual(result['summary']['total_resources'], 1)
        self.assertEqual(result['summary']['resources_without_tags'], 1)

    def test_empty_tag_values(self):
        """Test handling of empty string tag values."""
        analyzer = TagAnalyzer()
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Environment': '', 'Owner': 'team1'}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # Empty values should still count as having the tag
        self.assertEqual(result['summary']['resources_with_tags'], 1)
        self.assertEqual(result['summary']['unique_tags_found'], 2)

    def test_non_dict_resources_skipped(self):
        """Test that non-dict resources are skipped."""
        analyzer = TagAnalyzer()
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Env': 'prod'}},
                "not_a_dict",
                None
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        self.assertEqual(result['summary']['total_resources'], 1)

    def test_non_list_resource_types_skipped(self):
        """Test that non-list resource types are skipped."""
        analyzer = TagAnalyzer()
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Env': 'prod'}}
            ],
            'some_string_value': 'not_a_list',
            'some_none_value': None
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        self.assertEqual(result['summary']['total_resources'], 1)

    def test_calculate_resource_compliance_no_required_tags(self):
        """Test compliance calculation with no required tags."""
        analyzer = TagAnalyzer()  # No required tags
        resource_tags = {'Environment', 'Owner'}
        
        compliance = analyzer._calculate_resource_compliance(resource_tags)
        
        # With no required tags, everything is 100% compliant
        self.assertEqual(compliance, 100.0)


if __name__ == '__main__':
    unittest.main()
