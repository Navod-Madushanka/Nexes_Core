import ollama

def heartbeat_warmup():
    """
    FR-01: Heartbeat Warm-up.
    Ensures model is in VRAM with a 1-hour keep_alive.
    """
    print("Nexus Core: Initializing Heartbeat (FR-01)...")
    try:
        ollama.generate(
            model='llama3.2:latest', 
            prompt='', 
            keep_alive='1h',
            options={"num_predict": 1}
        )
        print("Nexus Core: Weights pre-loaded. System Ready.")
        return True
    except Exception as e:
        print(f"Nexus Core: Heartbeat Failed. Error: {e}")
        return False

def chat_inference(persona, context, user_input):
    """
    Nexus Loop (FR-16) - General Purpose Mega-Capacity.
    Balanced for high-context conversations and long, natural responses.
    """
    
    # Create a subtle boundary for history
    memory_block = ""
    if context:
        memory_block = (
            "\n[CONVERSATIONAL_CONTEXT]\n"
            f"{context}\n"
            "[END_OF_CONTEXT]\n"
        )

    # Clean, persona-driven prompt structure
    full_prompt = (
        f"{persona}\n"
        f"{memory_block}\n"
        f"USER: {user_input}\n"
        f"ALFRED:"
    )
    
    # 

    response = ollama.generate(
        model='llama3.2',
        prompt=full_prompt,
        options={
            "num_predict": 4096,    # High output limit remains for long explanations
            "temperature": 0.5,     # Increased to 0.5 for more natural, less "robotic" flow
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "stop": ["USER:", "ALFRED:"]
        }
    )
    
    return response['response'].strip()