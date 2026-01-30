import torch
from chromadb.utils import embedding_functions
import time

def validate_cpu_pinning():
    print("--- Nexus Core Phase 3 Hardware Audit ---")
    
    # 1. Initialize the embedding function as defined in vault_engine.py
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="mixedbread-ai/mxbai-embed-large-v1",
        device="cpu"
    )
    
    # 2. Access the underlying model to check its device
    # SentenceTransformer uses PyTorch; we check the first parameter's device
    underlying_model = ef._model
    model_device = next(underlying_model.parameters()).device
    
    print(f"[CHECK] Embedding Model Device: {model_device}")
    
    if "cpu" in str(model_device):
        print("✅ SUCCESS: Model is pinned to CPU.")
    else:
        print("❌ WARNING: Model is on GPU. This will conflict with Llama VRAM.")

    # 3. VRAM Usage Check
    if torch.cuda.is_available():
        vram_before = torch.cuda.memory_allocated()
        _ = ef(["This is a test to check VRAM leakage."])
        vram_after = torch.cuda.memory_allocated()
        
        leakage = vram_after - vram_before
        print(f"[CHECK] VRAM Leakage during embedding: {leakage} bytes")
        
        if leakage == 0:
            print("✅ SUCCESS: 0.0 GB VRAM consumed by Tier 3.")
        else:
            print("❌ FAIL: Vectorizing is consuming GPU resources.")
    else:
        print("[INFO] No CUDA detected; defaulting to CPU is confirmed.")

if __name__ == "__main__":
    validate_cpu_pinning()