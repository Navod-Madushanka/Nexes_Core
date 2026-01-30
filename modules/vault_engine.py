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
                # Clean up and add the synonym
                clean_syn = lemma.name().replace('_', ' ')
                synonyms.add(clean_syn)
                # Keep the expansion tight (max 5) to prevent 'Query Drift'
                if len(synonyms) >= 5: 
                    return " ".join(list(synonyms))
    
    return " ".join(list(synonyms))

def query_vault(user_query, n_results=3):
    """
    Implements FR-03 (Gatekeeper) and FR-02 (Linguistic Expansion).
    """
    # Step 1: Query Expansion (FR-02)
    search_query = expand_query(user_query)
    print(f"[*] Expanded Search Terms: {search_query}")

    # Step 2: Semantic Search
    results = vault.query(
        query_texts=[search_query],
        n_results=n_results
    )

    # Step 3: Gatekeeper Logic (FR-03)
    valid_context = []
    if results['distances'] and len(results['distances'][0]) > 0:
        for i, distance in enumerate(results['distances'][0]):
            if distance <= 0.5: # 0.5 Threshold Gatekeeper
                content = results['documents'][0][i]
                meta = results['metadatas'][0][i]
                valid_context.append(f"[{meta.get('source_origin', 'VAULT')}]: {content}")
            else:
                print(f"[GATEKEEPER] Aborted result {i} - Distance {distance:.4f} > 0.5")

    return "\n".join(valid_context) if valid_context else "No relevant info found in Vault."