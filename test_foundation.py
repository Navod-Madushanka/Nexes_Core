import sys
from modules.inference import heartbeat_warmup, chat_inference
from modules.identity import load_identity
from modules.ledger_mgr import initialize_ledger, recall_memory, save_summary, consolidate_logs

def start_system():
    print("--- NEXUS CORE: PHASE 2 (LEDGER INTEGRATION) ---")
    
    # 1. Pre-Flight: Warm-up (FR-01)
    if not heartbeat_warmup():
        print("[!] Failed to warm up inference engine.")
        return

    # 2. Identity & Budget (FR-08, FR-12)
    persona, token_total = load_identity()
    
    # 3. Initialize Ledger (Tier 2)
    initialize_ledger()

    print(f"Nexus Core: Identity & Ledger Layers initialized.") 
    print(f"System Budget: {token_total}/500 tokens used.") 

    if token_total <= 500:
        print("[STATUS]: PRE-FLIGHT CLEAR.") 
    else:
        print("[STATUS]: PRE-FLIGHT WARNING. Overhead exceeds 500 tokens.")

    print("\n" + "="*40)
    print(f"ALFRED: 'Ready for your instructions, Sir. The ledger is active.'")
    print("="*40)

    # Track session for Self-Reflection (FR-09)
    session_history = ""

    while True:
        try:
            user_input = input("\nSir: ").strip()
            
            if not user_input:
                continue
            
            # EXIT & REFLECTION LOGIC
            if user_input.lower() in ["/exit", "/quit"]:
                if session_history:
                    print("\nALFRED: 'One moment, Sir. Summarizing our discussion for the Ledger...'")
                    # Ask LLM to summarize the session_history
                    summary_prompt = "Summarize this conversation into a single concise paragraph for the archives."
                    summary_text = chat_inference(persona, "", f"History:\n{session_history}\n\nTask: {summary_prompt}")
                    
                    save_summary(summary_text)
                    consolidate_logs() # Trigger FR-04 check
                
                print("ALFRED: 'Very good, Sir. Powering down.'")
                break

            injected_context = ""

            # COMMAND: /recall
            if user_input.startswith("/recall"):
                query = user_input.replace("/recall", "").strip()
                if query:
                    print(f"[*] Searching Ledger for: '{query}'...")
                    injected_context = recall_memory(query)
                    if injected_context:
                        print("[*] Tier 2 Context Injected.")
                    else:
                        print("ALFRED: 'No matching records found, Sir.'")
                else:
                    print("ALFRED: 'Please specify keywords for recall, Sir.'")
                    continue

            # 4. Inference
            response = chat_inference(persona, injected_context or "", user_input)
            
            # Append to history for the end-of-session summary
            session_history += f"User: {user_input}\nALFRED: {response}\n"
            
            print(f"\nALFRED: {response}")

        except KeyboardInterrupt:
            print("\n[!] Emergency shutdown.")
            sys.exit()

if __name__ == "__main__":
    start_system()