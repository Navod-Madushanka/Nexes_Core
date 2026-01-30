import ollama

def heartbeat_warmup():
    """
    FR-01: Heartbeat Warm-up
    Sends a null prompt to Ollama to force-load the model into VRAM.
    """
    print("Nexus Core: Initializing Heartbeat (FR-01)...")
    try:
        # We use a blank prompt. 'keep_alive' ensures it stays in VRAM.
        # 'stream=False' waits for the model to fully load before continuing.
        ollama.generate(
            model='llama3.2', 
            prompt='', 
            keep_alive='1h'
        )
        print("Nexus Core: Weights pre-loaded. System Ready.")
        return True
    except Exception as e:
        print(f"Nexus Core: Heartbeat Failed. Ensure Ollama is running. Error: {e}")
        return False