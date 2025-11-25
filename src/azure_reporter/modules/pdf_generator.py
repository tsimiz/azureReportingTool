"""Module for generating PDF reports from analysis results."""

import logging
from typing import Dict, List, Any
from fpdf import FPDF
from fpdf.enums import XPos, YPos

logger = logging.getLogger(__name__)


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
        findings = analysis['findings'][:10]  # Limit to 10 findings per section
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
            
            self.pdf.cell(0, 8, f"[{severity}] {issue[:80]}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            
            # Add recommendation if available
            recommendation = finding.get('recommendation', '')
            if recommendation:
                self.pdf.set_font('Helvetica', '', 9)
                self.pdf.set_text_color(60, 60, 60)
                self.pdf.multi_cell(0, 5, f"  Recommendation: {recommendation[:150]}")
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
        
        for practice in best_practices[:7]:
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
