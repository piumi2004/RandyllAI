import unittest
from decimal import Decimal
from unittest.mock import patch

from backend.structured_retrieval import (
    retrieve_structured_evidence, format_database_records, is_agency_service_question,
)


class StructuredRetrievalTests(unittest.TestCase):
    def test_general_intakes_keep_scope_and_page_references(self):
        row = {"source_document": "report.pdf", "source_pages": [2, 3, 4], "intake_month": 3}
        with patch("backend.structured_retrieval.get_general_intakes", return_value=[row]) as general:
            evidence = retrieve_structured_evidence("University intakes and addmission periods")
        general.assert_called_once()
        self.assertIn("not university-specific", evidence["context"])
        self.assertEqual(evidence["sources"][0]["page"], "2, 3, 4")

    def test_named_university_does_not_get_general_intake_dates(self):
        with patch("backend.structured_retrieval.get_intakes", return_value=[]) as university, \
             patch("backend.structured_retrieval.get_general_intakes") as general:
            evidence = retrieve_structured_evidence("Example University intakes", "Example University")
        university.assert_called_once_with("Example University")
        general.assert_not_called()
        self.assertEqual(evidence, {"context": "", "sources": []})

    def test_services_require_approved_query_results(self):
        with patch("backend.structured_retrieval.get_agency_services", return_value=[]), \
             patch("backend.structured_retrieval.has_pending_agency_services", return_value=False):
            evidence = retrieve_structured_evidence("Why choose Randyll Overseas?")
        self.assertEqual(evidence, {"context": "", "sources": []})

    def test_generic_agency_questions_report_pending_review(self):
        for question in ("agency details", "Our servicese", "our services", "Why should I choose Randyll oversese?"):
            with self.subTest(question=question), \
                 patch("backend.structured_retrieval.get_agency_services", return_value=[]), \
                 patch("backend.structured_retrieval.has_pending_agency_services", return_value=True):
                evidence = retrieve_structured_evidence(question)
                self.assertIn("awaiting review", evidence["answer"])
                self.assertEqual(evidence["context"], "")

    def test_approved_services_return_facts_and_citations(self):
        row = {"source_document": "report.pdf", "source_page": 32, "service_name": "Document checklist"}
        with patch("backend.structured_retrieval.get_agency_services", return_value=[row]), \
             patch("backend.structured_retrieval.has_pending_agency_services") as pending:
            evidence = retrieve_structured_evidence("agency details")
        pending.assert_not_called()
        self.assertIn("Document checklist", evidence["context"])
        self.assertEqual(evidence["sources"][0]["page"], "32")
        self.assertTrue(is_agency_service_question("Does Randyll offer SOP drafting and interview preparation?"))

    def test_university_questions_are_not_agency_service_questions(self):
        for question in ("University admission services", "Randyll tell me the tuition", "Tuition fees"):
            self.assertFalse(is_agency_service_question(question))

    def test_multiple_categories_and_decimal_precision(self):
        with patch("backend.structured_retrieval.get_tuition", return_value=[]) as tuition, \
             patch("backend.structured_retrieval.get_intakes", return_value=[]) as intakes:
            retrieve_structured_evidence("Example University tuition and intake deadlines", "Example University")
        tuition.assert_called_once()
        intakes.assert_called_once()
        self.assertIn('"12345678901234.56"', format_database_records([Decimal("12345678901234.56")]))
