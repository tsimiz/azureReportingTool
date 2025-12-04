"""Module for generating PDF reports from analysis results."""

import logging
from typing import Dict, List, Any
from fpdf import FPDF
from fpdf.enums import XPos, YPos

logger = logging.getLogger(__name__)

# Constants for text and content limits
MAX_FINDINGS_PER_SECTION = 10
MAX_BEST_PRACTICES_PER_SECTION = 7
MAX_ISSUE_TEXT_LENGTH = 80
MAX_RECOMMENDATION_TEXT_LENGTH = 150
MAX_RESOURCE_GROUPS_IN_PDF = 10
MAX_RESOURCES_PER_GROUP_IN_PDF = 3


class AzureReportPDF(FPDF):
    """Custom FPDF class with header and footer."""

    def __init__(self):
        """Initialize the PDF with custom settings."""
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        """Add header to each page."""
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'Azure Environment Analysis Report', align='C')
        self.ln(15)

    def footer(self):
        """Add footer with page number to each page."""
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


class PDFGenerator:
    """Generates PDF reports from Azure analysis results."""

    def __init__(self):
        """Initialize PDF generator."""
        self.pdf = AzureReportPDF()
        self.pdf.set_margins(20, 20, 20)
        logger.info("PDF generator initialized")

    def _add_title_page(self, title: str = "Azure Environment Analysis Report"):
        """Add title page to the report."""
        self.pdf.add_page()
        self.pdf.set_font('Helvetica', 'B', 24)
        self.pdf.set_text_color(0, 51, 102)  # Dark blue
        self.pdf.ln(40)
        self.pdf.cell(0, 20, title, align='C')
        self.pdf.ln(20)
        self.pdf.set_font('Helvetica', '', 14)
        self.pdf.set_text_color(80, 80, 80)
        self.pdf.cell(0, 10, "Comprehensive analysis against Microsoft best practices", align='C')
        logger.info("Added title page")

    def _add_executive_summary(self, summary: str):
        """Add executive summary section."""
        self.pdf.add_page()
        self.pdf.set_font('Helvetica', 'B', 18)
        self.pdf.set_text_color(0, 51, 102)
        self.pdf.cell(0, 15, "Executive Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.ln(5)
        
        self.pdf.set_font('Helvetica', '', 11)
        self.pdf.set_text_color(0, 0, 0)
        
        # Split summary into paragraphs and add them
        paragraphs = summary.split('\n\n')
        for para in paragraphs:
            clean_para = para.strip()
            if clean_para:
                self.pdf.multi_cell(0, 6, clean_para)
                self.pdf.ln(4)
        
        logger.info("Added executive summary")

    def _add_resource_overview(self, resources: Dict[str, List[Dict[str, Any]]]):
        """Add resource overview section."""
        self.pdf.add_page()
        self.pdf.set_font('Helvetica', 'B', 18)
        self.pdf.set_text_color(0, 51, 102)
        self.pdf.cell(0, 15, "Azure Environment Overview", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.ln(5)
        
        resource_counts = [
            ("Resource Groups", len(resources.get('resource_groups', []))),
            ("Virtual Machines", len(resources.get('virtual_machines', []))),
            ("Storage Accounts", len(resources.get('storage_accounts', []))),
            ("Network Security Groups", len(resources.get('network_security_groups', []))),
            ("Virtual Networks", len(resources.get('virtual_networks', []))),
            ("Total Resources", len(resources.get('all_resources', [])))
        ]
        
        self.pdf.set_font('Helvetica', 'B', 12)
        self.pdf.set_text_color(0, 0, 0)
        
        for name, count in resource_counts:
            self.pdf.cell(0, 10, f"{name}: {count}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        logger.info("Added resource overview")

    def _add_tag_analysis_section(self, tag_analysis: Dict[str, Any]):
        """Add tag compliance analysis section."""
        self.pdf.add_page()
        
        # Section title
        self.pdf.set_font('Helvetica', 'B', 18)
        self.pdf.set_text_color(0, 51, 102)
        self.pdf.cell(0, 15, "Tag Compliance Analysis", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.ln(5)
        
        summary = tag_analysis.get('summary', {})
        
        # Compliance overview
        compliance_rate = summary.get('overall_compliance_rate', 0)
        self.pdf.set_font('Helvetica', 'B', 14)
        
        if compliance_rate >= 90:
            self.pdf.set_text_color(0, 128, 0)  # Green
        elif compliance_rate >= 70:
            self.pdf.set_text_color(255, 140, 0)  # Orange
        else:
            self.pdf.set_text_color(255, 0, 0)  # Red
        
        self.pdf.cell(0, 10, f"Overall Tag Compliance: {compliance_rate}%", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.ln(3)
        
        # Summary stats
        self.pdf.set_font('Helvetica', '', 11)
        self.pdf.set_text_color(0, 0, 0)
        
        stats = [
            f"Total Resources Analyzed: {summary.get('total_resources', 0)}",
            f"Resources with Tags: {summary.get('resources_with_tags', 0)}",
            f"Resources without Tags: {summary.get('resources_without_tags', 0)}",
            f"Unique Tags Found: {summary.get('unique_tags_found', 0)}",
            f"Required Tags: {summary.get('required_tags_count', 0)}"
        ]
        
        for stat in stats:
            self.pdf.cell(0, 8, stat, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.pdf.ln(5)
        
        # Required tags compliance
        required_tags_compliance = tag_analysis.get('required_tags_compliance', [])
        if required_tags_compliance:
            self.pdf.set_font('Helvetica', 'B', 14)
            self.pdf.set_text_color(0, 51, 102)
            self.pdf.cell(0, 12, "Required Tags Compliance", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.pdf.ln(2)
            
            self.pdf.set_font('Helvetica', '', 10)
            for tag_info in required_tags_compliance:
                tag_name = tag_info.get('tag_name', 'Unknown')
                tag_compliance = tag_info.get('compliance_percentage', 0)
                non_compliant = tag_info.get('non_compliant_resources', 0)
                
                if tag_compliance >= 90:
                    self.pdf.set_text_color(0, 128, 0)
                elif tag_compliance >= 70:
                    self.pdf.set_text_color(255, 140, 0)
                else:
                    self.pdf.set_text_color(255, 0, 0)
                
                self.pdf.cell(0, 7, f"  {tag_name}: {tag_compliance}% compliant ({non_compliant} missing)", 
                             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            self.pdf.ln(3)
        
        # Tag findings
        findings = tag_analysis.get('findings', [])
        if findings:
            self.pdf.set_font('Helvetica', 'B', 14)
            self.pdf.set_text_color(0, 51, 102)
            self.pdf.cell(0, 12, "Tag Compliance Findings", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.pdf.ln(2)
            
            for finding in findings[:MAX_FINDINGS_PER_SECTION]:
                severity = finding.get('severity', 'medium').upper()
                issue = finding.get('issue', 'N/A')
                
                self.pdf.set_font('Helvetica', 'B', 10)
                
                if severity == 'HIGH':
                    self.pdf.set_text_color(255, 140, 0)
                elif severity == 'MEDIUM':
                    self.pdf.set_text_color(200, 150, 0)
                else:
                    self.pdf.set_text_color(100, 100, 100)
                
                self.pdf.cell(0, 8, f"[{severity}] {issue[:MAX_ISSUE_TEXT_LENGTH]}", 
                             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                
                recommendation = finding.get('recommendation', '')
                if recommendation:
                    self.pdf.set_font('Helvetica', '', 9)
                    self.pdf.set_text_color(60, 60, 60)
                    self.pdf.multi_cell(0, 5, f"  Recommendation: {recommendation[:MAX_RECOMMENDATION_TEXT_LENGTH]}")
                    self.pdf.ln(2)
        
        # Resource groups tag compliance
        resource_groups_details = tag_analysis.get('resource_groups_details', [])
        if resource_groups_details:
            # Check if we need a new page
            if self.pdf.get_y() > 200:
                self.pdf.add_page()
            
            self.pdf.set_font('Helvetica', 'B', 14)
            self.pdf.set_text_color(0, 51, 102)
            self.pdf.cell(0, 12, "Tag Compliance by Resource Group", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.pdf.ln(2)
            
            # Show first N resource groups
            for rg in resource_groups_details[:MAX_RESOURCE_GROUPS_IN_PDF]:
                # Check if we need a new page
                if self.pdf.get_y() > 240:
                    self.pdf.add_page()
                
                rg_name = rg.get('name', 'Unknown')
                rg_compliance = rg.get('compliance_rate', 0)
                rg_missing_tags = rg.get('missing_tags', [])
                non_compliant_resources = rg.get('non_compliant_resources', 0)
                total_resources = rg.get('total_resources', 0)
                resources = rg.get('resources', [])
                
                # Resource group name
                self.pdf.set_font('Helvetica', 'B', 11)
                if rg_compliance >= 90:
                    self.pdf.set_text_color(0, 128, 0)
                elif rg_compliance >= 70:
                    self.pdf.set_text_color(255, 140, 0)
                else:
                    self.pdf.set_text_color(255, 0, 0)
                
                self.pdf.cell(0, 8, f"{rg_name} - {rg_compliance}% compliant", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                
                # Resource group tags status
                self.pdf.set_font('Helvetica', '', 9)
                if rg_missing_tags:
                    self.pdf.set_text_color(255, 0, 0)
                    missing_str = ', '.join(rg_missing_tags)
                    self.pdf.cell(0, 6, f"  RG Missing Tags: {missing_str}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                else:
                    self.pdf.set_text_color(0, 128, 0)
                    self.pdf.cell(0, 6, "  RG Tags: All required tags present", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                
                # Resource summary
                self.pdf.set_text_color(100, 100, 100)
                self.pdf.cell(0, 6, f"  Resources: {non_compliant_resources} of {total_resources} non-compliant", 
                             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                
                # Show all resources in this group (already sorted: non-compliant first, then compliant)
                if resources:
                    self.pdf.set_font('Helvetica', '', 8)
                    
                    # Show up to MAX_RESOURCES_PER_GROUP_IN_PDF*2 resources to include both non-compliant and compliant
                    max_to_show = min(len(resources), MAX_RESOURCES_PER_GROUP_IN_PDF * 2)
                    
                    for resource in resources[:max_to_show]:
                        # Check if we need a new page
                        if self.pdf.get_y() > 260:
                            self.pdf.add_page()
                        
                        resource_name = resource.get('resource_name', 'Unknown')
                        resource_type = resource.get('resource_type', 'Unknown')
                        compliance = resource.get('compliance_rate', 0)
                        tags = resource.get('tags', {})
                        missing = resource.get('missing_tags', [])
                        invalid_value_tags = resource.get('invalid_value_tags', [])
                        
                        # Color code based on compliance
                        if compliance == 100.0:
                            status_icon = "[OK]"
                            self.pdf.set_text_color(0, 128, 0)  # Green
                        else:
                            status_icon = "[X]"
                            self.pdf.set_text_color(255, 0, 0)  # Red
                        
                        # Resource name with status
                        self.pdf.cell(0, 5, f"    {status_icon} {resource_name} ({resource_type})", 
                                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                        
                        # Show tags
                        self.pdf.set_text_color(0, 0, 0)
                        if tags:
                            tags_str = ", ".join([f"{k}={v}" for k, v in list(tags.items())[:3]])
                            if len(tags) > 3:
                                tags_str += f" (+{len(tags) - 3} more)"
                            self.pdf.cell(0, 4, f"      Tags: {tags_str}", 
                                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                        else:
                            self.pdf.set_text_color(255, 0, 0)
                            self.pdf.cell(0, 4, "      Tags: None", 
                                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                            self.pdf.set_text_color(0, 0, 0)
                        
                        # Show issues if any
                        if missing:
                            self.pdf.set_text_color(255, 0, 0)
                            missing_str = ', '.join(missing[:3])
                            if len(missing) > 3:
                                missing_str += f" (+{len(missing) - 3} more)"
                            self.pdf.cell(0, 4, f"      Missing: {missing_str}", 
                                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                            self.pdf.set_text_color(0, 0, 0)
                        
                        if invalid_value_tags:
                            self.pdf.set_text_color(255, 0, 0)
                            invalid_str = ", ".join([f"{t['tag_name']}={t['tag_value']}" for t in invalid_value_tags[:2]])
                            if len(invalid_value_tags) > 2:
                                invalid_str += f" (+{len(invalid_value_tags) - 2} more)"
                            self.pdf.cell(0, 4, f"      Invalid: {invalid_str}", 
                                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                            self.pdf.set_text_color(0, 0, 0)
                    
                    if len(resources) > max_to_show:
                        self.pdf.set_text_color(100, 100, 100)
                        self.pdf.cell(0, 5, f"    ... and {len(resources) - max_to_show} more resources", 
                                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                        self.pdf.set_text_color(0, 0, 0)
                
                self.pdf.ln(2)
            
            if len(resource_groups_details) > MAX_RESOURCE_GROUPS_IN_PDF:
                self.pdf.set_font('Helvetica', 'I', 9)
                self.pdf.set_text_color(100, 100, 100)
                self.pdf.cell(0, 6, f"... and {len(resource_groups_details) - MAX_RESOURCE_GROUPS_IN_PDF} more resource groups", 
                             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Non-compliant resources (show first 10)
        non_compliant = tag_analysis.get('non_compliant_resources', [])
        if non_compliant:
            # Check if we need a new page
            if self.pdf.get_y() > 200:
                self.pdf.add_page()
            
            self.pdf.set_font('Helvetica', 'B', 14)
            self.pdf.set_text_color(0, 51, 102)
            self.pdf.cell(0, 12, f"All Non-Compliant Resources (showing {min(10, len(non_compliant))} of {len(non_compliant)})", 
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.pdf.ln(2)
            
            self.pdf.set_font('Helvetica', '', 9)
            self.pdf.set_text_color(0, 0, 0)
            
            for resource in non_compliant[:10]:
                resource_name = resource.get('resource_name', 'Unknown')
                resource_type = resource.get('resource_type', 'Unknown')
                resource_group = resource.get('resource_group', 'N/A')
                missing = resource.get('missing_tags', [])
                compliance = resource.get('compliance_rate', 0)
                
                self.pdf.set_font('Helvetica', 'B', 9)
                self.pdf.cell(0, 7, f"  {resource_name} ({resource_type})", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                
                self.pdf.set_font('Helvetica', '', 8)
                self.pdf.set_text_color(100, 100, 100)
                self.pdf.cell(0, 5, f"    Resource Group: {resource_group}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                
                missing_str = ', '.join(missing[:5])
                if len(missing) > 5:
                    missing_str += f" (+{len(missing) - 5} more)"
                self.pdf.cell(0, 5, f"    Missing: {missing_str} | Compliance: {compliance}%", 
                             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                self.pdf.set_text_color(0, 0, 0)
        
        logger.info("Added tag analysis section")

    def _add_cost_analysis_section(self, cost_analysis: Dict[str, Any]):
        """Add cost analysis and optimization recommendations section."""
        self.pdf.add_page()
        
        # Section title
        self.pdf.set_font('Helvetica', 'B', 18)
        self.pdf.set_text_color(0, 51, 102)
        self.pdf.cell(0, 15, "Cost Analysis & Optimization", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.ln(5)
        
        summary = cost_analysis.get('summary', {})
        opportunities = cost_analysis.get('optimization_opportunities', {})
        
        # Cost optimization summary
        total_findings = summary.get('total_findings', 0)
        self.pdf.set_font('Helvetica', 'B', 14)
        
        if total_findings == 0:
            self.pdf.set_text_color(0, 128, 0)  # Green
            self.pdf.cell(0, 10, "No immediate cost optimization opportunities identified", 
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            self.pdf.set_text_color(255, 140, 0)  # Orange
            self.pdf.cell(0, 10, f"Found {total_findings} cost optimization opportunities", 
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.ln(3)
        
        # Summary stats
        self.pdf.set_font('Helvetica', '', 11)
        self.pdf.set_text_color(0, 0, 0)
        
        stats = [
            f"Resources Analyzed: {summary.get('total_resources_analyzed', 0)}",
            f"Immediate Actions Needed: {opportunities.get('immediate_actions', 0)}",
            f"Reviews Recommended: {opportunities.get('review_needed', 0)}",
            f"Best Practice Suggestions: {opportunities.get('best_practices', 0)}"
        ]
        
        for stat in stats:
            self.pdf.cell(0, 8, stat, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.pdf.ln(5)
        
        # Optimization recommendations
        recommendations = cost_analysis.get('recommendations', [])
        if recommendations:
            self.pdf.set_font('Helvetica', 'B', 14)
            self.pdf.set_text_color(0, 51, 102)
            self.pdf.cell(0, 12, "Top Optimization Recommendations", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.pdf.ln(2)
            
            for i, rec in enumerate(recommendations[:5]):  # Top 5 recommendations
                self.pdf.set_font('Helvetica', 'B', 11)
                priority = rec.get('priority', 99)
                affected = rec.get('affected_resources', 0)
                
                if priority <= 2:
                    self.pdf.set_text_color(255, 0, 0)  # Red for high priority
                elif priority <= 4:
                    self.pdf.set_text_color(255, 140, 0)  # Orange
                else:
                    self.pdf.set_text_color(0, 100, 0)  # Green
                
                self.pdf.cell(0, 8, f"{i+1}. {rec.get('summary', 'N/A')[:70]}", 
                             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                
                self.pdf.set_font('Helvetica', '', 10)
                self.pdf.set_text_color(60, 60, 60)
                action = rec.get('action', '')[:100]
                self.pdf.multi_cell(0, 5, f"   Action: {action}")
                
                impact = rec.get('potential_impact', '')
                if impact:
                    self.pdf.cell(0, 5, f"   Potential Savings: {impact[:60]}", 
                                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                
                self.pdf.cell(0, 5, f"   Affected Resources: {affected}", 
                             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                self.pdf.ln(3)
        
        # Cost findings by severity
        findings = cost_analysis.get('findings', [])
        if findings:
            # Check if we need a new page
            if self.pdf.get_y() > 200:
                self.pdf.add_page()
            
            self.pdf.set_font('Helvetica', 'B', 14)
            self.pdf.set_text_color(0, 51, 102)
            self.pdf.cell(0, 12, f"Cost Findings (showing {min(10, len(findings))} of {len(findings)})", 
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.pdf.ln(2)
            
            for finding in findings[:MAX_FINDINGS_PER_SECTION]:
                severity = finding.get('severity', 'low').upper()
                issue = finding.get('issue', 'N/A')
                resource = finding.get('resource', 'Unknown')
                
                self.pdf.set_font('Helvetica', 'B', 10)
                
                if severity == 'HIGH':
                    self.pdf.set_text_color(255, 0, 0)
                elif severity == 'MEDIUM':
                    self.pdf.set_text_color(255, 140, 0)
                else:
                    self.pdf.set_text_color(100, 100, 100)
                
                self.pdf.cell(0, 7, f"[{severity}] {resource}: {issue[:60]}", 
                             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                
                recommendation = finding.get('recommendation', '')
                if recommendation:
                    self.pdf.set_font('Helvetica', '', 9)
                    self.pdf.set_text_color(60, 60, 60)
                    self.pdf.multi_cell(0, 5, f"  -> {recommendation[:100]}")
                
                self.pdf.ln(2)
        
        logger.info("Added cost analysis section")

    def _add_findings_section(self, resource_type: str, analysis: Dict[str, Any]):
        """Add findings section for a specific resource type."""
        if not analysis or 'findings' not in analysis or not analysis['findings']:
            return
        
        self.pdf.add_page()
        
        # Section title
        display_name = resource_type.replace('_', ' ').title()
        self.pdf.set_font('Helvetica', 'B', 16)
        self.pdf.set_text_color(0, 51, 102)
        self.pdf.cell(0, 12, f"{display_name} - Findings", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.ln(3)
        
        # Overall score if available
        if 'overall_score' in analysis:
            score = analysis['overall_score']
            self.pdf.set_font('Helvetica', 'B', 12)
            
            if score >= 8:
                self.pdf.set_text_color(0, 128, 0)  # Green
            elif score >= 6:
                self.pdf.set_text_color(255, 140, 0)  # Orange
            else:
                self.pdf.set_text_color(255, 0, 0)  # Red
            
            self.pdf.cell(0, 10, f"Overall Score: {score}/10", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.pdf.ln(3)
        
        # Findings
        findings = analysis['findings'][:MAX_FINDINGS_PER_SECTION]
        for finding in findings:
            severity = finding.get('severity', 'medium').upper()
            issue = finding.get('issue', 'N/A')
            
            self.pdf.set_font('Helvetica', 'B', 10)
            
            if severity == 'CRITICAL':
                self.pdf.set_text_color(255, 0, 0)
            elif severity == 'HIGH':
                self.pdf.set_text_color(255, 140, 0)
            elif severity == 'MEDIUM':
                self.pdf.set_text_color(200, 150, 0)
            else:
                self.pdf.set_text_color(100, 100, 100)
            
            self.pdf.cell(0, 8, f"[{severity}] {issue[:MAX_ISSUE_TEXT_LENGTH]}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Add recommendation if available
            recommendation = finding.get('recommendation', '')
            if recommendation:
                self.pdf.set_font('Helvetica', '', 9)
                self.pdf.set_text_color(60, 60, 60)
                self.pdf.multi_cell(0, 5, f"  Recommendation: {recommendation[:MAX_RECOMMENDATION_TEXT_LENGTH]}")
                self.pdf.ln(2)
        
        logger.info(f"Added findings section for {resource_type}")

    def _add_best_practices_section(self, resource_type: str, analysis: Dict[str, Any]):
        """Add best practices met section."""
        if not analysis or 'best_practices_met' not in analysis:
            return
        
        best_practices = analysis.get('best_practices_met', [])
        if not best_practices:
            return
        
        display_name = resource_type.replace('_', ' ').title()
        self.pdf.set_font('Helvetica', 'B', 14)
        self.pdf.set_text_color(0, 128, 0)
        self.pdf.cell(0, 10, f"{display_name} - Best Practices Met", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.ln(2)
        
        self.pdf.set_font('Helvetica', '', 10)
        self.pdf.set_text_color(0, 100, 0)
        
        for practice in best_practices[:MAX_BEST_PRACTICES_PER_SECTION]:
            self.pdf.cell(0, 7, f"  {practice}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.pdf.ln(5)
        logger.info(f"Added best practices section for {resource_type}")

    def _add_summary_page(self):
        """Add final summary page with next steps."""
        self.pdf.add_page()
        self.pdf.set_font('Helvetica', 'B', 18)
        self.pdf.set_text_color(0, 51, 102)
        self.pdf.cell(0, 15, "Next Steps", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.ln(5)
        
        next_steps = [
            "1. Review all critical and high-severity findings",
            "2. Prioritize security-related issues",
            "3. Review the improvement backlog",
            "4. Implement recommended changes systematically",
            "5. Schedule regular assessments",
            "6. Monitor ongoing compliance"
        ]
        
        self.pdf.set_font('Helvetica', '', 12)
        self.pdf.set_text_color(0, 0, 0)
        
        for step in next_steps:
            self.pdf.cell(0, 10, step, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        logger.info("Added summary page")

    def generate_report(self, resources: Dict[str, List[Dict[str, Any]]], 
                       analyses: Dict[str, Any], output_path: str):
        """Generate complete PDF report."""
        logger.info("Generating PDF report...")
        
        # Add title page
        self._add_title_page()
        
        # Executive summary
        if 'executive_summary' in analyses:
            self._add_executive_summary(analyses['executive_summary'])
        
        # Resource overview
        self._add_resource_overview(resources)
        
        # Tag analysis section (if available)
        if 'tag_analysis' in analyses:
            self._add_tag_analysis_section(analyses['tag_analysis'])
        
        # Cost analysis section (if available)
        if 'cost_analysis' in analyses:
            self._add_cost_analysis_section(analyses['cost_analysis'])
        
        # Add sections for each resource type
        resource_types = [
            'virtual_machines',
            'storage_accounts',
            'network_security_groups',
            'virtual_networks'
        ]
        
        for resource_type in resource_types:
            if resource_type in analyses:
                analysis = analyses[resource_type]
                self._add_findings_section(resource_type, analysis)
                self._add_best_practices_section(resource_type, analysis)
        
        # Add sections for generic resources grouped by type
        if 'generic_resources' in analyses:
            generic_analysis = analyses['generic_resources']
            if 'resource_types' in generic_analysis:
                for resource_type, analysis in generic_analysis['resource_types'].items():
                    simple_type = resource_type.split('/')[-1] if '/' in resource_type else resource_type
                    self._add_findings_section(simple_type, analysis)
                    self._add_best_practices_section(simple_type, analysis)
        
        # Final summary
        self._add_summary_page()
        
        # Save PDF
        self.pdf.output(output_path)
        logger.info(f"PDF report saved to: {output_path}")
