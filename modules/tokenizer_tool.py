import tiktoken

def count_tokens(text: str) -> int:
    """
    FR-12: Precision token counting.
    Uses 'o200k_base' which is the closest match for the Llama-3 
    tokenization logic in a local Python environment.
    """
    try:
        # o200k_base is the encoding used by the latest Llama/GPT models
        encoding = tiktoken.get_encoding("o200k_base")
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Tokenizer Error: {e}")
        # Fallback to a rough word-count estimate if library fails
        return len(text.split()) * 1.3