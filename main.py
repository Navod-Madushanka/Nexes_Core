import sys
from modules.inference import heartbeat_warmup, chat_inference
from modules.identity import load_identity
from modules.ledger_mgr import initialize_ledger, recall_memory, save_summary, consolidate_logs

def start_system():
    """
    Nexus Core Phase 2: Episodic Memory Integration.
    Orchestrates Tier 0 (Identity) and Tier 2 (Ledger) operations.
    """
    print("--- NEXUS CORE: PHASE 2 (LEDGER INTEGRATION) ---")
    
    # 1. Pre-Flight: Ollama Warm-up (FR-01)
    if not heartbeat_warmup():
        print("[!] Failed to warm up inference engine. Ensure Ollama is running.")
        return

    # 2. Identity Load & Token Budget (FR-08, FR-12)
    persona, token_total = load_identity()
    
    # 3. Initialize Tier 2 Ledger (SQLite + WAL)
    initialize_ledger()

    print(f"Nexus Core: Identity & Ledger Layers initialized.") 
    print(f"System Budget: {token_total}/500 tokens used.") 

    # Budget Gate Check (FR-12)
    if token_total <= 500:
        print("[STATUS]: PRE-FLIGHT CLEAR. System Overhead within FR-12 limits.") 
    else:
        print("[STATUS]: PRE-FLIGHT WARNING. Overhead exceeds 500 tokens.")

    print("\n" + "="*40)
    print(f"ALFRED: 'Ready for your instructions, Sir. The ledger is active.'")
    print("="*40)

    # We maintain a session log for the summary at the end
    session_history = ""

    # --- Step 2: Nexus Loop (Capture & Interceptor) ---
    while True:
        try:
            user_input = input("\nSir: ").strip()
            
            if not user_input:
                continue
            
            # EXIT SEQUENCE: Persistence & Self-Reflection (FR-04, FR-09)
            if user_input.lower() in ["/exit", "/quit"]:
                if session_history:
                    print("\nALFRED: 'One moment, Sir. Archiving session facts and lessons learned...'")
                    
                    # Refined Reflection Prompt for Fact Extraction
                    reflection_prompt = (
                        "Extract only the specific facts and user preferences from the history below. "
                        "Ignore small talk. Provide a concise, one-paragraph factual summary for the ledger."
                    )
                    
                    summary_text = chat_inference(persona, "", f"History:\n{session_history}\n\nTask: {reflection_prompt}")
                    
                    # Save to Tier 2 (SQLite) and Check Consolidation
                    save_summary(summary_text)
                    consolidate_logs()
                
                print("ALFRED: 'Very good, Sir. The Ledger is updated. Powering down.'")
                break

            injected_context = ""

            # COMMAND: /recall (Tier 2 Keyword Search)
            if user_input.startswith("/recall"):
                query = user_input.replace("/recall", "").strip()
                if query:
                    print(f"[*] Accessing Ledger for keywords: '{query}'...")
                    found_memory = recall_memory(query)
                    
                    if not found_memory:
                        print("ALFRED: 'I found no matching records in the session logs, Sir.'")
                    else:
                        injected_context = found_memory
                        print("[*] Tier 2 Context Injected.")
                        # We don't add the /recall command to session_history to keep logs clean
                        response = chat_inference(persona, injected_context, f"I have recalled some data regarding '{query}'. Please acknowledge.")
                        print(f"\nALFRED: {response}")
                        continue
                else:
                    print("ALFRED: 'Please provide a search term for the recall command, Sir.'")
                    continue

            # 4. Inference (The Nexus Loop)
            # Tier 0 (Persona) + Tier 2 (Recall) + Tier 1 (Current Input)
            response = chat_inference(persona, injected_context or "", user_input)
            
            # Update session history (Only current interaction, not injected context)
            session_history += f"User: {user_input}\nALFRED: {response}\n"
            
            print(f"\nALFRED: {response}")

        except KeyboardInterrupt:
            print("\n[!] Emergency shutdown. Data may not be archived.")
            sys.exit()

if __name__ == "__main__":
    start_system()