from contextlib import closing
import json
import unittest
from pathlib import Path

from backend.knowledge_loader import load_documents
from backend.review_knowledge import OUTPUT, expand_merged_cells, review_items
from backend.index_knowledge import verify_and_promote
from backend.knowledge_domains import COLLECTION
from qdrant_client import QdrantClient, models


class ReviewTests(unittest.TestCase):
    def hannam_undergraduate(self):
        return [d for d in load_documents() if d['source_document'] == 'Hannam University Bachelor_s.pdf'
                and d['original_path'] is None]

    def test_hannam_gpa_ranges_keep_scales_and_inclusive_lower_bound(self):
        rows = [d for d in self.hannam_undergraduate() if d['topic'] == 'Academic_Grading']
        self.assertEqual(len(rows), 41)
        by_score = {int(d['text'].rsplit('100 points scale: ', 1)[1]): d['text'] for d in rows}
        self.assertEqual(set(by_score), set(range(60, 101)))
        self.assertIn('4.0 scale: 3.93\u223c4.00', by_score[100])
        self.assertIn('4.5 scale: 4.42\u223c4.50', by_score[100])
        self.assertIn('7.0 scale: 5.20\u223c5.30', by_score[83])
        self.assertIn('7.0 scale: 5.10\u223c5.19', by_score[82])
        self.assertIn('4.0 scale: 1.00\uc774\ud558', by_score[60])
        self.assertIn('at or below (inclusive)', by_score[60])

    def test_hannam_appendices_keep_dates_and_supersede_fragments(self):
        docs = self.hannam_undergraduate()
        countries = [d for d in docs if d['page'] == 10]
        schools = [d for d in docs if d['page'] == 11]
        self.assertEqual(len(countries), 5)
        self.assertEqual(len(schools), 16)
        self.assertTrue(all('July 9, 2026' in d['text'] and d['topic'] == 'Documents_Verification' for d in countries))
        self.assertTrue(all('April 1, 2025' in d['text'] and 'not a nationality or automatic-admission rule' in d['text'] for d in schools))
        self.assertFalse(any(d.get('original_path', '').endswith('/Hannam_University_Bachelor_s/Documents_Verification.txt')
                             for d in load_documents() if d.get('original_path')))
        verification = next(d for d in docs if d['page'] == 7)
        self.assertIn('both the graduation certificate and transcript', verification['text'])
        self.assertIn('only if the highest academic degree was obtained in China', verification['text'])

    def test_hannam_forms_restore_context_and_complete_declarations(self):
        docs = self.hannam_undergraduate()
        letter = next(d for d in docs if d['page'] == 17)
        self.assertIn('Form 2', letter['text'])
        self.assertIn('Field 4: Write the exact date of graduation (withdrawal)', letter['text'])
        declaration = next(d for d in docs if d['page'] == 19)['text']
        self.assertIn('(By signing here,', declaration)
        self.assertIn('cancellation of my admission to Hannam University)', declaration)
        ledger = json.loads((OUTPUT / 'REVIEW_LEDGER.json').read_text(encoding='utf-8'))
        self.assertTrue(all(d['outcome'] == 'reconstructed_original_held' for d in ledger if d['review_id'] in {'R004', 'R005'}))

    def test_hannam_program_totals_and_distinct_tracks(self):
        docs = [d for d in load_documents() if d['source_document'] ==
                '2027-Spring-Semester-Graduate-School-Admissions-Guide-HNU.pdf'
                and d['topic'] == 'Programs_Majors' and d.get('page') in (4, 5)]
        self.assertEqual(len(docs), 48)
        self.assertEqual(sum(d['page'] == 5 for d in docs), 22)
        for heading, expected in [("Master's", 45), ('Ph.D.', 42), ('Integrated Ph.D.', 36)]:
            self.assertEqual(sum(f'\n{heading}: \u25cb' in d['text'] for d in docs), expected)
        bio = [d for d in docs if '\nDepartment: Biopharmaceutical Engineering\n' in d['text']]
        self.assertEqual(len(bio), 2)
        ordinary = next(d for d in bio if '\nField: ENGINEERING\n' in d['text'])
        interdisciplinary = next(d for d in bio if '\nField: INTERDISCIPLINE / ENGINEERING\n' in d['text'])
        self.assertIn("\nMaster's: \u25cb\nPh.D.: -\nIntegrated Ph.D.: -", ordinary['text'])
        self.assertIn("\nMaster's: -\nPh.D.: \u25cb\nIntegrated Ph.D.: -", interdisciplinary['text'])
        fine = next(d for d in docs if '\nDepartment: Fine Arts\n' in d['text'])
        self.assertIn("Industrial Art (Master's); Fine Art (Ph.D.)", fine['text'])
        self.assertIn('Integrated Ph.D.: -', fine['text'])
        ledger = json.loads((OUTPUT / 'REVIEW_LEDGER.json').read_text(encoding='utf-8'))
        item = next(d for d in ledger if d['review_id'] == 'R003')
        self.assertEqual(item['outcome'], 'reconstructed_original_held')
        self.assertEqual(len(item['replacement_paths']), 2)

    def test_promotion_accepts_coordinate_round_trip(self):
        with closing(QdrantClient(':memory:')) as client:
            client.create_collection('stage', vectors_config=models.VectorParams(size=2, distance=models.Distance.COSINE))
            client.upsert('stage', [models.PointStruct(id=1, vector=[1., 0.],
                payload={'text': 'Exact source text', 'source_region': [42.05]})])
            verify_and_promote(client, 'stage', [{'id': '1', 'text': 'Exact source text', 'source_region': [42.050000000000004]}])
            self.assertEqual(client.get_aliases().aliases[0].alias_name, COLLECTION)

    def test_promotion_rejects_changed_evidence(self):
        with closing(QdrantClient(':memory:')) as client:
            client.create_collection('stage', vectors_config=models.VectorParams(size=2, distance=models.Distance.COSINE))
            client.upsert('stage', [models.PointStruct(id=1, vector=[1., 0.], payload={'text': 'Old fact'})])
            with self.assertRaises(RuntimeError):
                verify_and_promote(client, 'stage', [{'id': '1', 'text': 'Corrected fact'}])
            self.assertEqual(client.get_aliases().aliases, [])

    def test_all_approved_items_have_ledger_entries(self):
        ledger = json.loads((OUTPUT / 'REVIEW_LEDGER.json').read_text(encoding='utf-8'))
        self.assertEqual({d['review_id'] for d in ledger}, {d['review_id'] for d in review_items()})
        self.assertEqual(len(ledger), 78)

    def test_production_manifest_fails_closed(self):
        docs = load_documents()
        self.assertTrue(docs)
        self.assertTrue(all(d['status'] == 'active' and d['audience'] == 'international' for d in docs))
        self.assertFalse(any(d['university'].startswith('Unverified') for d in docs))
        self.assertFalse(any(d['university'] in {'KIT', 'Woosuk University', 'Kunjang University College'} for d in docs))

    def test_kongju_insurance_is_not_a_financial_affidavit(self):
        docs = [d for d in load_documents() if d['university'] == 'Kongju National University'
                and d['topic'] == 'Health_Insurance']
        self.assertEqual({(d['degree'], d['page']) for d in docs}, {('Graduate', 17), ('Undergraduate', 14)})
        self.assertTrue(all('Mandatory Enrollment' in d['text'] for d in docs))

    def test_housing_prices_keep_their_residence(self):
        d = next(d for d in load_documents() if d['university'] == 'Yeungnam University College'
                 and d['topic'] == 'Housing_Dormitory')
        self.assertIn('Happy Dormitory: 2 persons per room; KRW 264,000', d['text'])
        self.assertIn('Global House: 2 persons per room; KRW 210,000', d['text'])
        self.assertIn('Meals are not included', d['text'])

    def test_merged_cells_follow_rectangles_not_previous_values(self):
        class Row:
            def __init__(self, cells): self.cells = cells
        class Table:
            rows = [Row([(0, 0, 10, 20), (10, 0, 20, 10)]),
                    Row([None, (10, 10, 20, 20)]),
                    Row([(0, 20, 10, 30), (10, 20, 20, 30)])]
            def extract(self): return [['Incoming', 'A'], [None, 'B'], ['', 'C']]
        self.assertEqual(expand_merged_cells(Table()), [['Incoming', 'A'], ['Incoming', 'B'], ['', 'C']])


if __name__ == '__main__':
    unittest.main()
