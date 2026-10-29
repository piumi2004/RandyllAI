import csv
import tempfile
import unittest
from pathlib import Path

from qdrant_client import QdrantClient, models
from backend.knowledge_domains import TAXONOMY, classify_topic, infer_domains, search_with_domains
from backend.knowledge_loader import load_documents, audit, resolve_root


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'Randyll_Semantic_Knowledge'
        self.root.mkdir()
        with (self.root / 'KNOWLEDGE_INDEX.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['file_path', 'source_document'])
            writer.writeheader()
            for topic in ('Tuition_Fees', 'Housing_Dormitory', 'Other_Information'):
                path = f'Example_University/Graduate/Guide/{topic}.txt'
                writer.writerow({'file_path': path, 'source_document': 'Guide.pdf'})
                target = self.root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('Example passage', encoding='utf-8')

    def test_nested_and_flat_roots_produce_same_identity(self):
        nested = load_documents(self.base)
        flat = load_documents(self.root)
        self.assertEqual(nested, flat)
        self.assertTrue(all(d['university'] == 'Example University' for d in nested))
        self.assertTrue(all(d['degree'] == 'Graduate' for d in nested))

    def test_source_has_multiple_domains_without_copying_chunks(self):
        docs = load_documents(self.base)
        self.assertEqual(len(docs), 3)
        self.assertEqual(len({d['document_id'] for d in docs}), 1)
        self.assertTrue(all(d['document_domains'] == ['accommodation', 'finances'] for d in docs))

    def test_ambiguous_topic_is_reviewed_not_invented(self):
        doc = next(d for d in load_documents(self.base) if d['topic'] == 'Other_Information')
        self.assertEqual(doc['domains'], [])
        self.assertIn('unmapped_or_ambiguous_topic', doc['review_reasons'])
        self.assertEqual(classify_topic('Unknown_Topic')[1:], ([], True))

    def test_curated_precedence_only_when_nonempty_curated_exists(self):
        auto = self.root / 'Dongseo_University/Mixed/Guide/Tuition_Fees.txt'
        auto.parent.mkdir(parents=True)
        auto.write_text('ORIGINAL SOURCE: Guide.pdf\nAutomatic fees', encoding='utf-8')
        self.assertTrue(any(d['source_path'].startswith('Dongseo_University') for d in load_documents(self.base)))
        curated = self.root / 'CURATED_FACT_SHEETS/Dongseo_University/02_Undergraduate_Tuition.txt'
        curated.parent.mkdir(parents=True)
        curated.write_text('Source: Guide.md, Tuition\nCurated fees', encoding='utf-8')
        docs = [d for d in load_documents(self.base) if d['university'] == 'Dongseo University']
        self.assertEqual(len(docs), 1)
        self.assertTrue(docs[0]['curated'])
        self.assertEqual(docs[0]['degree'], 'Undergraduate')
        self.assertEqual(docs[0]['source_document'], 'Guide.md')

    def test_ambiguous_roots_fail(self):
        (self.base / 'KNOWLEDGE_INDEX.csv').write_text('file_path,source_document\n')
        with self.assertRaises(ValueError):
            resolve_root(self.base)

    def test_taxonomy_and_coverage(self):
        for topic, domains in TAXONOMY['topics'].items():
            self.assertLessEqual(set(domains), set(TAXONOMY['domains']), topic)
        for target in TAXONOMY['aliases'].values():
            self.assertIn(target, TAXONOMY['topics'])
        report = audit(load_documents(self.base))
        self.assertIn('employment', report['uncovered_domains'])
        self.assertEqual(len(report['review_queue']), 1)


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.client = QdrantClient(':memory:')
        self.addCleanup(self.client.close)
        self.client.create_collection('test', vectors_config=models.VectorParams(size=2, distance=models.Distance.COSINE))
        self.client.upsert('test', points=[
            models.PointStruct(id=1, vector=[1.0, 0.0], payload={'status': 'active', 'audience': 'international', 'university': 'A', 'domains': ['finances', 'applications']}),
            models.PointStruct(id=2, vector=[0.9, 0.1], payload={'status': 'active', 'audience': 'international', 'university': 'A', 'domains': ['accommodation']}),
            models.PointStruct(id=3, vector=[0.8, 0.2], payload={'status': 'active', 'audience': 'international', 'university': 'B', 'domains': ['visas']}),
            models.PointStruct(id=4, vector=[0.7, 0.3], payload={'status': 'active', 'audience': 'international', 'university': 'A', 'domains': []}),
        ])

    def search(self, question='', domains=None):
        return search_with_domains(self.client, 'test', [1.0, 0.0], question, 10,
            accept=lambda point: point.payload['university'] == 'A', domains=domains)

    def test_explicit_domains_match_array_and_remain_strict(self):
        self.assertEqual([p.id for p in self.search(domains=['applications'])], [1])
        self.assertEqual({p.id for p in self.search(domains=['finances', 'accommodation'])}, {1, 2})
        self.assertEqual(self.search(domains=['employment']), [])

    def test_inferred_search_keeps_broad_fallback_and_deduplicates(self):
        self.assertEqual([p.id for p in self.search('tuition')], [1, 2, 4])
        self.assertEqual([p.id for p in self.search('visa')], [1, 2, 4])
        self.assertEqual([p.id for p in self.search('part-time work')], [1, 2, 4])

    def test_unknown_and_mixed_questions(self):
        self.assertEqual(infer_domains('Tell me more'), [])
        self.assertEqual(infer_domains('visa and tuition'), ['finances', 'visas'])
        self.assertEqual([p.id for p in self.search('Tell me more')], [1, 2, 4])

    def test_invalid_explicit_domain_fails(self):
        with self.assertRaises(ValueError):
            self.search(domains=['made_up'])

    def test_held_domestic_and_legacy_points_never_enter_fallback(self):
        self.client.upsert('test', points=[models.PointStruct(id=i, vector=[1.0, 0.0], payload=p)
            for i, p in enumerate([
                {'university': 'A', 'domains': ['finances'], 'status': 'held', 'audience': 'international'},
                {'university': 'A', 'domains': ['finances'], 'status': 'active', 'audience': 'domestic'},
                {'university': 'A', 'domains': ['finances']},
            ], 5)])
        for question, domains in [('tuition', None), ('unrecognized', None), ('', ['finances'])]:
            self.assertFalse({5, 6, 7} & {p.id for p in self.search(question, domains)})


class V2RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.client = QdrantClient(':memory:')
        self.addCleanup(self.client.close)
        self.collection = 'randyll_korea_knowledge_v2'
        self.client.create_collection(self.collection,
            vectors_config=models.VectorParams(size=2, distance=models.Distance.COSINE))
        self.client.upsert(self.collection, points=[
            models.PointStruct(id=i, vector=[1.0, 0.0] if i < 65 else [0.8, 0.2], payload={
                'university': 'Randyll Semantic Knowledge', 'degree': 'Example University',
                'topic': 'Tuition Fees' if i % 2 else 'Housing Dormitory',
                'source_path': 'Randyll_Semantic_Knowledge/' +
                    ('Other_University' if i < 65 else 'Example_University') +
                    '/Graduate/Guide/Tuition_Fees.txt',
            }) for i in range(1, 69)])

    def search(self, domains=None):
        return search_with_domains(self.client, self.collection, [1.0, 0.0], 'tuition', 2,
            accept=lambda p: p.payload['university'] == 'Example University', domains=domains)

    def test_legacy_payload_and_university_filter_beyond_first_page(self):
        points = self.search()
        self.assertEqual(len(points), 2)
        self.assertTrue(all(p.id >= 65 for p in points))
        self.assertTrue(all(p.payload['degree'] == 'Graduate' for p in points))
        stored = self.client.retrieve(self.collection, ids=[65])[0]
        self.assertEqual(stored.payload['university'], 'Randyll Semantic Knowledge')

    def test_explicit_domains_use_legacy_topics(self):
        self.assertEqual({p.id for p in self.search(['finances'])}, {65, 67})
        self.assertEqual(self.search(['employment']), [])
        with self.assertRaises(ValueError):
            self.search(['unknown'])

    def test_explicit_held_or_domestic_records_remain_excluded(self):
        self.client.set_payload(self.collection, payload={'status': 'held'}, points=[65])
        self.client.set_payload(self.collection, payload={'audience': 'domestic'}, points=[66])
        self.assertEqual({p.id for p in self.search()}, {67, 68})


if __name__ == '__main__':
    unittest.main()
