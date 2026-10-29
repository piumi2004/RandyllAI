import torch
from sentence_transformers import SentenceTransformer

print("CUDA available:", torch.cuda.is_available())

model = SentenceTransformer(
    "BAAI/bge-m3",
    device="cuda"
)

sentences = [
    "What are the admission requirements for Korean universities?",
    "What is the tuition fee for international students?",
    "What documents are required for a D-2 student visa?"
]

embeddings = model.encode(
    sentences,
    batch_size=3,
    convert_to_numpy=True
)

print("Model device:", model.device)
print("Embedding shape:", embeddings.shape)
print("Embedding generation successful!")