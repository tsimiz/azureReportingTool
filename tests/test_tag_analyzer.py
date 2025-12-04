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
        resource_tag_names = {'Environment', 'Owner'}
        
        compliance = analyzer._calculate_resource_compliance(resource_tag_names, None)
        
        # With no required tags, everything is 100% compliant
        self.assertEqual(compliance, 100.0)


class TestTagAnalyzerInvalidValues(unittest.TestCase):
    """Test cases for invalid tag values feature."""

    def test_tag_analyzer_with_invalid_values(self):
        """Test TagAnalyzer initialization with invalid tag values."""
        invalid_values = ['none', 'na', 'n/a', '']
        analyzer = TagAnalyzer(invalid_tag_values=invalid_values)
        self.assertEqual(len(analyzer.invalid_tag_values), 4)
        # Should be normalized to lowercase
        self.assertIn('none', analyzer.invalid_tag_values)
        self.assertIn('na', analyzer.invalid_tag_values)

    def test_is_tag_value_valid(self):
        """Test tag value validation."""
        invalid_values = ['none', 'na', 'n/a', '', 'tbd']
        analyzer = TagAnalyzer(invalid_tag_values=invalid_values)
        
        # Valid values
        self.assertTrue(analyzer._is_tag_value_valid('production'))
        self.assertTrue(analyzer._is_tag_value_valid('dev'))
        self.assertTrue(analyzer._is_tag_value_valid('test'))
        
        # Invalid values (case-insensitive)
        self.assertFalse(analyzer._is_tag_value_valid('none'))
        self.assertFalse(analyzer._is_tag_value_valid('None'))
        self.assertFalse(analyzer._is_tag_value_valid('NONE'))
        self.assertFalse(analyzer._is_tag_value_valid('na'))
        self.assertFalse(analyzer._is_tag_value_valid('N/A'))
        self.assertFalse(analyzer._is_tag_value_valid(''))
        self.assertFalse(analyzer._is_tag_value_valid('tbd'))
        self.assertFalse(analyzer._is_tag_value_valid('TBD'))

    def test_analyze_resources_with_invalid_tag_values(self):
        """Test analyzing resources with invalid tag values."""
        required_tags = ['Environment', 'Owner']
        invalid_values = ['none', 'na', '']
        analyzer = TagAnalyzer(required_tags=required_tags, invalid_tag_values=invalid_values)
        
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Environment': 'none', 'Owner': 'team1'}},
                {'name': 'vm2', 'id': '/subs/1/vm2', 'tags': {'Environment': 'prod', 'Owner': 'na'}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # Both resources should be non-compliant
        self.assertEqual(len(result['non_compliant_resources']), 2)
        
        # Check first resource has invalid Environment value
        vm1 = next(r for r in result['non_compliant_resources'] if r['resource_name'] == 'vm1')
        self.assertEqual(len(vm1['invalid_value_tags']), 1)
        self.assertEqual(vm1['invalid_value_tags'][0]['tag_name'], 'Environment')
        self.assertEqual(vm1['invalid_value_tags'][0]['tag_value'], 'none')
        
        # Check second resource has invalid Owner value
        vm2 = next(r for r in result['non_compliant_resources'] if r['resource_name'] == 'vm2')
        self.assertEqual(len(vm2['invalid_value_tags']), 1)
        self.assertEqual(vm2['invalid_value_tags'][0]['tag_name'], 'Owner')

    def test_compliance_rate_with_invalid_values(self):
        """Test that compliance rate considers invalid tag values."""
        required_tags = ['Environment', 'Owner']
        invalid_values = ['none', 'na']
        analyzer = TagAnalyzer(required_tags=required_tags, invalid_tag_values=invalid_values)
        
        resources = {
            'virtual_machines': [
                # Fully compliant
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Environment': 'prod', 'Owner': 'team1'}},
                # One invalid value
                {'name': 'vm2', 'id': '/subs/1/vm2', 'tags': {'Environment': 'none', 'Owner': 'team2'}},
                # Both invalid values
                {'name': 'vm3', 'id': '/subs/1/vm3', 'tags': {'Environment': 'na', 'Owner': 'none'}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # vm1: 100% compliant
        # vm2: 50% compliant (1 of 2 tags valid)
        # vm3: 0% compliant (0 of 2 tags valid)
        # Overall: (100 + 50 + 0) / 3 = 50%
        self.assertEqual(result['summary']['overall_compliance_rate'], 50.0)

    def test_invalid_values_do_not_affect_missing_tags(self):
        """Test that invalid values checking doesn't interfere with missing tags."""
        required_tags = ['Environment', 'Owner', 'CostCenter']
        invalid_values = ['none']
        analyzer = TagAnalyzer(required_tags=required_tags, invalid_tag_values=invalid_values)
        
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Environment': 'none'}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        vm1 = result['non_compliant_resources'][0]
        # Should have missing tags: Owner and CostCenter
        self.assertEqual(len(vm1['missing_tags']), 2)
        self.assertIn('Owner', vm1['missing_tags'])
        self.assertIn('CostCenter', vm1['missing_tags'])
        
        # Should have invalid value tag: Environment
        self.assertEqual(len(vm1['invalid_value_tags']), 1)
        self.assertEqual(vm1['invalid_value_tags'][0]['tag_name'], 'Environment')

    def test_findings_include_invalid_values(self):
        """Test that findings are generated for invalid tag values."""
        required_tags = ['Environment']
        invalid_values = ['none']
        analyzer = TagAnalyzer(required_tags=required_tags, invalid_tag_values=invalid_values)
        
        resources = {
            'virtual_machines': [
                {'name': f'vm{i}', 'id': f'/subs/1/vm{i}', 'tags': {'Environment': 'none'}} 
                for i in range(10)
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # Should have findings about invalid values
        findings = result['findings']
        self.assertGreater(len(findings), 0)
        
        # Check if there's a finding about invalid tag values
        invalid_value_findings = [f for f in findings if 'invalid' in f['issue'].lower() or 'non-compliant values' in f['issue'].lower()]
        self.assertGreater(len(invalid_value_findings), 0)

    def test_no_invalid_values_configured(self):
        """Test that when no invalid values are configured, all values are valid."""
        required_tags = ['Environment']
        analyzer = TagAnalyzer(required_tags=required_tags)  # No invalid_tag_values
        
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Environment': 'none'}},
                {'name': 'vm2', 'id': '/subs/1/vm2', 'tags': {'Environment': 'na'}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # All resources should be compliant since no invalid values are configured
        self.assertEqual(result['summary']['overall_compliance_rate'], 100.0)
        self.assertEqual(len(result['non_compliant_resources']), 0)

    def test_empty_string_value_detection(self):
        """Test that empty string tag values are detected as invalid."""
        required_tags = ['Environment']
        invalid_values = ['']
        analyzer = TagAnalyzer(required_tags=required_tags, invalid_tag_values=invalid_values)
        
        resources = {
            'virtual_machines': [
                {'name': 'vm1', 'id': '/subs/1/vm1', 'tags': {'Environment': ''}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        self.assertEqual(len(result['non_compliant_resources']), 1)
        vm1 = result['non_compliant_resources'][0]
        self.assertEqual(len(vm1['invalid_value_tags']), 1)
        self.assertEqual(vm1['invalid_value_tags'][0]['tag_name'], 'Environment')

    def test_resource_groups_with_invalid_values(self):
        """Test that resource groups with invalid tag values are detected."""
        required_tags = ['Environment']
        invalid_values = ['none']
        analyzer = TagAnalyzer(required_tags=required_tags, invalid_tag_values=invalid_values)
        
        resources = {
            'resource_groups': [
                {'name': 'rg1', 'tags': {'Environment': 'none'}}
            ]
        }
        
        result = analyzer.analyze_resource_tags(resources)
        
        # Check resource groups details
        rg_details = result['resource_groups_details']
        self.assertEqual(len(rg_details), 1)
        
        rg1 = rg_details[0]
        self.assertEqual(len(rg1['invalid_value_tags']), 1)
        self.assertEqual(rg1['invalid_value_tags'][0]['tag_name'], 'Environment')
        self.assertEqual(rg1['invalid_value_tags'][0]['tag_value'], 'none')


if __name__ == '__main__':
    unittest.main()
