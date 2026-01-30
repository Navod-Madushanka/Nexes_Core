import sqlite3
import os
import hashlib
import time  # Added time import
from datetime import datetime
from modules.tokenizer_tool import count_tokens

DB_PATH = os.path.join("data", "nexus_logs.db")

def initialize_ledger():
    """Initializes the SQLite database with WAL mode and Phase 4 schema."""
    os.makedirs("data", exist_ok=True) 
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    # Changed timestamp type to REAL for float storage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL, 
            content TEXT NOT NULL,
            is_archived INTEGER DEFAULT 0,
            sha256_hash TEXT UNIQUE 
        )
    ''')
    conn.commit()
    conn.close()
    print(f"[*] Nexus Ledger initialized (WAL Mode).")

def save_summary(content):
    """Saves a summary. FR-13: Deduplicates via SHA256."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Changed to float for easier comparison (FR-16)
    timestamp = time.time() 
    
    sha256_hash = hashlib.sha256(content.encode()).hexdigest()
    try:
        cursor.execute('''
            INSERT INTO session_summaries (timestamp, content, sha256_hash, is_archived)
            VALUES (?, ?, ?, 0)
        ''', (timestamp, content, sha256_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        pass 
    finally:
        conn.close()

def recall_memory(query_text):
    """
    FR-16 Update: Returns a dictionary containing the latest timestamp 
    as a float and the combined content for Conflict Orchestration.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    search_pattern = f"%{query_text}%"
    
    # Ordering by timestamp DESC still works perfectly with floats
    cursor.execute('''
        SELECT content, timestamp FROM session_summaries 
        WHERE content LIKE ? AND is_archived = 0 
        ORDER BY timestamp DESC
    ''', (search_pattern,))
    
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None

    # latest_timestamp will now be a float
    latest_timestamp = rows[0][1]
    compiled_content = ""
    
    for content, ts in rows:
        # Convert back to readable string only for the prompt injection
        readable_ts = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n[{readable_ts}] {content}"
        
        # FR-14: Respect the 800-token limit
        if count_tokens(compiled_content + entry) > 800:
            break
        compiled_content += entry
        
    return {
        "content": compiled_content.strip(),
        "timestamp": latest_timestamp, # Returning the float
        "source": "Tier 2 (Episodic)"
    }

def consolidate_logs():
    """FR-04: Archives old logs after 7 sessions to prevent T2 bloat."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM session_summaries WHERE is_archived = 0")
    if cursor.fetchone()[0] >= 7:
        cursor.execute("UPDATE session_summaries SET is_archived = 1 WHERE is_archived = 0")
        conn.commit()
        print("[*] Tier 2 Consolidation: 7 sessions archived.")
    conn.close()