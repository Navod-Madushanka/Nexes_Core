import os
import hashlib
import time
from PIL import Image
import pytesseract
from tqdm import tqdm # Required for FR-15 TUI Progress Bar
from modules.vault_engine import vault # Tier 3 ChromaDB collection

DOCS_DIR = os.path.join("data", "docs")

def get_file_hash(file_path):
    """FR-13: Generate SHA256 hash for de-duplication."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files without RAM spikes
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def process_file(file_name):
    """Extracts text and adds to Tier 3 Vault."""
    path = os.path.join(DOCS_DIR, file_name)
    file_hash = get_file_hash(path)
    
    # FR-13: De-duplication check against the vector store
    existing = vault.get(ids=[file_hash])
    if existing and existing['ids']:
        return "duplicate"

    content = ""
    # FR-10: Multi-Modal Ingestion (OCR for Images)
    if file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
        try:
            content = pytesseract.image_to_string(Image.open(path))
        except Exception as e:
            print(f"\n[!] OCR Error on {file_name}: {e}")
    # Standard Text Ingestion
    elif file_name.lower().endswith('.txt'):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    
    if content.strip():
        # FR-16: Include timestamp and source for Conflict Orchestration
        vault.add(
            documents=[content],
            metadatas=[{
                "source_origin": file_name, 
                "timestamp": time.time(), # Critical for FR-16 "Current Truth" logic
                "hash": file_hash
            }],
            ids=[file_hash]
        )
        return "success"
    return "empty"

def sync_docs_folder():
    """
    FR-05: Throttled Ingestion.
    FR-15: TUI Ingestion Queue Progress Bar.
    """
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        
    files = [f for f in os.listdir(DOCS_DIR) if not f.startswith('.')]
    if not files:
        print("[!] No files found in /docs/ to ingest.")
        return

    print(f"[*] Nexus Core: Syncing {len(files)} files to Tier 3...")
    
    # FR-15: Implementation of the TUI Ingestion Queue progress bar
    for f in tqdm(files, desc="Ingesting Vault", unit="file", colour="green"):
        status = process_file(f)
        
        if status == "success":
            # FR-05: 10-second delay to prevent CPU thermal throttling
            time.sleep(10) 
        elif status == "duplicate":
            # No delay needed for skipped files
            continue 
    
    print("[*] Ingestion Cycle Complete.")