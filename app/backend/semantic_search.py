# backend/semantic_search.py
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')
index = []

def clear_index():
    global index
    index = []

def add_to_index(chunks):
    global index
    embeddings = model.encode([chunk[0] for chunk in chunks])
    for chunk, embedding in zip(chunks, embeddings):
        index.append((chunk, embedding))

def search(query, top_k=5):
    if not index:
        return []
    
    query_embedding = model.encode([query])[0]
    similarities = []
    
    for chunk, embedding in index:
        similarity = np.dot(embedding, query_embedding)
        similarities.append((chunk, similarity))
    
    return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]