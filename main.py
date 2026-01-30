import sys
import os
import threading
from modules.inference import heartbeat_warmup, chat_inference
from modules.identity import load_identity
from modules.ledger_mgr import initialize_ledger, recall_memory, save_summary, consolidate_logs
from modules.vault_engine import query_vault 
from modules.tokenizer_tool import count_tokens 

def prune_tier_1(history_list):
    """
    FR-07: Async Context Pruning logic.
    Moves oldest 25% to Tier 2 via CPU-bound summarization.
    """
    slice_index = len(history_list) // 4
    if slice_index == 0: slice_index = 1 
    
    to_summarize = list(history_list)[:slice_index]
    
    def background_task():
        content = "\n".join(to_summarize)
        # Summarizing for the Ledger (Tier 2)
        summary = chat_inference("System", "Summarize these facts for Tier 2 storage.", content)
        save_summary(summary) 
        print(f"\n[*] FR-07: {len(to_summarize)} messages archived to Tier 2.")

    threading.Thread(target=background_task, daemon=True).start()
    return list(history_list)[slice_index:]

def start_system():
    print("--- NEXUS CORE: PHASE 4 (DYNAMIC CONTEXT & ORCHESTRATION) ---")
    
    if not heartbeat_warmup():
        print("[!] Failed to warm up inference engine.")
        return

    persona, persona_tokens = load_identity()
    initialize_ledger()

    # FR-14: Define the Elastic Parameters
    BASE_T1_LIMIT = 2048
    CONTEXT_RESERVE = 800
    
    rolling_history = [] 
    
    # State management for FR-16 Orchestration
    t2_context = None # Stores {content, timestamp, source}
    t3_context = None # Stores {content, timestamp, source}

    print(f"Nexus Core: Identity, Ledger, & Vault Layers initialized.") 

    while True:
        try:
            # --- STEP 4.2: DYNAMIC BUDGET CALCULATION (FR-14) ---
            has_active_context = t2_context or t3_context
            current_t1_threshold = BASE_T1_LIMIT + (0 if has_active_context else CONTEXT_RESERVE)
            
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

            elif user_input.lower() == "/clear":
                t2_context = None
                t3_context = None
                print(f"[*] Context cleared. Tier 1 budget expanded.")
                continue

            elif user_input.startswith("/recall"):
                query = user_input.replace("/recall", "").strip()
                t2_context = recall_memory(query)
                if t2_context:
                    # Note: t2_context['timestamp'] is now a float
                    print(f"[*] Tier 2 Context Injected.")
                continue

            elif user_input.startswith("/vault"):
                query = user_input.replace("/vault", "").strip()
                print("[*] Performing CPU-Bound Semantic Search...")
                t3_context = query_vault(query) 
                
                if t3_context and "No relevant info found" not in str(t3_context):
                    print(f"[*] Tier 3 Context Injected.")
                else:
                    print(f"ALFRED: No relevant vault data found.")
                    t3_context = None
                continue

            elif user_input.lower() == "/ingest":
                from modules.ingest_handler import sync_docs_folder
                sync_docs_folder()
                continue
            
            # --- STEP 4.1 & 4.2: THE ELASTIC GUARD ---
            if count_tokens("\n".join(rolling_history)) > current_t1_threshold:
                print(f"[*] Elasticity Triggered: Shrinking history to accommodate context...")
                rolling_history = prune_tier_1(rolling_history)

            # --- STEP 4.3: CONFLICT ORCHESTRATOR (FR-16) ---
            warning_block = ""
            injected_str = "No external documents loaded."
            
            if t2_context and t3_context:
                # UPDATED: Now both are floats, so this is a clean numerical comparison
                if t3_context['timestamp'] > t2_context['timestamp']:
                    warning_block = "\n[!] SYSTEM: Vault data is more recent. Prioritizing Tier 3.\n"
                else:
                    warning_block = "\n[!] SYSTEM: Session logs are more recent. Prioritizing Tier 2.\n"

                # Debug Print (Optional):
                # print(f"DEBUG: T2 TS: {t2_context['timestamp']} | T3 TS: {t3_context['timestamp']}")

            if has_active_context:
                content_2 = t2_context['content'] if t2_context else "None"
                content_3 = t3_context['content'] if t3_context else "None"
                injected_str = f"{warning_block}\n[TIER 2]: {content_2}\n\n[TIER 3]: {content_3}"

            # --- NEXUS LOOP: INFERENCE ---
            history_str = "\n".join(rolling_history)
            
            prompt_context = f"""
{injected_str}

### INSTRUCTIONS ###
You are ALFRED. Use the [TIER 3] or [TIER 2] data above as your absolute source of truth. 
If data conflicts, prioritize the entry specifically flagged in the SYSTEM warning.

### HISTORY ###
{history_str}
"""
            response = chat_inference(persona, prompt_context, user_input)
            
            rolling_history.append(f"User: {user_input}")
            rolling_history.append(f"ALFRED: {response}")

            print(f"\nALFRED: {response}")

        except KeyboardInterrupt:
            sys.exit()

if __name__ == "__main__":
    start_system()