"""Module for analyzing Azure resource tags against required tags."""

import logging
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)


class TagAnalyzer:
    """Analyzes Azure resource tags for compliance against required tags."""

    def __init__(self, required_tags: Optional[List[str]] = None, invalid_tag_values: Optional[List[str]] = None):
        """Initialize tag analyzer.
        
        Args:
            required_tags: List of tag names that are required on resources.
            invalid_tag_values: List of tag values that should be flagged as invalid/non-compliant.
        """
        self.required_tags = set(required_tags) if required_tags else set()
        # Normalize invalid values to lowercase for case-insensitive comparison
        # Convert to string first to handle non-string values safely
        self.invalid_tag_values = set(str(v).lower() if v is not None else "" for v in invalid_tag_values) if invalid_tag_values else set()
        logger.info(f"Tag analyzer initialized with {len(self.required_tags)} required tags and {len(self.invalid_tag_values)} invalid tag values")

    def _is_tag_value_valid(self, tag_value: Any) -> bool:
        """Check if a tag value is valid (not in the invalid values list).
        
        Args:
            tag_value: The tag value to check
            
        Returns:
            True if value is valid, False if invalid
        """
        if not self.invalid_tag_values:
            return True
        
        # Convert value to string and normalize to lowercase
        value_str = str(tag_value) if tag_value is not None else ""
        value_normalized = value_str.lower().strip()
        
        return value_normalized not in self.invalid_tag_values

    def analyze_resource_tags(self, resources: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Analyze tags across all resources.
        
        Args:
            resources: Dictionary of resource type to list of resources
            
        Returns:
            Dictionary containing tag analysis results
        """
        logger.info("Starting tag analysis...")
        
        all_tags: Dict[str, int] = {}  # tag_name -> count
        resources_with_tags = 0
        resources_without_tags = 0
        total_resources = 0
        
        # Track missing tags per resource
        missing_tags_by_resource: List[Dict[str, Any]] = []
        
        # Track tag usage
        tag_values: Dict[str, Dict[str, int]] = {}  # tag_name -> {value -> count}
        
        # Track resource groups and their tags
        resource_groups_info: Dict[str, Dict[str, Any]] = {}  # rg_name -> {tags, resources}
        
        # First, extract resource group information
        resource_groups_list = resources.get('resource_groups', [])
        for rg in resource_groups_list:
            if isinstance(rg, dict):
                rg_name = rg.get('name', 'Unknown')
                rg_tags = rg.get('tags', {}) or {}
                rg_tag_names = set(rg_tags.keys())
                
                # Check resource group compliance
                rg_missing_tags = list(self.required_tags - rg_tag_names) if self.required_tags else []
                
                # Check for invalid tag values on resource group required tags
                rg_invalid_value_tags = []
                for tag_name in self.required_tags:
                    if tag_name in rg_tags:
                        tag_value = rg_tags[tag_name]
                        if not self._is_tag_value_valid(tag_value):
                            rg_invalid_value_tags.append({
                                'tag_name': tag_name,
                                'tag_value': str(tag_value) if tag_value is not None else ""
                            })
                
                resource_groups_info[rg_name] = {
                    'name': rg_name,
                    'tags': rg_tags,
                    'existing_tags': list(rg_tag_names),
                    'missing_tags': rg_missing_tags,
                    'invalid_value_tags': rg_invalid_value_tags,
                    'compliance_rate': self._calculate_resource_compliance(rg_tag_names, rg_tags),
                    'resources': []
                }
        
        # Analyze each resource type
        for resource_type, resource_list in resources.items():
            if not isinstance(resource_list, list):
                continue
            
            # Skip resource_groups as we've already processed them
            # Skip all_resources as it's a duplicate collection
            if resource_type in ('resource_groups', 'all_resources'):
                continue
                
            for resource in resource_list:
                if not isinstance(resource, dict):
                    continue
                    
                total_resources += 1
                resource_tags = resource.get('tags', {}) or {}
                resource_group_name = resource.get('resource_group', 'N/A')
                
                if resource_tags:
                    resources_with_tags += 1
                else:
                    resources_without_tags += 1
                
                # Count tag usage
                for tag_name, tag_value in resource_tags.items():
                    all_tags[tag_name] = all_tags.get(tag_name, 0) + 1
                    
                    if tag_name not in tag_values:
                        tag_values[tag_name] = {}
                    tag_value_str = str(tag_value) if tag_value else "(empty)"
                    tag_values[tag_name][tag_value_str] = tag_values[tag_name].get(tag_value_str, 0) + 1
                
                # Check for missing required tags
                resource_tag_names = set(resource_tags.keys())
                missing = self.required_tags - resource_tag_names if self.required_tags else set()
                
                # Check for invalid tag values on required tags
                invalid_value_tags = []
                for tag_name in self.required_tags:
                    if tag_name in resource_tags:
                        tag_value = resource_tags[tag_name]
                        if not self._is_tag_value_valid(tag_value):
                            invalid_value_tags.append({
                                'tag_name': tag_name,
                                'tag_value': str(tag_value) if tag_value is not None else ""
                            })
                
                resource_info = {
                    'resource_type': resource_type,
                    'resource_name': resource.get('name', 'Unknown'),
                    'resource_id': resource.get('id', 'N/A'),
                    'resource_group': resource_group_name,
                    'existing_tags': list(resource_tag_names),
                    'missing_tags': list(missing),
                    'invalid_value_tags': invalid_value_tags,
                    'compliance_rate': self._calculate_resource_compliance(resource_tag_names, resource_tags)
                }
                
                if missing or invalid_value_tags:
                    missing_tags_by_resource.append(resource_info)
                
                # Add resource to its resource group
                if resource_group_name in resource_groups_info:
                    resource_groups_info[resource_group_name]['resources'].append(resource_info)
        
        # Build resource groups by compliance summary (before calculating overall compliance)
        resource_groups_by_compliance = self._build_resource_groups_summary(resource_groups_info)
        
        # Calculate compliance metrics (now includes resource groups)
        compliance_rate = self._calculate_overall_compliance(
            missing_tags_by_resource, 
            total_resources, 
            resource_groups_by_compliance
        )
        
        # Build tag summary
        tag_summary = []
        for tag_name, count in sorted(all_tags.items(), key=lambda x: -x[1]):
            tag_summary.append({
                'tag_name': tag_name,
                'usage_count': count,
                'usage_percentage': round(count / total_resources * 100, 1) if total_resources > 0 else 0,
                'is_required': tag_name in self.required_tags,
                'unique_values': len(tag_values.get(tag_name, {}))
            })
        
        # Build required tags compliance summary
        required_tags_summary = []
        for tag_name in self.required_tags:
            count = all_tags.get(tag_name, 0)
            required_tags_summary.append({
                'tag_name': tag_name,
                'compliant_resources': count,
                'non_compliant_resources': total_resources - count,
                'compliance_percentage': round(count / total_resources * 100, 1) if total_resources > 0 else 0
            })
        
        analysis_result = {
            'summary': {
                'total_resources': total_resources,
                'resources_with_tags': resources_with_tags,
                'resources_without_tags': resources_without_tags,
                'unique_tags_found': len(all_tags),
                'required_tags_count': len(self.required_tags),
                'overall_compliance_rate': compliance_rate,
                'total_resource_groups': len(resource_groups_info)
            },
            'tag_usage': tag_summary,
            'required_tags_compliance': required_tags_summary,
            'non_compliant_resources': missing_tags_by_resource,
            'resource_groups_details': resource_groups_by_compliance,
            'findings': self._generate_findings(
                missing_tags_by_resource, 
                compliance_rate, 
                resources_without_tags,
                total_resources
            )
        }
        
        logger.info(f"Tag analysis complete. Compliance rate: {compliance_rate}%")
        return analysis_result

    def _build_resource_groups_summary(
        self, 
        resource_groups_info: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build a summary of resource groups with their tag compliance.
        
        Args:
            resource_groups_info: Dictionary of resource group information
            
        Returns:
            List of resource groups with compliance details, sorted by compliance rate
        """
        summary = []
        for rg_name, rg_info in resource_groups_info.items():
            # Count non-compliant resources in this resource group
            non_compliant_count = sum(
                1 for res in rg_info['resources'] 
                if (res.get('missing_tags') and len(res['missing_tags']) > 0) or
                   (res.get('invalid_value_tags') and len(res['invalid_value_tags']) > 0)
            )
            
            # Calculate overall compliance for this resource group
            # This includes both the RG's own tag compliance and the compliance of resources within it
            rg_own_compliance = rg_info['compliance_rate']
            resources = rg_info['resources']
            
            if resources:
                # Calculate average compliance of all resources in this RG
                # compliance_rate is always present in resource_info from analyze_resource_tags
                resource_compliance_sum = sum(res['compliance_rate'] for res in resources)
                resource_avg_compliance = resource_compliance_sum / len(resources)
                
                # Overall RG compliance is the average of RG's own compliance and resources' average compliance
                overall_rg_compliance = (rg_own_compliance + resource_avg_compliance) / 2
            else:
                # If no resources, compliance is just the RG's own compliance
                overall_rg_compliance = rg_own_compliance
            
            summary.append({
                'name': rg_name,
                'tags': rg_info['tags'],
                'existing_tags': rg_info['existing_tags'],
                'missing_tags': rg_info['missing_tags'],
                'invalid_value_tags': rg_info.get('invalid_value_tags', []),
                'compliance_rate': round(overall_rg_compliance, 1),
                'total_resources': len(rg_info['resources']),
                'non_compliant_resources': non_compliant_count,
                'resources': rg_info['resources']
            })
        
        # Sort by compliance rate (ascending) to show worst first
        summary.sort(key=lambda x: x['compliance_rate'])
        return summary

    def _calculate_resource_compliance(self, resource_tag_names: Set[str], resource_tags: Dict[str, Any] = None) -> float:
        """Calculate compliance rate for a single resource.
        
        Args:
            resource_tag_names: Set of tag names on the resource
            resource_tags: Dictionary of tag names to values (optional, for value validation)
            
        Returns:
            Compliance rate as percentage (0-100)
        """
        if not self.required_tags:
            return 100.0
        
        # Count tags that are present AND have valid values
        compliant_tags = 0
        for tag_name in self.required_tags:
            if tag_name in resource_tag_names:
                # If we have tag values, check if the value is valid
                if resource_tags is not None:
                    if self._is_tag_value_valid(resource_tags.get(tag_name)):
                        compliant_tags += 1
                else:
                    # If no tag values provided, just check presence
                    compliant_tags += 1
        
        return round(compliant_tags / len(self.required_tags) * 100, 1)

    def _calculate_overall_compliance(
        self, 
        missing_tags_by_resource: List[Dict[str, Any]], 
        total_resources: int,
        resource_groups: List[Dict[str, Any]] = None
    ) -> float:
        """Calculate overall tag compliance rate.
        
        Args:
            missing_tags_by_resource: List of resources with missing tags
            total_resources: Total number of resources analyzed
            resource_groups: List of resource groups with their compliance details
            
        Returns:
            Overall compliance rate as percentage
        """
        if not self.required_tags:
            return 100.0
        
        # Calculate average compliance across all resources
        if total_resources == 0 and (not resource_groups or len(resource_groups) == 0):
            return 100.0
        
        total_compliance = 0
        total_items = 0
        
        # Add resource compliance
        if total_resources > 0:
            compliant_resources = total_resources - len(missing_tags_by_resource)
            partially_compliant = [r for r in missing_tags_by_resource if r['compliance_rate'] > 0]
            
            # Weight: fully compliant resources contribute 100%, partial contributes their rate
            total_compliance += (compliant_resources * 100)
            for resource in partially_compliant:
                total_compliance += resource['compliance_rate']
            
            total_items += total_resources
        
        # Add resource group compliance (resource groups themselves count as items)
        if resource_groups:
            for rg in resource_groups:
                # Use the RG's compliance rate (which already factors in its resources)
                # compliance_rate is always present from _build_resource_groups_summary
                total_compliance += rg['compliance_rate']
                total_items += 1
        
        if total_items == 0:
            return 100.0
        
        return round(total_compliance / total_items, 1)

    def _generate_findings(
        self, 
        missing_tags_by_resource: List[Dict[str, Any]],
        compliance_rate: float,
        resources_without_tags: int,
        total_resources: int
    ) -> List[Dict[str, Any]]:
        """Generate findings from tag analysis.
        
        Args:
            missing_tags_by_resource: List of resources with missing tags
            compliance_rate: Overall compliance rate
            resources_without_tags: Count of resources without any tags
            total_resources: Total number of resources
            
        Returns:
            List of findings
        """
        findings = []
        
        # Overall compliance finding
        if compliance_rate < 50:
            severity = 'high'
            issue = f"Tag compliance is critically low at {compliance_rate}%"
        elif compliance_rate < 80:
            severity = 'medium'
            issue = f"Tag compliance is below target at {compliance_rate}%"
        elif compliance_rate < 100:
            severity = 'low'
            issue = f"Tag compliance is good but not complete at {compliance_rate}%"
        else:
            severity = None
            
        if severity:
            findings.append({
                'resource': 'All Resources',
                'category': 'tagging',
                'severity': severity,
                'issue': issue,
                'recommendation': 'Implement a tagging policy to ensure all resources have required tags'
            })
        
        # Resources without any tags
        if resources_without_tags > 0:
            pct = round(resources_without_tags / total_resources * 100, 1) if total_resources > 0 else 0
            if pct > 25:
                severity = 'high'
            elif pct > 10:
                severity = 'medium'
            else:
                severity = 'low'
                
            findings.append({
                'resource': 'Multiple Resources',
                'category': 'tagging',
                'severity': severity,
                'issue': f"{resources_without_tags} resources ({pct}%) have no tags at all",
                'recommendation': 'Apply at minimum the required tags to all resources for proper cost allocation and management'
            })
        
        # Group missing tags by tag name to identify most common gaps
        tag_gaps: Dict[str, int] = {}
        for resource in missing_tags_by_resource:
            for tag in resource['missing_tags']:
                tag_gaps[tag] = tag_gaps.get(tag, 0) + 1
        
        # Report on most commonly missing tags
        for tag_name, count in sorted(tag_gaps.items(), key=lambda x: -x[1])[:5]:
            pct = round(count / total_resources * 100, 1) if total_resources > 0 else 0
            if pct > 50:
                severity = 'high'
            elif pct > 25:
                severity = 'medium'
            else:
                severity = 'low'
                
            findings.append({
                'resource': f"Tag: {tag_name}",
                'category': 'tagging',
                'severity': severity,
                'issue': f"Required tag '{tag_name}' is missing from {count} resources ({pct}%)",
                'recommendation': f"Apply the '{tag_name}' tag to all resources to improve compliance"
            })
        
        # Group invalid tag values by tag name
        invalid_value_gaps: Dict[str, int] = {}
        for resource in missing_tags_by_resource:
            for invalid_tag in resource.get('invalid_value_tags', []):
                tag_name = invalid_tag['tag_name']
                invalid_value_gaps[tag_name] = invalid_value_gaps.get(tag_name, 0) + 1
        
        # Report on most common invalid tag values
        for tag_name, count in sorted(invalid_value_gaps.items(), key=lambda x: -x[1])[:5]:
            pct = round(count / total_resources * 100, 1) if total_resources > 0 else 0
            if pct > 50:
                severity = 'high'
            elif pct > 25:
                severity = 'medium'
            else:
                severity = 'low'
                
            findings.append({
                'resource': f"Tag: {tag_name}",
                'category': 'tagging',
                'severity': severity,
                'issue': f"Required tag '{tag_name}' has invalid/non-compliant values on {count} resources ({pct}%)",
                'recommendation': f"Update the '{tag_name}' tag values to valid, meaningful values for proper compliance"
            })
        
        return findings
