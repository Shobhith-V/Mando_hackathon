from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')
index = faiss.IndexFlatL2(384)
docs = []  # List of (text, source)

def add_to_index(chunks):
    global docs
    embeddings = model.encode([c for c, _ in chunks])
    index.add(np.array(embeddings).astype('float32'))
    docs.extend(chunks)

def search(query, top_k=5):
    query_embedding = model.encode([query])
    D, I = index.search(np.array(query_embedding).astype('float32'), top_k)
    return [docs[i] for i in I[0]]
