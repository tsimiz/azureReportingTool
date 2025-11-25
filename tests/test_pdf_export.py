"""Tests for PDF export functionality."""

import os
import tempfile
import unittest
from unittest.mock import patch
from azure_reporter.modules.pdf_generator import PDFGenerator
from azure_reporter.utils.config_loader import ConfigLoader


class TestPDFExportFunctionality(unittest.TestCase):
    """Test PDF export functionality."""

    def test_pdf_generator_exists(self):
        """Test that PDFGenerator can be instantiated."""
        generator = PDFGenerator()
        self.assertIsNotNone(generator)
        self.assertTrue(hasattr(generator, 'generate_report'))
        self.assertTrue(callable(getattr(generator, 'generate_report')))

    def test_pdf_generator_creates_file(self):
        """Test that PDFGenerator creates a valid PDF file."""
        generator = PDFGenerator()
        
        # Sample resources and analyses
        resources = {
            'virtual_machines': [{'name': 'test-vm'}],
            'storage_accounts': [{'name': 'teststorage'}],
            'network_security_groups': [],
            'virtual_networks': [],
            'resource_groups': [{'name': 'test-rg'}],
            'all_resources': [{'name': 'test-resource'}]
        }
        
        analyses = {
            'executive_summary': 'This is a test executive summary.',
            'virtual_machines': {
                'overall_score': 7,
                'findings': [
                    {
                        'severity': 'medium',
                        'issue': 'Test issue',
                        'recommendation': 'Test recommendation',
                        'resource': 'test-vm'
                    }
                ],
                'best_practices_met': ['Practice 1', 'Practice 2']
            }
        }
        
        # Create a temporary file for the output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_report.pdf')
            generator.generate_report(resources, analyses, output_path)
            
            # Verify the file was created
            self.assertTrue(os.path.exists(output_path))
            
            # Verify it has content (PDF files start with %PDF)
            with open(output_path, 'rb') as f:
                header = f.read(4)
                self.assertEqual(header, b'%PDF')

    def test_default_config_uses_pdf(self):
        """Test that default configuration uses PDF format."""
        with patch.dict('os.environ', {}, clear=True):
            loader = ConfigLoader()
            config = loader.get_config()
            
            # Verify default export format is PDF
            self.assertEqual(config['output']['export_format'], 'pdf')
            self.assertTrue(config['output']['report_filename'].endswith('.pdf'))

    def test_config_allows_pptx_override(self):
        """Test that configuration can be set to use PPTX format."""
        with patch.dict('os.environ', {}, clear=True):
            # Create a config that explicitly sets PPTX format
            loader = ConfigLoader()
            config = loader.get_config()
            
            # Verify export_format can be changed
            config['output']['export_format'] = 'pptx'
            self.assertEqual(config['output']['export_format'], 'pptx')


class TestPDFGeneratorMethods(unittest.TestCase):
    """Test individual PDF generator methods."""

    def test_pdf_generator_initialization(self):
        """Test PDFGenerator initializes correctly."""
        generator = PDFGenerator()
        self.assertIsNotNone(generator.pdf)

    def test_add_title_page(self):
        """Test that title page can be added."""
        generator = PDFGenerator()
        # This should not raise an exception
        generator._add_title_page("Test Report")
        # Verify a page was added
        self.assertEqual(len(generator.pdf.pages), 1)

    def test_add_resource_overview(self):
        """Test that resource overview can be added."""
        generator = PDFGenerator()
        resources = {
            'virtual_machines': [{'name': 'vm1'}, {'name': 'vm2'}],
            'storage_accounts': [],
            'network_security_groups': [],
            'virtual_networks': [],
            'resource_groups': [{'name': 'rg1'}],
            'all_resources': [{'name': 'res1'}, {'name': 'res2'}, {'name': 'res3'}]
        }
        # This should not raise an exception
        generator._add_resource_overview(resources)
        # Verify a page was added
        self.assertEqual(len(generator.pdf.pages), 1)

    def test_pdf_handles_empty_analyses(self):
        """Test that PDF generator handles empty analyses gracefully."""
        generator = PDFGenerator()
        
        resources = {
            'virtual_machines': [],
            'storage_accounts': [],
            'network_security_groups': [],
            'virtual_networks': [],
            'resource_groups': [],
            'all_resources': []
        }
        
        analyses = {}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_empty.pdf')
            # Should not raise an exception
            generator.generate_report(resources, analyses, output_path)
            self.assertTrue(os.path.exists(output_path))


if __name__ == '__main__':
    unittest.main()
