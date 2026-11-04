import unittest

import numpy as np
import pymupdf
from qdrant_client import QdrantClient, models

from backend.knowledge_domains import (
    LEGACY_COLLECTION,
    UPLOAD_COLLECTION,
    search_with_domains,
)
from backend.upload_documents import (
    GUIDE_CATEGORIES,
    UNIVERSITIES,
    analyze_guide,
    extract_pages,
    inspect_replacement_targets,
    replace_guide_in_qdrant,
    upload_document_to_qdrant,
)


class FakeEmbeddingModel:
    def get_sentence_embedding_dimension(self):
        return 4

    def encode(self, texts, **kwargs):
        return np.asarray([[1.0, 0.0, 0.0, 0.0] for _ in texts])


class FailSecondDeleteClient:
    def __init__(self, client):
        self.client = client
        self.delete_count = 0

    def __getattr__(self, name):
        return getattr(self.client, name)

    def delete(self, *args, **kwargs):
        self.delete_count += 1
        if self.delete_count == 2:
            raise RuntimeError("simulated delete failure")
        return self.client.delete(*args, **kwargs)


class UploadDocumentTests(unittest.TestCase):
    def make_pdf(self, text):
        document = pymupdf.open()
        page = document.new_page()
        page.insert_text((72, 72), text)
        content = document.tobytes()
        document.close()
        return content

    def make_multipage_pdf(self, page_texts):
        document = pymupdf.open()
        for text in page_texts:
            page = document.new_page()
            page.insert_text((72, 72), text)
        content = document.tobytes()
        document.close()
        return content

    def make_metadata(self):
        filename = "dongseo-2027-undergraduate-admission-guide.pdf"
        content = self.make_pdf(
            "Dongseo University\n"
            "2027 Undergraduate Admission Guidelines\n"
            "Application procedure and required documents."
        )
        return filename, content, analyze_guide(filename, content)

    def make_qdrant(self, collections=("main",)):
        client = QdrantClient(":memory:")
        self.addCleanup(client.close)
        for collection in collections:
            client.create_collection(
                collection_name=collection,
                vectors_config=models.VectorParams(
                    size=4,
                    distance=models.Distance.COSINE,
                ),
            )
        return client

    def test_analysis_detects_university_year_category_and_degree(self):
        _, _, metadata = self.make_metadata()
        self.assertEqual(metadata["university_id"], "dongseo")
        self.assertEqual(metadata["university"], UNIVERSITIES["dongseo"])
        self.assertEqual(metadata["academic_year"], 2027)
        self.assertEqual(metadata["category_label"], "Admission guidelines")
        self.assertEqual(metadata["degree_level"], "Undergraduate")
        self.assertEqual(metadata["intake_scope"], "All intakes")
        self.assertEqual(metadata["page_count"], 1)

    def test_analysis_rejects_multiple_universities(self):
        filename = "2027-undergraduate-admission-guide.pdf"
        content = self.make_pdf(
            "Dongseo University and Gachon University\n"
            "2027 Undergraduate Admission Guidelines"
        )
        with self.assertRaisesRegex(ValueError, "multiple supported universities"):
            analyze_guide(filename, content)

    def test_analysis_finds_university_beyond_first_two_pages(self):
        filename = "Group Admission Guide.pdf"
        content = self.make_multipage_pdf([
            "2027 Undergraduate Admission Guidelines",
            "Application procedure and required documents.",
            "University: Dongseo University",
        ])
        metadata = analyze_guide(filename, content)
        self.assertEqual(metadata["university_id"], "dongseo")

    def test_longer_university_alias_wins_over_its_embedded_short_name(self):
        filename = "2027 Undergraduate Admission Guidelines.pdf"
        content = self.make_pdf(
            "Yeungnam University College\n"
            "2027 Undergraduate Admission Guidelines"
        )
        metadata = analyze_guide(filename, content)
        self.assertEqual(metadata["university_id"], "yeungnam university college")

    def test_analysis_rejects_unclear_degree_scope(self):
        filename = "dongseo-2027-admission-guide.pdf"
        content = self.make_pdf(
            "Dongseo University\n2027 Admission Guidelines"
        )
        with self.assertRaisesRegex(ValueError, "determine one degree level"):
            analyze_guide(filename, content)

    def test_analysis_rejects_conflicting_academic_year(self):
        filename = "dongseo-2027-undergraduate-admission-guide.pdf"
        content = self.make_pdf(
            "Dongseo University\n2026 Academic Year Undergraduate Admission Guidelines"
        )
        with self.assertRaisesRegex(ValueError, "conflicts with the guide title"):
            analyze_guide(filename, content)

    def test_pdf_text_is_extracted_with_page_numbers(self):
        content = self.make_pdf("2027 admission requirements")
        self.assertEqual(
            extract_pages("guide.pdf", content),
            [{"page": 1, "text": "2027 admission requirements"}],
        )

    def test_generic_markdown_upload_is_indexed_and_searchable(self):
        client = self.make_qdrant((LEGACY_COLLECTION,))
        filename = "student-support.md"
        content = (
            b"# Student support\n\n"
            b"Students can contact the international office for help."
        )
        result = upload_document_to_qdrant(
            filename,
            content,
            client,
            FakeEmbeddingModel(),
        )
        self.assertEqual(result["chunks"], 1)
        self.assertFalse(result["already_active"])

        points, _ = client.scroll(
            UPLOAD_COLLECTION,
            limit=10,
            with_payload=True,
        )
        self.assertEqual(len(points), 1)
        payload = points[0].payload
        self.assertEqual(payload["status"], "active")
        self.assertNotIn("source_version", payload)
        self.assertNotIn("document_key", payload)
        self.assertEqual(payload["filename"], filename)
        self.assertEqual(payload["university"], "General knowledge")
        self.assertIn("applications", payload["domains"])
        self.assertIn("Students can contact", payload["text"])

        results = search_with_domains(
            client,
            LEGACY_COLLECTION,
            [1.0, 0.0, 0.0, 0.0],
            "student support",
            10,
            domains=["education"],
            additional_collections=(UPLOAD_COLLECTION,),
        )
        self.assertTrue(any(point.payload["filename"] == filename for point in results))
        duplicate = upload_document_to_qdrant(
            filename,
            content,
            client,
            FakeEmbeddingModel(),
        )
        self.assertTrue(duplicate["already_active"])

    def test_generic_upload_supports_plain_text_and_pdf(self):
        client = self.make_qdrant()
        model = FakeEmbeddingModel()
        txt_result = upload_document_to_qdrant(
            "notes.txt",
            b"Plain UTF-8 text document.",
            client,
            model,
        )
        pdf_result = upload_document_to_qdrant(
            "notes.pdf",
            self.make_pdf("PDF document text."),
            client,
            model,
        )
        self.assertEqual(txt_result["chunks"], 1)
        self.assertEqual(pdf_result["chunks"], 1)
        points, _ = client.scroll(
            UPLOAD_COLLECTION,
            limit=10,
            with_payload=True,
        )
        self.assertEqual(
            {point.payload["filename"] for point in points},
            {"notes.txt", "notes.pdf"},
        )

    def test_changed_same_source_upload_replaces_obsolete_chunks(self):
        client = self.make_qdrant(("main",))
        filename = "dongseo-guide-2027.pdf"
        client.upsert(
            collection_name="main",
            points=[
                models.PointStruct(
                    id=301,
                    vector=[0.8, 0.2, 0.0, 0.0],
                    payload={
                        "text": "Unchanged tuition information.",
                        "source_document": filename,
                        "university": "Dongseo University",
                        "degree": "Undergraduate",
                        "topic": "Tuition_Fees",
                        "source_path": (
                            "Dongseo_University/Undergraduate/Guide/Tuition_Fees.txt"
                        ),
                    },
                ),
                models.PointStruct(
                    id=302,
                    vector=[0.7, 0.3, 0.0, 0.0],
                    payload={
                        "text": "Old deadline information for 2026.",
                        "source_document": filename,
                        "university": "Dongseo University",
                        "degree": "Undergraduate",
                        "topic": "Tuition_Fees",
                        "source_path": (
                            "Dongseo_University/Undergraduate/Guide/Tuition_Fees.txt"
                        ),
                    },
                ),
                models.PointStruct(
                    id=303,
                    vector=[0.6, 0.4, 0.0, 0.0],
                    payload={
                        "text": "Unrelated source content.",
                        "source_document": "other-guide.pdf",
                        "university": "Gachon University",
                        "topic": "Other_Information",
                    },
                ),
            ],
        )
        revised_pdf = self.make_multipage_pdf([
            "Unchanged tuition information.",
            "New deadline information for 2027.",
        ])

        result = upload_document_to_qdrant(
            filename,
            revised_pdf,
            client,
            FakeEmbeddingModel(),
            primary_collection="main",
        )

        self.assertEqual(result["unchanged_chunks"], 1)
        self.assertEqual(result["updated_chunks"], 1)
        self.assertEqual(result["removed_chunks"], 1)
        main_points, _ = client.scroll("main", limit=10, with_payload=True)
        self.assertEqual(
            {str(point.id) for point in main_points},
            {"301", "303"},
        )
        upload_points, _ = client.scroll(
            UPLOAD_COLLECTION,
            limit=10,
            with_payload=True,
        )
        self.assertEqual(len(upload_points), 1)
        self.assertTrue(all("source_version" not in point.payload for point in upload_points))
        self.assertTrue(all(
            point.payload["university"] == "Dongseo University"
            and point.payload["topic"] == "Tuition_Fees"
            and point.payload["academic_year"] == 2027
            for point in upload_points
        ))
        indexed_text = "\n".join(
            point.payload.get("text", "")
            for point in [*main_points, *upload_points]
        )
        self.assertIn("Unchanged tuition information.", indexed_text)
        self.assertIn("New deadline information for 2027.", indexed_text)
        self.assertNotIn("Old deadline information for 2026.", indexed_text)
        self.assertIn("New deadline information for 2027.", upload_points[0].payload["text"])
        self.assertNotIn("Unchanged tuition information.", upload_points[0].payload["text"])
        retrieved = search_with_domains(
            client,
            "main",
            [1.0, 0.0, 0.0, 0.0],
            "deadline information",
            10,
            additional_collections=(UPLOAD_COLLECTION,),
        )
        retrieved_text = "\n".join(point.payload["text"] for point in retrieved)
        self.assertIn("New deadline information for 2027.", retrieved_text)
        self.assertNotIn("Old deadline information for 2026.", retrieved_text)

        repeated = upload_document_to_qdrant(
            filename,
            revised_pdf,
            client,
            FakeEmbeddingModel(),
            primary_collection="main",
        )
        self.assertTrue(repeated["already_active"])
        self.assertEqual(repeated["unchanged_chunks"], 2)

        held_client = self.make_qdrant(("main",))
        held_client.upsert(
            collection_name="main",
            points=[models.PointStruct(
                id=304,
                vector=[0.5, 0.5, 0.0, 0.0],
                payload={
                    "text": "Held source information.",
                    "source_document": filename,
                    "review_status": "needs_official_verification",
                    "publication_status": "staging_only_not_approved",
                },
            )],
        )
        with self.assertRaisesRegex(ValueError, "complete the review workflow"):
            upload_document_to_qdrant(
                filename,
                revised_pdf,
                held_client,
                FakeEmbeddingModel(),
                primary_collection="main",
            )
        held_points, _ = held_client.scroll("main", limit=10)
        self.assertEqual({str(point.id) for point in held_points}, {"304"})

    def test_numeric_duplicate_filename_replaces_previous_copy(self):
        client = self.make_qdrant(("main",))
        client.upsert(
            collection_name="main",
            points=[models.PointStruct(
                id=305,
                vector=[0.8, 0.2, 0.0, 0.0],
                payload={
                    "text": (
                        "Bonus Opportunity 1 (Real Industry Consultancy): "
                        "+10%, up to 10 bonus marks."
                    ),
                    "source_document": "Group Assignment (1).pdf",
                    "filename": "Group Assignment (1).pdf",
                    "university": "General_South_Korea_Guidance",
                    "topic": "Other_Information",
                    "source_path": "data/reports/group-assignment.txt",
                },
            )],
        )
        new_pdf = self.make_pdf(
            "Bonus Opportunity 1 (Real Industry Consultancy): "
            "+20%, up to 20 bonus marks."
        )

        result = upload_document_to_qdrant(
            "Group Assignment (2).pdf",
            new_pdf,
            client,
            FakeEmbeddingModel(),
            primary_collection="main",
        )

        self.assertTrue(result["matched_source"])
        self.assertEqual(result["updated_chunks"], 1)
        self.assertEqual(result["removed_chunks"], 1)
        old_points = client.retrieve(
            "main",
            ids=[305],
            with_payload=True,
        )
        self.assertEqual(old_points, [])
        latest_points, _ = client.scroll(
            UPLOAD_COLLECTION,
            limit=10,
            with_payload=True,
        )
        self.assertEqual(len(latest_points), 1)
        self.assertNotIn("source_version", latest_points[0].payload)
        self.assertIn("+20%", latest_points[0].payload["text"])
        self.assertNotIn("+10%", latest_points[0].payload["text"])

        results = search_with_domains(
            client,
            "main",
            [1.0, 0.0, 0.0, 0.0],
            "bonus opportunity marks",
            10,
            additional_collections=(UPLOAD_COLLECTION,),
        )
        self.assertTrue(results)
        self.assertTrue(all("+10%" not in point.payload["text"] for point in results))
        self.assertTrue(any("+20%" in point.payload["text"] for point in results))

    def test_exact_uploaded_copy_wins_over_older_numbered_copy(self):
        client = self.make_qdrant(("main", UPLOAD_COLLECTION))
        shared_text = "The course includes a real industry consultancy."
        old_text = "Bonus Opportunity 1: +10%, up to 10 bonus marks."
        new_text = "Bonus Opportunity 1: +20%, up to 20 bonus marks."
        client.upsert(
            collection_name=UPLOAD_COLLECTION,
            points=[
                models.PointStruct(
                    id=401,
                    vector=[0.7, 0.3, 0.0, 0.0],
                    payload={
                        "text": f"Source document: Group Assignment (1).pdf\n\n{shared_text}",
                        "source_document": "Group Assignment (1).pdf",
                        "filename": "Group Assignment (1).pdf",
                        "status": "active",
                        "audience": "international",
                        "domains": ["education"],
                    },
                ),
                models.PointStruct(
                    id=402,
                    vector=[0.6, 0.4, 0.0, 0.0],
                    payload={
                        "text": f"Source document: Group Assignment (1).pdf\n\n{old_text}",
                        "source_document": "Group Assignment (1).pdf",
                        "filename": "Group Assignment (1).pdf",
                        "status": "active",
                        "audience": "international",
                        "domains": ["education"],
                    },
                ),
                models.PointStruct(
                    id=403,
                    vector=[0.8, 0.2, 0.0, 0.0],
                    payload={
                        "text": f"Source document: Group Assignment (2).pdf\n\n{shared_text}",
                        "source_document": "Group Assignment (2).pdf",
                        "filename": "Group Assignment (2).pdf",
                        "status": "active",
                        "audience": "international",
                        "domains": ["education"],
                    },
                ),
                models.PointStruct(
                    id=404,
                    vector=[0.9, 0.1, 0.0, 0.0],
                    payload={
                        "text": f"Source document: Group Assignment (2).pdf\n\n{new_text}",
                        "source_document": "Group Assignment (2).pdf",
                        "filename": "Group Assignment (2).pdf",
                        "status": "active",
                        "audience": "international",
                        "domains": ["education"],
                    },
                ),
            ],
        )
        new_pdf = self.make_multipage_pdf([shared_text, new_text])

        result = upload_document_to_qdrant(
            "Group Assignment (2).pdf",
            new_pdf,
            client,
            FakeEmbeddingModel(),
            primary_collection="main",
        )

        self.assertTrue(result["matched_source"])
        self.assertEqual(result["unchanged_chunks"], 2)
        self.assertEqual(result["updated_chunks"], 0)
        self.assertEqual(result["removed_chunks"], 2)
        points, _ = client.scroll(
            UPLOAD_COLLECTION,
            limit=10,
            with_payload=True,
        )
        self.assertEqual({str(point.id) for point in points}, {"403", "404"})
        self.assertTrue(all("source_version" not in point.payload for point in points))
        self.assertTrue(all("document_key" not in point.payload for point in points))
        self.assertTrue(all("is_active" not in point.payload for point in points))
        results = search_with_domains(
            client,
            "main",
            [1.0, 0.0, 0.0, 0.0],
            "bonus opportunity marks",
            10,
            additional_collections=(UPLOAD_COLLECTION,),
        )
        self.assertTrue(results)
        self.assertTrue(all("+10%" not in point.payload["text"] for point in results))
        self.assertTrue(any("+20%" in point.payload["text"] for point in results))

    def test_replacement_deletes_matching_old_vectors_across_collections(self):
        client = self.make_qdrant(("main", UPLOAD_COLLECTION))
        filename, content, metadata = self.make_metadata()
        category_topics = GUIDE_CATEGORIES["Admission guidelines"]["topics"]
        client.upsert(
            collection_name="main",
            points=[
                models.PointStruct(
                    id=101,
                    vector=[0.8, 0.2, 0.0, 0.0],
                    payload={
                        "topic": "Application_Procedure",
                        "source_path": (
                            "Dongseo_University/Undergraduate/Guide/"
                            "Application_Procedure.txt"
                        ),
                    },
                ),
                models.PointStruct(
                    id=102,
                    vector=[0.7, 0.3, 0.0, 0.0],
                    payload={
                        "topic": "Application_Procedure",
                        "source_path": (
                            "Dongseo_University/Graduate/Guide/"
                            "Application_Procedure.txt"
                        ),
                    },
                ),
                models.PointStruct(
                    id=103,
                    vector=[0.6, 0.4, 0.0, 0.0],
                    payload={
                        "topic": "Tuition_Fees",
                        "source_path": (
                            "Dongseo_University/Undergraduate/Guide/"
                            "Tuition_Fees.txt"
                        ),
                    },
                ),
                models.PointStruct(
                    id=104,
                    vector=[0.5, 0.5, 0.0, 0.0],
                    payload={
                        "topic": "Application_Procedure",
                        "source_path": (
                            "Gachon_University/Undergraduate/Guide/"
                            "Application_Procedure.txt"
                        ),
                    },
                ),
            ],
        )
        client.upsert(
            collection_name=UPLOAD_COLLECTION,
            points=[models.PointStruct(
                id=105,
                vector=[0.75, 0.25, 0.0, 0.0],
                payload={
                    "status": "active",
                    "audience": "international",
                    "domains": ["applications"],
                    "university_id": "dongseo",
                    "degree_level": "Undergraduate",
                    "replacement_topics": category_topics,
                    "category": "admission_guidelines",
                },
            )],
        )

        preview = inspect_replacement_targets(client, metadata, "main")
        self.assertEqual([item["points"] for item in preview], [1, 1])

        result = replace_guide_in_qdrant(
            filename,
            content,
            metadata,
            client,
            FakeEmbeddingModel(),
            primary_collection="main",
        )

        self.assertEqual(result["deleted_points"], 2)
        main_points, _ = client.scroll("main", limit=20, with_payload=True)
        upload_points, _ = client.scroll(
            UPLOAD_COLLECTION,
            limit=20,
            with_payload=True,
        )
        main_ids = {str(point.id) for point in main_points}
        self.assertEqual(
            main_ids,
            {"102", "103", "104"},
        )
        self.assertNotIn("105", {str(point.id) for point in upload_points})
        new_points = [
            point for point in upload_points
            if (point.payload or {}).get("source_hash") == metadata["sha256"]
        ]
        self.assertTrue(new_points)
        self.assertTrue(all(point.payload["status"] == "active" for point in new_points))
        self.assertTrue(all("applications" in point.payload["domains"] for point in new_points))
        self.assertTrue(all(point.payload["academic_year"] == 2027 for point in new_points))

    def test_same_active_guide_is_not_reindexed(self):
        client = self.make_qdrant()
        filename, content, metadata = self.make_metadata()
        model = FakeEmbeddingModel()
        first = replace_guide_in_qdrant(
            filename, content, metadata, client, model, "main"
        )
        second = replace_guide_in_qdrant(
            filename, content, metadata, client, model, "main"
        )
        self.assertFalse(first["already_active"])
        self.assertTrue(second["already_active"])
        points, _ = client.scroll(UPLOAD_COLLECTION, limit=20)
        self.assertEqual(len(points), first["chunks"])

    def test_old_vectors_are_restored_and_new_vectors_deactivated_on_delete_failure(self):
        base_client = self.make_qdrant(("main", UPLOAD_COLLECTION))
        filename, content, metadata = self.make_metadata()
        base_client.upsert(
            collection_name="main",
            points=[models.PointStruct(
                id=201,
                vector=[0.8, 0.2, 0.0, 0.0],
                payload={
                    "topic": "Application_Procedure",
                    "source_path": (
                        "Dongseo_University/Undergraduate/Guide/"
                        "Application_Procedure.txt"
                    ),
                },
            )],
        )
        base_client.upsert(
            collection_name=UPLOAD_COLLECTION,
            points=[models.PointStruct(
                id=202,
                vector=[0.7, 0.3, 0.0, 0.0],
                payload={
                    "status": "active",
                    "audience": "international",
                    "domains": ["applications"],
                    "university_id": "dongseo",
                    "degree_level": "Undergraduate",
                    "replacement_topics": GUIDE_CATEGORIES[
                        "Admission guidelines"
                    ]["topics"],
                    "category": "admission_guidelines",
                },
            )],
        )
        client = FailSecondDeleteClient(base_client)

        with self.assertRaisesRegex(RuntimeError, "simulated delete failure"):
            replace_guide_in_qdrant(
                filename,
                content,
                metadata,
                client,
                FakeEmbeddingModel(),
                primary_collection="main",
            )

        old_points, _ = base_client.scroll("main", limit=10)
        self.assertEqual({str(point.id) for point in old_points}, {"201"})
        new_points, _ = base_client.scroll(
            UPLOAD_COLLECTION,
            limit=20,
            with_payload=True,
        )
        self.assertIn("202", {str(point.id) for point in new_points})
        failed_points = [
            point for point in new_points
            if (point.payload or {}).get("source_hash") == metadata["sha256"]
        ]
        self.assertTrue(failed_points)
        self.assertTrue(all(
            point.payload["status"] == "replacement_failed"
            for point in failed_points
        ))

    def test_new_vectors_are_searchable_through_the_v2_chat_path(self):
        client = self.make_qdrant((LEGACY_COLLECTION,))
        filename, content, metadata = self.make_metadata()
        replace_guide_in_qdrant(
            filename,
            content,
            metadata,
            client,
            FakeEmbeddingModel(),
            primary_collection=LEGACY_COLLECTION,
        )

        results = search_with_domains(
            client,
            LEGACY_COLLECTION,
            [1.0, 0.0, 0.0, 0.0],
            "admission procedure",
            10,
            domains=["applications"],
            additional_collections=(UPLOAD_COLLECTION,),
        )
        self.assertTrue(results)
        self.assertTrue(all(
            point.payload["status"] == "active" for point in results
        ))
        self.assertTrue(any(
            point.payload.get("academic_year") == 2027 for point in results
        ))


if __name__ == "__main__":
    unittest.main()
