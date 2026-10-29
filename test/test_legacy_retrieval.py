import unittest
from contextlib import closing

from qdrant_client import QdrantClient, models

from backend.legacy_retrieval import search_legacy_collection


class LegacyRetrievalTests(unittest.TestCase):
    def test_legacy_missing_metadata_allowed_but_explicit_holds_excluded(self):
        with closing(QdrantClient(":memory:")) as client:
            client.create_collection("legacy", vectors_config=models.VectorParams(
                size=2, distance=models.Distance.COSINE))
            payloads = [
                {"topic": "Tuition Fees"},
                {"status": "held"},
                {"audience": "domestic"},
                {"audience": "unresolved"},
                {"review_required": True},
                {"topic": "Programs Majors"},
            ]
            client.upsert("legacy", [models.PointStruct(
                id=i, vector=[1., 0.], payload=payload)
                for i, payload in enumerate(payloads)])
            hits = search_legacy_collection(client, "legacy", [1., 0.], "fees", 10)
            self.assertEqual({hit.id for hit in hits}, {0, 5})
            hits = search_legacy_collection(client, "legacy", [1., 0.], "fees", 10,
                                            domains=["finances"])
            self.assertEqual([hit.id for hit in hits], [0])
            hits = search_legacy_collection(client, "legacy", [1., 0.], "fees", 10,
                                            accept=lambda point: point.id == 5)
            self.assertEqual([hit.id for hit in hits], [5])
