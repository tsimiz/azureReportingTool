"""Module for generating PowerPoint presentations from analysis results."""

import logging
from typing import Dict, List, Any
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

logger = logging.getLogger(__name__)


class PowerPointGenerator:
    """Generates PowerPoint presentations from Azure analysis results."""

    def __init__(self):
        """Initialize PowerPoint generator."""
        self.prs = Presentation()
        self.prs.slide_width = Inches(10)
        self.prs.slide_height = Inches(7.5)
        logger.info("PowerPoint generator initialized")

    def add_title_slide(self, title: str = "Azure Environment Analysis Report"):
        """Add title slide to presentation."""
        slide_layout = self.prs.slide_layouts[0]  # Title slide layout
        slide = self.prs.slides.add_slide(slide_layout)
        
        title_shape = slide.shapes.title
        subtitle_shape = slide.placeholders[1]
        
        title_shape.text = title
        subtitle_shape.text = "Comprehensive analysis against Microsoft best practices"
        
        logger.info("Added title slide")

    def add_executive_summary_slide(self, summary: str):
        """Add executive summary slide."""
        slide_layout = self.prs.slide_layouts[1]  # Title and Content layout
        slide = self.prs.slides.add_slide(slide_layout)
        
        title = slide.shapes.title
        title.text = "Executive Summary"
        
        content = slide.placeholders[1]
        text_frame = content.text_frame
        text_frame.clear()
        
        # Split summary into paragraphs
        paragraphs = summary.split('\n\n')
        for i, para in enumerate(paragraphs):
            if i > 0:
                p = text_frame.add_paragraph()
            else:
                p = text_frame.paragraphs[0]
            p.text = para.strip()
            p.font.size = Pt(12)
            p.level = 0
        
        logger.info("Added executive summary slide")

    def add_resource_overview_slide(self, resources: Dict[str, List[Dict[str, Any]]]):
        """Add resource overview slide with counts."""
        slide_layout = self.prs.slide_layouts[1]
        slide = self.prs.slides.add_slide(slide_layout)
        
        title = slide.shapes.title
        title.text = "Azure Environment Overview"
        
        content = slide.placeholders[1]
        text_frame = content.text_frame
        text_frame.clear()
        
        # Add resource counts
        resource_counts = [
            f"Resource Groups: {len(resources.get('resource_groups', []))}",
            f"Virtual Machines: {len(resources.get('virtual_machines', []))}",
            f"Storage Accounts: {len(resources.get('storage_accounts', []))}",
            f"Network Security Groups: {len(resources.get('network_security_groups', []))}",
            f"Virtual Networks: {len(resources.get('virtual_networks', []))}",
            f"Total Resources: {len(resources.get('all_resources', []))}"
        ]
        
        for i, count in enumerate(resource_counts):
            if i > 0:
                p = text_frame.add_paragraph()
            else:
                p = text_frame.paragraphs[0]
            p.text = count
            p.font.size = Pt(18)
            p.font.bold = True
            p.level = 0
        
        logger.info("Added resource overview slide")

    def add_findings_slide(self, resource_type: str, analysis: Dict[str, Any]):
        """Add slide for findings of a specific resource type."""
        if not analysis or 'findings' not in analysis or not analysis['findings']:
            return
        
        slide_layout = self.prs.slide_layouts[1]
        slide = self.prs.slides.add_slide(slide_layout)
        
        title = slide.shapes.title
        title.text = f"{resource_type.replace('_', ' ').title()} - Findings"
        
        # Add overall score if available
        content = slide.placeholders[1]
        text_frame = content.text_frame
        text_frame.clear()
        
        if 'overall_score' in analysis:
            score = analysis['overall_score']
            p = text_frame.paragraphs[0]
            p.text = f"Overall Score: {score}/10"
            p.font.size = Pt(16)
            p.font.bold = True
            
            # Color code the score
            if score >= 8:
                p.font.color.rgb = RGBColor(0, 128, 0)  # Green
            elif score >= 6:
                p.font.color.rgb = RGBColor(255, 165, 0)  # Orange
            else:
                p.font.color.rgb = RGBColor(255, 0, 0)  # Red
        
        # Add findings (limit to top 5 per slide)
        findings = analysis['findings'][:5]
        for finding in findings:
            p = text_frame.add_paragraph()
            severity = finding.get('severity', 'medium').upper()
            issue = finding.get('issue', 'N/A')
            p.text = f"[{severity}] {issue}"
            p.font.size = Pt(11)
            p.level = 1
            
            # Color code by severity
            if severity == 'CRITICAL':
                p.font.color.rgb = RGBColor(255, 0, 0)
            elif severity == 'HIGH':
                p.font.color.rgb = RGBColor(255, 140, 0)
            elif severity == 'MEDIUM':
                p.font.color.rgb = RGBColor(255, 215, 0)
        
        logger.info(f"Added findings slide for {resource_type}")

    def add_recommendations_slide(self, resource_type: str, analysis: Dict[str, Any]):
        """Add slide for recommendations of a specific resource type."""
        if not analysis or 'findings' not in analysis or not analysis['findings']:
            return
        
        slide_layout = self.prs.slide_layouts[1]
        slide = self.prs.slides.add_slide(slide_layout)
        
        title = slide.shapes.title
        title.text = f"{resource_type.replace('_', ' ').title()} - Recommendations"
        
        content = slide.placeholders[1]
        text_frame = content.text_frame
        text_frame.clear()
        
        # Add recommendations (limit to top 5 per slide)
        findings = analysis['findings'][:5]
        for i, finding in enumerate(findings):
            if i > 0:
                p = text_frame.add_paragraph()
            else:
                p = text_frame.paragraphs[0]
                
            resource = finding.get('resource', 'General')
            recommendation = finding.get('recommendation', 'N/A')
            p.text = f"{resource}: {recommendation}"
            p.font.size = Pt(11)
            p.level = 0
        
        logger.info(f"Added recommendations slide for {resource_type}")

    def add_best_practices_slide(self, resource_type: str, analysis: Dict[str, Any]):
        """Add slide for best practices met."""
        if not analysis or 'best_practices_met' not in analysis:
            return
        
        best_practices = analysis.get('best_practices_met', [])
        if not best_practices:
            return
        
        slide_layout = self.prs.slide_layouts[1]
        slide = self.prs.slides.add_slide(slide_layout)
        
        title = slide.shapes.title
        title.text = f"{resource_type.replace('_', ' ').title()} - Best Practices Met ✓"
        
        content = slide.placeholders[1]
        text_frame = content.text_frame
        text_frame.clear()
        
        for i, practice in enumerate(best_practices[:7]):
            if i > 0:
                p = text_frame.add_paragraph()
            else:
                p = text_frame.paragraphs[0]
            p.text = f"✓ {practice}"
            p.font.size = Pt(14)
            p.font.color.rgb = RGBColor(0, 128, 0)
            p.level = 0
        
        logger.info(f"Added best practices slide for {resource_type}")

    def add_summary_slide(self):
        """Add final summary slide."""
        slide_layout = self.prs.slide_layouts[1]
        slide = self.prs.slides.add_slide(slide_layout)
        
        title = slide.shapes.title
        title.text = "Next Steps"
        
        content = slide.placeholders[1]
        text_frame = content.text_frame
        text_frame.clear()
        
        next_steps = [
            "Review all critical and high-severity findings",
            "Prioritize security-related issues",
            "Review the improvement backlog",
            "Implement recommended changes systematically",
            "Schedule regular assessments",
            "Monitor ongoing compliance"
        ]
        
        for i, step in enumerate(next_steps):
            if i > 0:
                p = text_frame.add_paragraph()
            else:
                p = text_frame.paragraphs[0]
            p.text = f"{i+1}. {step}"
            p.font.size = Pt(14)
            p.level = 0
        
        logger.info("Added summary slide")

    def generate_report(self, resources: Dict[str, List[Dict[str, Any]]], 
                       analyses: Dict[str, Any], output_path: str):
        """Generate complete PowerPoint report."""
        logger.info("Generating PowerPoint report...")
        
        # Add slides
        self.add_title_slide()
        
        # Executive summary
        if 'executive_summary' in analyses:
            self.add_executive_summary_slide(analyses['executive_summary'])
        
        # Resource overview
        self.add_resource_overview_slide(resources)
        
        # Add slides for each resource type
        resource_types = [
            'virtual_machines',
            'storage_accounts', 
            'network_security_groups',
            'virtual_networks'
        ]
        
        for resource_type in resource_types:
            if resource_type in analyses:
                analysis = analyses[resource_type]
                self.add_findings_slide(resource_type, analysis)
                self.add_recommendations_slide(resource_type, analysis)
                self.add_best_practices_slide(resource_type, analysis)
        
        # Add slides for generic resources grouped by type
        if 'generic_resources' in analyses:
            generic_analysis = analyses['generic_resources']
            if 'resource_types' in generic_analysis:
                for resource_type, analysis in generic_analysis['resource_types'].items():
                    # Use simplified resource type name for slide title
                    simple_type = resource_type.split('/')[-1] if '/' in resource_type else resource_type
                    self.add_findings_slide(simple_type, analysis)
                    self.add_recommendations_slide(simple_type, analysis)
                    self.add_best_practices_slide(simple_type, analysis)
        
        # Final summary
        self.add_summary_slide()
        
        # Save presentation
        self.prs.save(output_path)
        logger.info(f"PowerPoint report saved to: {output_path}")
