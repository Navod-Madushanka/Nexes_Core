from modules.inference import heartbeat_warmup
from modules.identity import load_identity

def start_system():
    print("--- NEXUS CORE: PHASE 1 FINAL ---")
    
    # Step 1.1: Heartbeat
    if not heartbeat_warmup():
        return

    # Step 1.2 & 1.3: Identity & Token Budget
    persona, token_total = load_identity()
    
    print(f"Nexus Core: Identity Layer initialized.")
    print(f"Token Budget: {token_total}/500 tokens used.")

    if token_total <= 500:
        print("[STATUS]: PRE-FLIGHT CLEAR. System Overhead within FR-12 limits.")
    else:
        print("[STATUS]: PRE-FLIGHT WARNING. Overhead exceeds 500 tokens.")

    print("\n" + "="*40)
    print(f"ALFRED: 'Ready for your instructions, Sir. The current time is noted.'")
    print("="*40)


if __name__ == "__main__":
    start_system()