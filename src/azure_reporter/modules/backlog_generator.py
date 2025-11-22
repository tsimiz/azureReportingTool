"""Module for generating improvement backlog from analysis results."""

import logging
from typing import Dict, List, Any
import csv
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class BacklogGenerator:
    """Generates improvement backlog from Azure analysis results."""

    def __init__(self):
        """Initialize backlog generator."""
        self.backlog_items = []
        logger.info("Backlog generator initialized")

    def extract_backlog_items(self, analyses: Dict[str, Any]):
        """Extract backlog items from all analyses."""
        logger.info("Extracting backlog items from analyses...")
        
        resource_types = [
            'virtual_machines',
            'storage_accounts',
            'network_security_groups',
            'virtual_networks'
        ]
        
        item_id = 1
        
        for resource_type in resource_types:
            if resource_type not in analyses:
                continue
                
            analysis = analyses[resource_type]
            if 'findings' not in analysis:
                continue
            
            for finding in analysis['findings']:
                backlog_item = {
                    'id': f"ITEM-{item_id:04d}",
                    'resource_type': resource_type.replace('_', ' ').title(),
                    'resource_name': finding.get('resource', 'N/A'),
                    'category': finding.get('category', 'general').title(),
                    'severity': finding.get('severity', 'medium').upper(),
                    'issue': finding.get('issue', 'N/A'),
                    'recommendation': finding.get('recommendation', 'N/A'),
                    'status': 'Open',
                    'priority': self._calculate_priority(finding.get('severity', 'medium')),
                    'estimated_effort': self._estimate_effort(finding),
                    'created_date': datetime.now().strftime('%Y-%m-%d')
                }
                
                self.backlog_items.append(backlog_item)
                item_id += 1
        
        # Extract backlog items from generic resources
        if 'generic_resources' in analyses:
            generic_analysis = analyses['generic_resources']
            if 'resource_types' in generic_analysis:
                for resource_type, analysis in generic_analysis['resource_types'].items():
                    if 'findings' not in analysis:
                        continue
                    
                    # Use simplified resource type name
                    simple_type = resource_type.split('/')[-1] if '/' in resource_type else resource_type
                    
                    for finding in analysis['findings']:
                        backlog_item = {
                            'id': f"ITEM-{item_id:04d}",
                            'resource_type': simple_type,
                            'resource_name': finding.get('resource', 'N/A'),
                            'category': finding.get('category', 'general').title(),
                            'severity': finding.get('severity', 'medium').upper(),
                            'issue': finding.get('issue', 'N/A'),
                            'recommendation': finding.get('recommendation', 'N/A'),
                            'status': 'Open',
                            'priority': self._calculate_priority(finding.get('severity', 'medium')),
                            'estimated_effort': self._estimate_effort(finding),
                            'created_date': datetime.now().strftime('%Y-%m-%d')
                        }
                        
                        self.backlog_items.append(backlog_item)
                        item_id += 1
        
        # Sort by priority (1 is highest)
        self.backlog_items.sort(key=lambda x: x['priority'])
        
        logger.info(f"Extracted {len(self.backlog_items)} backlog items")

    def _calculate_priority(self, severity: str) -> int:
        """Calculate priority based on severity."""
        severity_map = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        }
        return severity_map.get(severity.lower(), 3)

    def _estimate_effort(self, finding: Dict[str, Any]) -> str:
        """Estimate effort required to address the finding."""
        severity = finding.get('severity', 'medium').lower()
        category = finding.get('category', 'general').lower()
        
        # Simple heuristic for effort estimation
        if category == 'security' and severity in ['critical', 'high']:
            return 'Medium'
        elif severity == 'critical':
            return 'High'
        elif severity == 'low':
            return 'Small'
        else:
            return 'Medium'

    def generate_csv_backlog(self, output_path: str):
        """Generate backlog as CSV file."""
        logger.info(f"Generating CSV backlog at {output_path}...")
        
        if not self.backlog_items:
            logger.warning("No backlog items to write")
            return
        
        fieldnames = [
            'id', 'priority', 'severity', 'status', 'resource_type',
            'resource_name', 'category', 'issue', 'recommendation',
            'estimated_effort', 'created_date'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.backlog_items)
        
        logger.info(f"CSV backlog saved to: {output_path}")

    def generate_json_backlog(self, output_path: str):
        """Generate backlog as JSON file."""
        logger.info(f"Generating JSON backlog at {output_path}...")
        
        if not self.backlog_items:
            logger.warning("No backlog items to write")
            return
        
        backlog_data = {
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_items': len(self.backlog_items),
            'items': self.backlog_items,
            'summary': self._generate_backlog_summary()
        }
        
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(backlog_data, jsonfile, indent=2)
        
        logger.info(f"JSON backlog saved to: {output_path}")

    def _generate_backlog_summary(self) -> Dict[str, Any]:
        """Generate summary statistics for the backlog."""
        summary = {
            'by_severity': {},
            'by_category': {},
            'by_resource_type': {},
            'by_priority': {}
        }
        
        for item in self.backlog_items:
            # Count by severity
            severity = item['severity']
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            
            # Count by category
            category = item['category']
            summary['by_category'][category] = summary['by_category'].get(category, 0) + 1
            
            # Count by resource type
            resource_type = item['resource_type']
            summary['by_resource_type'][resource_type] = summary['by_resource_type'].get(resource_type, 0) + 1
            
            # Count by priority
            priority = item['priority']
            summary['by_priority'][priority] = summary['by_priority'].get(priority, 0) + 1
        
        return summary

    def generate_markdown_backlog(self, output_path: str):
        """Generate backlog as Markdown file."""
        logger.info(f"Generating Markdown backlog at {output_path}...")
        
        if not self.backlog_items:
            logger.warning("No backlog items to write")
            return
        
        with open(output_path, 'w', encoding='utf-8') as mdfile:
            mdfile.write("# Azure Environment Improvement Backlog\n\n")
            mdfile.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            mdfile.write(f"Total Items: {len(self.backlog_items)}\n\n")
            
            # Write summary
            summary = self._generate_backlog_summary()
            mdfile.write("## Summary\n\n")
            
            mdfile.write("### By Severity\n")
            for severity, count in sorted(summary['by_severity'].items()):
                mdfile.write(f"- {severity}: {count}\n")
            mdfile.write("\n")
            
            mdfile.write("### By Category\n")
            for category, count in sorted(summary['by_category'].items()):
                mdfile.write(f"- {category}: {count}\n")
            mdfile.write("\n")
            
            # Write items grouped by priority
            mdfile.write("## Backlog Items\n\n")
            
            current_priority = None
            for item in self.backlog_items:
                if item['priority'] != current_priority:
                    current_priority = item['priority']
                    priority_name = ['Critical', 'High', 'Medium', 'Low'][current_priority - 1]
                    mdfile.write(f"### Priority {current_priority}: {priority_name}\n\n")
                
                mdfile.write(f"#### {item['id']} - {item['resource_name']}\n\n")
                mdfile.write(f"- **Severity**: {item['severity']}\n")
                mdfile.write(f"- **Resource Type**: {item['resource_type']}\n")
                mdfile.write(f"- **Category**: {item['category']}\n")
                mdfile.write(f"- **Issue**: {item['issue']}\n")
                mdfile.write(f"- **Recommendation**: {item['recommendation']}\n")
                mdfile.write(f"- **Estimated Effort**: {item['estimated_effort']}\n")
                mdfile.write(f"- **Status**: {item['status']}\n\n")
        
        logger.info(f"Markdown backlog saved to: {output_path}")

    def generate_all_formats(self, output_dir: str):
        """Generate backlog in all formats."""
        logger.info("Generating backlog in all formats...")
        
        self.generate_csv_backlog(f"{output_dir}/improvement_backlog.csv")
        self.generate_json_backlog(f"{output_dir}/improvement_backlog.json")
        self.generate_markdown_backlog(f"{output_dir}/improvement_backlog.md")
        
        logger.info("All backlog formats generated")
