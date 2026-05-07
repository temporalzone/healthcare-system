from django.test import TestCase
from unittest.mock import patch

from core.views import analyze_pdf_report


class AnalyzePdfReportTests(TestCase):
    @patch('core.views.PyPDF2.PdfReader')
    def test_generates_structured_multiline_analysis(self, mock_pdf_reader):
        fake_page = type('Page', (), {'extract_text': lambda self: 'Glucose high. Sugar high. Cholesterol high.'})()
        mock_pdf_reader.return_value.pages = [fake_page]

        analysis = analyze_pdf_report(file_obj=object())

        self.assertIn('Summary / Key findings:', analysis)
        self.assertIn('Detected flags:', analysis)
        self.assertIn('Why it matters (brief):', analysis)
        self.assertIn('Suggested next steps (non-diagnostic):', analysis)
        self.assertIn('Recommended follow-up tests / consult guidance:', analysis)
        self.assertIn('High blood sugar markers', analysis)
        self.assertIn('High cholesterol markers', analysis)
        self.assertIn('Safety note: This is an automated, non-diagnostic summary', analysis)
        self.assertIn('\n', analysis)

    @patch('core.views.PyPDF2.PdfReader')
    def test_returns_structured_response_when_no_flags_detected(self, mock_pdf_reader):
        fake_page = type('Page', (), {'extract_text': lambda self: 'Routine values noted. Within reference range.'})()
        mock_pdf_reader.return_value.pages = [fake_page]

        analysis = analyze_pdf_report(file_obj=object())

        self.assertIn('No explicit high-risk marker terms were detected.', analysis)
        self.assertIn('No specific high/low marker combinations were detected', analysis)

    @patch('core.views.PyPDF2.PdfReader', side_effect=Exception('bad-pdf'))
    def test_handles_reader_exceptions(self, _mock_pdf_reader):
        self.assertEqual(analyze_pdf_report(file_obj=object()), 'Could not auto-analyze.')
