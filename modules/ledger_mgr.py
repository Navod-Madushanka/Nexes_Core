import sqlite3
import os
import hashlib
from datetime import datetime
from modules.tokenizer_tool import count_tokens  # From Phase 1 [cite: 132]

# Path to the database [cite: 105]
DB_PATH = os.path.join("data", "nexus_logs.db")

def initialize_ledger():
    """
    Step 2.1: Initializes the SQLite database and creates the schema.
    Matches requirements for ER-02 (Safety) and FR-04 (Consolidation).
    """
    os.makedirs("data", exist_ok=True) 
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable Write-Ahead Logging (WAL) for data safety (ER-02) [cite: 7, 112, 150]
    cursor.execute("PRAGMA journal_mode=WAL;")

    # Define the session_summaries table schema [cite: 7, 9]
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,          -- For FR-16 conflict orchestration 
            content TEXT NOT NULL,            -- The session summary 
            is_archived INTEGER DEFAULT 0,    -- Boolean flag for FR-04 
            sha256_hash TEXT UNIQUE           -- FR-13: Prevents duplicate entries 
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"[*] Nexus Ledger initialized at {DB_PATH} (WAL Mode Enabled).")

def save_summary(content):
    """
    Saves a session summary to Tier 2 storage with deduplication.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Generate SHA256 to prevent Tier 3/Tier 2 clutter (FR-13) 
    sha256_hash = hashlib.sha256(content.encode()).hexdigest()
    
    try:
        cursor.execute('''
            INSERT INTO session_summaries (timestamp, content, sha256_hash, is_archived)
            VALUES (?, ?, ?, 0)
        ''', (timestamp, content, sha256_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        # Silently fail if the hash already exists to prevent duplicates 
        pass
    finally:
        conn.close()

def recall_memory(query_text):
    """
    Step 2.2: Handles keyword searches and enforces the 800-token cap.
    Filters by is_archived=0 for Tier 2 efficiency (FR-16).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Keyword search (Step 2.2) [cite: 117]
    search_pattern = f"%{query_text}%"
    
    # Prioritize recent logs that haven't been archived yet 
    cursor.execute('''
        SELECT content, timestamp FROM session_summaries 
        WHERE content LIKE ? AND is_archived = 0 
        ORDER BY timestamp DESC
    ''', (search_pattern,))
    
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    injected_text = "--- RELEVANT PAST CONTEXT ---"
    
    for content, timestamp in rows:
        # Prepend timestamp for Conflict Orchestrator grounding (FR-16)
        entry = f"\n[{timestamp}] {content}"
        
        # FR-12 / Step 2.2: Injection capped at 800 tokens 
        if count_tokens(injected_text + entry) > 800:
            break
            
        injected_text += entry
        
    return injected_text

def consolidate_logs():
    """
    FR-04: Merges daily logs into a 'Weekly Recap' every 7 sessions.
    Marks old logs as archived.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check how many unarchived sessions exist
    cursor.execute("SELECT COUNT(*) FROM session_summaries WHERE is_archived = 0")
    count = cursor.fetchone()[0]
    
    if count >= 7:
        print("[*] 7 Sessions reached. Triggering Weekly Consolidation...")
        # In a full implementation, you'd send these to the LLM to summarize.
        # For now, we will mark them as archived to keep the database lean.
        cursor.execute("UPDATE session_summaries SET is_archived = 1 WHERE is_archived = 0")
        conn.commit()
        print("[*] Tier 2 Consolidation complete. Logs archived.")
    
    conn.close()