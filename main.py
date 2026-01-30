import sys
import os
from collections import deque
from modules.inference import heartbeat_warmup, chat_inference
from modules.identity import load_identity
from modules.ledger_mgr import initialize_ledger, recall_memory, save_summary, consolidate_logs
from modules.vault_engine import query_vault 

def start_system():
    print("--- NEXUS CORE: PHASE 3 (SEMANTIC VAULT) ---")
    
    if not heartbeat_warmup():
        print("[!] Failed to warm up inference engine.")
        return

    persona, persona_tokens = load_identity()
    BUDGET_LIMIT = 8000
    initialize_ledger()

    print(f"Nexus Core: Identity, Ledger, & Vault Layers initialized.") 
    print(f"System Budget: {persona_tokens}/{BUDGET_LIMIT} tokens used.") 

    rolling_history = deque(maxlen=10) # Reduced window for better focus
    injected_context = "" # Persistent context until next command

    while True:
        try:
            user_input = input("\nSir: ").strip()
            if not user_input: continue
            
            # --- COMMAND INTERCEPTOR ---
            if user_input.lower() in ["/exit", "/quit"]:
                if rolling_history:
                    print("\nALFRED: 'One moment, Sir. Archiving session logs...'")
                    full_history_str = "\n".join(rolling_history)
                    reflection_prompt = "Summarize the key technical facts and preferences from this session."
                    summary_text = chat_inference(persona, "", f"History:\n{full_history_str}\n\nTask: {reflection_prompt}")
                    save_summary(summary_text)
                    consolidate_logs()
                print("ALFRED: 'System offline. Have a pleasant evening, Sir.'")
                break

            elif user_input.startswith("/recall"):
                query = user_input.replace("/recall", "").strip()
                found_memory = recall_memory(query)
                if found_memory:
                    injected_context = f"[TIER 2 EPISODIC]: {found_memory}"
                    print("[*] Tier 2 Context Injected.")
                continue

            elif user_input.startswith("/vault"):
                query = user_input.replace("/vault", "").strip()
                print("[*] Performing CPU-Bound Semantic Search...")
                found_docs = query_vault(query)
                
                if "No relevant info found" not in found_docs:
                    # Clear old context and inject new Tier 3 data
                    injected_context = f"[TIER 3 VAULT DATA]: {found_docs}"
                    print("[*] Tier 3 Context Injected. ALFRED is now grounded in this data.")
                else:
                    print(f"ALFRED: {found_docs}")
                continue

            elif user_input.lower() == "/ingest":
                from modules.ingest_handler import sync_docs_folder
                sync_docs_folder()
                continue

            # --- NEXUS LOOP: INFERENCE ---
            
            # 1. Format the history
            history_str = "\n".join(list(rolling_history))
            
            # 2. Build the Augmented Prompt (The Fix)
            # We explicitly tell ALFRED to prioritize the Injected Context block.
            prompt_context = f"""
{injected_context if injected_context else "No external documents loaded."}

### INSTRUCTIONS ###
You are ALFRED. Use the [TIER 3] or [TIER 2] data above as your absolute source of truth. 
If the user asks about something in those documents, prioritize that info over your general training.
If no context is provided, rely on your core identity and history.

### HISTORY ###
{history_str}
"""
            # Generate response
            response = chat_inference(persona, prompt_context, user_input)
            
            # Update history
            rolling_history.append(f"User: {user_input}")
            rolling_history.append(f"ALFRED: {response}")
            
            print(f"\nALFRED: {response}")

        except KeyboardInterrupt:
            sys.exit()

if __name__ == "__main__":
    start_system()