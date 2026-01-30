import ollama
from modules.inference import heartbeat_warmup
from modules.identity import load_identity

def run_phase_1_audit():
    print("=== NEXUS CORE: PHASE 1 AUDIT ===")
    errors = 0

    # Test 1: Ollama & Heartbeat
    print("\n[1/3] Testing Heartbeat (FR-01)...")
    if heartbeat_warmup():
        print("PASS: Model loaded into VRAM.")
    else:
        print("FAIL: Could not contact Ollama.")
        errors += 1

    # Test 2: Identity Injection
    print("\n[2/3] Testing Identity Injection (FR-08)...")
    persona, t_count = load_identity()
    if "ALFRED" in persona and "Navod" in persona:
        print("PASS: Identity loaded correctly from JSON.")
    else:
        print("FAIL: Identity block is missing key profile data.")
        errors += 1

    # Test 3: Token Budget
    print("\n[3/3] Testing Token Budget (FR-12)...")
    print(f"Current Size: {t_count} tokens.")
    if t_count <= 500:
        print("PASS: System overhead is within the 500-token limit.")
    else:
        print("FAIL: Identity is too large for the System Budget.")
        errors += 1

    # Final Inference Test
    if errors == 0:
        print("\n" + "="*40)
        print("ALL SYSTEMS NOMINAL. RUNNING LIVE INFERENCE...")
        print("="*40)
        
        try:
            test_query = "ALFRED, confirm status and identify yourself."
            response = ollama.chat(model='llama3.2', messages=[
                {'role': 'system', 'content': persona},
                {'role': 'user', 'content': test_query},
            ])
            print(f"\nALFRED: {response['message']['content']}")
        except Exception as e:
            print(f"Inference Error: {e}")
    else:
        print(f"\nAUDIT FAILED: {errors} error(s) found. Fix before Phase 2.")

if __name__ == "__main__":
    run_phase_1_audit()