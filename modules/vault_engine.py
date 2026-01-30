import chromadb
from chromadb.utils import embedding_functions
from nltk.corpus import wordnet # FR-02 Requirement

# Initialize ChromaDB
client = chromadb.PersistentClient(path="data/chroma_store")
cpu_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="mixedbread-ai/mxbai-embed-large-v1",
    device="cpu"
)

vault = client.get_or_create_collection(
    name="semantic_vault", 
    embedding_function=cpu_ef,
    metadata={"hnsw:space": "cosine"}
)

def expand_query(query):
    """
    FR-02: CPU-Bound Query Expansion using WordNet.
    Ensures that if you search for 'funds', it can find 'budget'.
    """
    synonyms = {query}
    # Analyze each word for synonyms
    for word in query.split():
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                clean_syn = lemma.name().replace('_', ' ')
                synonyms.add(clean_syn)
                if len(synonyms) >= 5: 
                    return " ".join(list(synonyms))
    
    return " ".join(list(synonyms))

def query_vault(user_query):
    """
    Final Phase 4 Version: Implements FR-03 (Gatekeeper) and returns 
    the best matching structured dictionary for FR-16 Orchestration.
    """
    # Step 1: Query Expansion (FR-02)
    search_query = expand_query(user_query)
    
    # Step 2: Semantic Search (Requesting 1 best match for the orchestrator)
    results = vault.query(
        query_texts=[search_query],
        n_results=1
    )

    # Step 3: Gatekeeper Logic (FR-03)
    if results['distances'] and len(results['distances'][0]) > 0:
        distance = results['distances'][0][0]
        
        # 0.5 Threshold Gatekeeper: Prevents Hallucinations
        if distance <= 0.5:
            content = results['documents'][0][0]
            meta = results['metadatas'][0][0]
            
            # FR-16: Force the timestamp to a float for easier comparison
            # Default to 0.0 (Unix Epoch) if missing
            raw_ts = meta.get("timestamp", 0)
            
            # Return the dictionary format main.py is waiting for
            return {
                "content": content,
                "timestamp": float(raw_ts), 
                "source": f"Tier 3 Vault ({meta.get('source_origin', 'Unknown')})",
                "distance": distance
            }
        else:
            print(f"[*] Gatekeeper: Best vault match too weak ({distance:.4f} > 0.5). Ignoring.")

    return None # Returns None if nothing is relevant