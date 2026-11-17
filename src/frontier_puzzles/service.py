import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .banks import BANKS, TOTAL_ITEMS
from .loader import load_all
from .eval import score_answer

app = FastAPI(title="puzzle-frontier", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_ITEMS = None

def items():
    global _ITEMS
    if _ITEMS is None:
        _ITEMS = load_all(os.environ.get("PUZZLE_FRONTIER_JSONL") or None)
    return _ITEMS

def public_view(it):
    return {"id": it["id"], "family": it["family"], "bank": it["source"], "level": it["level"],
            "prompt": it["prompt"], "clues": it.get("clues"), "answer_format": it.get("answer_format")}

@app.get("/health")
def health():
    return {"ok": True, "n_items": len(items()), "banks": len(BANKS)}

@app.get("/banks")
def banks():
    return {"total_items": TOTAL_ITEMS, "banks": BANKS}

@app.get("/puzzle/{item_id}")
def puzzle(item_id: str):
    for it in items():
        if it["id"] == item_id:
            return public_view(it)
    raise HTTPException(status_code=404, detail="item not found")

@app.get("/random")
def random(bank: str = None, level: int = None):
    pool = items()
    if bank:
        pool = [i for i in pool if i["source"].endswith(bank)]
    if level:
        pool = [i for i in pool if i.get("level") == level]
    if not pool:
        raise HTTPException(status_code=404, detail="no item matches")
    import random as _r
    return public_view(_r.choice(pool))

class Answer(BaseModel):
    id: str
    answer: str

@app.post("/validate")
def validate(a: Answer):
    for it in items():
        if it["id"] == a.id:
            r = score_answer(it, a.answer)
            r.pop("bank", None)
            return r
    raise HTTPException(status_code=404, detail="item not found")

@app.get("/premium/random")
def premium_random(bank: str = None):
    """Premium endpoint: gated at the edge by the Cloudflare Worker x402 check."""
    return random(bank)

@app.get("/")
def root():
    web = os.environ.get("PUZZLE_FRONTIER_WEB")
    for cand in [web, "web/index.html", "../web/index.html"]:
        if cand and os.path.isfile(cand):
            return FileResponse(cand)
    return {"service": "puzzle-frontier", "docs": "/docs", "endpoints": ["/health", "/banks", "/random", "/puzzle/{id}", "/validate"]}

def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8000")))

if __name__ == "__main__":
    main()
