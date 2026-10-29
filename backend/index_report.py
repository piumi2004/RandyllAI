
from pathlib import Path
import uuid

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models

# EXISTING COLLECTION — NO NEW COLLECTION
COLLECTION = "randyll_korea_knowledge_v2"
QDRANT_URL = "http://localhost:6333"

INPUT_DIR = Path("data/report_topics_staging")
MODEL_NAME = "BAAI/bge-m3"


def read_txt(file):
    """Read metadata and knowledge content from one TXT file."""
    text = file.read_text(encoding="utf-8-sig").strip()

    # Metadata is separated from content by a blank line.
    parts = text.split("\n\n", 1)

    if len(parts) != 2:
        raise ValueError(f"Missing metadata/content separator: {file}")

    header, content = parts

    metadata = {}

    for line in header.splitlines():
        key, sep, value = line.partition(":")
        if sep:
            metadata[key.strip()] = value.strip()

    return metadata, content.strip()


def main():
    # Read files from all nested folders.
    files = sorted(INPUT_DIR.rglob("*.txt"))

    print("TXT files found:", len(files))

    if len(files) != 116:
        raise RuntimeError(
            f"Expected 116 TXT files but found {len(files)}. "
            "Check the input folder before indexing."
        )

    records = []
    seen_ids = set()

    for file in files:
        metadata, content = read_txt(file)

        record_id = metadata.get("RECORD_ID")

        if not record_id:
            raise ValueError(f"Missing RECORD_ID: {file}")

        if record_id in seen_ids:
            raise ValueError(f"Duplicate RECORD_ID: {record_id}")

        if not content:
            raise ValueError(f"Empty knowledge content: {file}")

        seen_ids.add(record_id)

        records.append({
            "record_id": record_id,
            "content": content,
            "metadata": metadata,
            "file": file,
        })

    print("Records prepared:", len(records))

    # Connect to existing Qdrant collection.
    client = QdrantClient(url=QDRANT_URL)

    if not client.collection_exists(COLLECTION):
        raise RuntimeError(
            f"Existing collection not found: {COLLECTION}"
        )

    collection_info = client.get_collection(COLLECTION)
    config = collection_info.config.params.vectors

    if not isinstance(config, models.VectorParams):
        raise RuntimeError(
            "Unexpected vector configuration."
        )

    if config.size != 1024:
        raise RuntimeError(
            "Existing collection does not use 1024-dimensional vectors."
        )

    before = client.count(
        collection_name=COLLECTION,
        exact=True
    ).count

    print("Existing Qdrant points:", before)

    # Load BGE-M3 model.
    print("Loading BGE-M3...")
    encoder = SentenceTransformer(MODEL_NAME)

    # Produce embeddings for all 116 records.
    texts = [
        (
            f"Domain: {r['metadata'].get('DOMAIN', '')}\n"
            f"Topic: {r['metadata'].get('TOPIC', '')}\n"
            f"{r['content']}"
        )
        for r in records
    ]

    print("Generating embeddings...")

    vectors = encoder.encode(
        texts,
        batch_size=8,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    points = []

    for record, vector in zip(records, vectors):
        metadata = record["metadata"]

        # Same ID every time this record is indexed.
        point_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                "randyll_report:" + record["record_id"]
            )
        )

        # Keep actual review status; do NOT auto-approve.
        review_status = metadata.get(
            "REVIEW_STATUS", "unverified"
        )

        publication_status = metadata.get(
            "PUBLICATION_STATUS", "staging_only_not_approved"
        )

        # All report records are marked held until
        # the production review process approves them.
        payload = {
    "text": record["content"],
    "record_id": record["record_id"],
    "university": "General_South_Korea_Guidance",
    "topic": metadata.get("TOPIC", ""),
    "domain": metadata.get("DOMAIN", ""),
    "source_document": metadata.get("SOURCE_DOCUMENT", ""),
    "source_pages": metadata.get("PHYSICAL_PDF_PAGES", ""),
    "source_path": record["file"].as_posix(),
    "source_type": metadata.get("SOURCE_TYPE", ""),
}

        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector.tolist(),
                payload=payload,
            )
        )

    print("Uploading to:", COLLECTION)

    # Upsert replaces existing points with matching IDs.
    # All unrelated existing points remain unchanged.
    for start in range(0, len(points), 32):
        batch = points[start:start + 32]

        client.upsert(
            collection_name=COLLECTION,
            points=batch,
            wait=True,
        )

    after = client.count(
        collection_name=COLLECTION,
        exact=True
    ).count

    print("\nUPLOAD COMPLETE")
    print("Collection:", COLLECTION)
    print("TXT records processed:", len(records))
    print("Points submitted:", len(points))
    print("Points before:", before)
    print("Points after:", after)
    print("Net increase:", after - before)

    print(
        "\nReview status preserved. "
        "New report records are marked held."
    )


if __name__ == "__main__":
    main()
