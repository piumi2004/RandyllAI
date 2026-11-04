import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from backend.upload_documents import (
    MAX_FILE_BYTES,
    create_qdrant_client,
    load_embedding_model,
    upload_document_to_qdrant,
)


@st.cache_resource
def get_qdrant_client():
    return create_qdrant_client()


@st.cache_resource(show_spinner="Loading the BGE-M3 embedding model...")
def get_embedding_model():
    return load_embedding_model()


st.set_page_config(
    page_title="Update knowledge | Randyll AI",
    page_icon=":material/upload_file:",
    layout="centered",
)

st.title("Update university knowledge", icon=":material/upload_file:")

uploaded_file = st.file_uploader(
    "Document",
    type=["pdf", "txt", "md"],
    accept_multiple_files=False,
    help="Upload a text-based document up to 50 MB. Scanned PDFs need OCR first.",
    max_upload_size=50,
)

if uploaded_file:
    content = uploaded_file.getvalue()
    if len(content) > MAX_FILE_BYTES:
        st.error("The document exceeds the 50 MB upload limit.")
    elif st.button("Upload and sync to Qdrant", type="primary"):
        try:
            with st.spinner("Updating and verifying this source in Qdrant..."):
                result = upload_document_to_qdrant(
                    filename=uploaded_file.name,
                    content=content,
                    client=get_qdrant_client(),
                    embedding_model=get_embedding_model(),
                )
            if result["already_active"]:
                st.success(
                    f"{result['filename']} is already up to date. Kept "
                    f"{result['unchanged_chunks']} unchanged chunks."
                )
            elif result["matched_source"]:
                st.success(
                    f"Updated {result['filename']} in Qdrant: "
                    f"{result['updated_chunks']} changed/new chunks indexed, "
                    f"{result['unchanged_chunks']} unchanged chunks kept, and "
                    f"{result['removed_chunks']} obsolete chunks removed."
                )
            else:
                st.success(
                    f"Added {result['filename']} to Qdrant as a new document "
                    f"with {result['updated_chunks']} searchable chunks. No "
                    "existing source with that filename was found."
                )
        except (
            OSError,
            ResponseHandlingException,
            RuntimeError,
            UnexpectedResponse,
            ValueError,
        ) as error:
            st.error(f"The document was not synced: {error}")
