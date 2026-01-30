import ollama

def heartbeat_warmup():
    """
    FR-01: Heartbeat Warm-up.
    Ensures model is in VRAM with a 1-hour keep_alive.
    """
    print("Nexus Core: Initializing Heartbeat (FR-01)...")
    try:
        ollama.generate(
            model='llama3.2', 
            prompt='', 
            keep_alive='1h'
        )
        print("Nexus Core: Weights pre-loaded. System Ready.")
        return True
    except Exception as e:
        print(f"Nexus Core: Heartbeat Failed. Error: {e}")
        return False

def chat_inference(persona, context, user_input):
    """
    Nexus Loop (FR-16) with Hallucination Guard.
    Explicitly tells the model what is 'Memory' vs 'Current Input'.
    """
    
    # Create a strict boundary for injected memory
    memory_block = ""
    if context:
        memory_block = (
            "\n[HISTORY_START]\n"
            f"{context}\n"
            "[HISTORY_END]\n"
            "INSTRUCTION: Use the HISTORY block above to answer. If it's empty, "
            "simply say you don't know yet. Do NOT invent system stats or directories.\n"
        )

    # Final prompt structure
    full_prompt = (
        f"{persona}\n"
        f"{memory_block}\n"
        f"USER: {user_input}\n"
        f"ALFRED:"
    )
    
    response = ollama.generate(
        model='llama3.2:latest',
        prompt=full_prompt,
        options={
            "num_predict": 200,
            "temperature": 0.1,  # Lowered to 0.1 to stop the AI from making things up
            "top_p": 0.9
        }
    )
    
    return response['response']