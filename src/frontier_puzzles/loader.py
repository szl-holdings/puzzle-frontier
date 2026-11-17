import json

DATASET_ID = "SZLHOLDINGS/certified-puzzles-frontier-bank-v1"

def _read_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out

def load_all(local_path=None):
    """Load every certified item. Pulls puzzles.jsonl from the public Hugging Face
    dataset unless local_path points at a puzzles.jsonl file."""
    if local_path:
        return _read_jsonl(local_path)
    from huggingface_hub import hf_hub_download
    path = hf_hub_download(DATASET_ID, "puzzles.jsonl", repo_type="dataset")
    return _read_jsonl(path)

def load_bank(bank, local_path=None):
    """Load one bank by name (see banks.BANKS for the catalog)."""
    items = [r for r in load_all(local_path) if r.get("source", "").endswith(bank)]
    if not items:
        raise ValueError("unknown or empty bank: " + str(bank))
    return items

def get_item(item_id, local_path=None):
    for r in load_all(local_path):
        if r.get("id") == item_id:
            return r
    raise KeyError("item not found: " + str(item_id))
