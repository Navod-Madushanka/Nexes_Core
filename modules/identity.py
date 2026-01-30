import json
import os
from datetime import datetime
from modules.tokenizer_tool import count_tokens

def load_identity():
    """
    FR-08 & FR-12: Load Identity + Temporal Data + Budget Check
    """
    profile_path = os.path.join('data', 'user_profile.json')
    
    with open(profile_path, 'r') as f:
        data = json.load(f)
    
    # 1. Generate Temporal Data
    current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
    
    # 2. Construct the Persona Block
    persona_block = f"""
[SYSTEM OVERHEAD / TIER 0]
Current Time: {current_time}
User: {data['user_name']}
Assistant: {data['assistant_name']}

PREFERENCES: {", ".join(data['core_preferences'])}
RULES: {", ".join(data['behavior_rules'])}
LESSONS: {", ".join(data['lessons_learned'])}
"""

    # 3. Token Check (FR-12)
    t_count = count_tokens(persona_block)
    
    # Recursive Summarization Logic (Simplified for Phase 1)
    if t_count > 500:
        # If too long, we drop the 'Lessons' to save space immediately
        persona_block = persona_block.split("LESSONS:")[0] + "LESSONS: [Summarized for space]"
        t_count = count_tokens(persona_block)

    return persona_block, t_count