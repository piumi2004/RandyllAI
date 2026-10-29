import unittest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from backend.corpus_ingestion import parse_amount, pdf_tuition_rows, postgres_safe, xlsx_sheets
from backend.structured_search import fee_groups, question_filters, summarize_fee_scopes, field_terms


class CorpusTests(unittest.TestCase):
    def test_money_parsing_never_turns_ranges_or_formulas_into_exact_fees(self):
        for value in ("1,200–1,500", "12,34", "=F2*0.21", "KRW 500", "-100", "", "5.5%", "100 200"):
            self.assertIsNone(parse_amount(value), value)
        self.assertEqual(parse_amount("4,373,800"), "4373800")
        self.assertEqual(parse_amount("123.45"), "123.45")

    def test_table_fee_keeps_field_and_currency_without_using_scholarship_percentage(self):
        rows = [["Category", "Tuition Fee (KRW)"], ["Engineering", "5,718,800"], ["Scholarship", "50%"]]
        fees = pdf_tuition_rows(rows, "Tuition fee KRW")
        self.assertEqual(len(fees), 1)
        self.assertEqual((fees[0]["field"], fees[0]["amount"], fees[0]["currency"]),
                         ("Engineering", "5718800", "KRW"))

    def test_database_nul_escape_is_visible_and_preserves_other_unicode(self):
        raw = {"text": "☎ 한국\x00text", "cells": ["A\x00B"]}
        safe = postgres_safe(raw)
        self.assertEqual(safe["text"], "☎ 한국\\u0000text")
        self.assertIn("\x00", raw["text"])
        self.assertNotIn("\x00", safe["cells"][0])

    def test_workbook_uses_relationships_not_sheet_ids_and_preserves_formulas(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.xlsx"
            with ZipFile(path, "w") as z:
                z.writestr("xl/workbook.xml", '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Fees" sheetId="9" r:id="rId7"/></sheets></workbook>')
                z.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="rId7" Target="worksheets/sheet2.xml"/></Relationships>')
                z.writestr("xl/worksheets/sheet2.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="2"><c r="A2" t="inlineStr"><is><t>University</t></is></c><c r="F2"><f>100*2</f><v>200</v></c></row></sheetData></worksheet>')
            sheet, rows = next(xlsx_sheets(path))
            self.assertEqual(sheet, "Fees")
            self.assertEqual(rows[0]["values"]["A"], "University")
            self.assertEqual(rows[0]["formulas"]["F"], "100*2")

    def test_comparisons_separate_currency_period_year_and_degree(self):
        base = {"university": "A", "field_of_study": "Engineering", "degree_level": "Bachelor",
                "amount": Decimal("2000"), "currency": "KRW", "billing_period": "semester",
                "effective_year": 2026, "is_estimate": False, "amount_max": None}
        records = [base, {**base, "university": "B", "amount": Decimal("1500")},
                   {**base, "currency": "USD"}, {**base, "effective_year": 2027},
                   {**base, "degree_level": "Master"}, {**base, "billing_period": "year"}]
        groups, unranked = fee_groups(records)
        self.assertEqual(len(groups), 5)
        self.assertEqual(unranked, [])
        combined = next(g for g in groups if len(g["rows"]) == 2)
        self.assertEqual(combined["rows"][0]["university"], "B")
        self.assertEqual(combined["rows"][1]["amount_rank_within_scope"], 2)

    def test_unknown_scope_and_estimates_are_not_ranked(self):
        base = {"university": "A", "field_of_study": "X", "degree_level": "Bachelor", "amount": "100",
                "currency": "KRW", "billing_period": "semester", "effective_year": 2026,
                "is_estimate": False, "amount_max": None}
        rows = [{**base, "billing_period": "unknown"}, {**base, "effective_year": None},
                {**base, "is_estimate": True}, {**base, "degree_level": "Graduate"},
                {**base, "amount_max": "200"}]
        groups, unknown = fee_groups(rows)
        self.assertFalse(groups)
        self.assertEqual(len(unknown), 5)

    def test_budget_parser_keeps_currency_period_year_and_degree(self):
        filters = question_filters("English taught master's tuition under 10 million KRW per year in 2027")
        self.assertEqual(filters["maximum"], Decimal("10000000"))
        self.assertEqual((filters["currency"], filters["period"], filters["degree"], filters["year"]),
                         ("KRW", "year", "Master", 2027))
        self.assertEqual(filters["language"], "English")
        self.assertFalse(filters["budget_inclusive"])
        self.assertTrue(question_filters("tuition up to 10 million KRW per year")["budget_inclusive"])
        self.assertEqual(field_terms("Engineering departments"), ["engineering"])

    def test_large_catalogue_does_not_hide_second_university(self):
        base = {"university": "A", "field_of_study": "Engineering", "degree_level": "Bachelor",
                "amount": "100", "currency": "KRW", "billing_period": "unknown",
                "effective_year": None, "review_status": "pending"}
        rows = [{**base, "amount": str(i+100)} for i in range(385)] + [{**base, "university": "B", "amount": "500"}]
        summary, examples = summarize_fee_scopes(rows)
        self.assertEqual({r["university"] for r in summary}, {"A", "B"})
        self.assertEqual({r["university"] for r in examples}, {"A", "B"})
        self.assertEqual(summary[0]["listed_records"], 385)
