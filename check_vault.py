from modules.vault_engine import vault

# 1. Check total count
count = vault.count()
print(f"[*] Total items in Vault: {count}")

# 2. Peek at data
if count > 0:
    print("[*] Previewing first entry:")
    print(vault.get(limit=1))

# 3. Test query with raw distances
query = "What is the project budget?"
results = vault.query(query_texts=[query], n_results=1)
if results['distances']:
    print(f"[*] Query: '{query}'")
    print(f"[*] Distance Score: {results['distances'][0][0]:.4f}")
    print(f"[*] Content: {results['documents'][0][0][:50]}...")