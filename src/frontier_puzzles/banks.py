BANKS = {
    "zebra_fresh": {"family": "zebra", "size": "5 houses x 4 categories", "n": 100, "kind": "fresh-seed eval", "note": "contamination-free eval at the released size"},
    "zebra_f7": {"family": "zebra", "size": "7 houses x 5 categories", "n": 100, "kind": "new size", "note": "largest certified Zebra bank in existence"},
    "futoshiki_f7": {"family": "futoshiki", "size": "7x7", "n": 100, "kind": "new size", "note": "beyond the released 6x6"},
    "sudoku_f12": {"family": "sudoku", "size": "12x12 (box 3x4)", "n": 59, "kind": "new size", "note": "largest certified Sudoku in the bank; 59 of 60 bank items in this release"},
    "killer_f9": {"family": "killer", "size": "9x9 (box 3x3)", "n": 17, "kind": "new size", "note": "the classic Killer size; 17 of 20 bank items in this release, heavy re-certification continues"},
    "killer_fresh": {"family": "killer", "size": "6x6", "n": 60, "kind": "fresh-seed eval", "note": "contamination-free eval at the released size"},
}

BANK_COUNTS = {name: meta["n"] for name, meta in BANKS.items()}
TOTAL_ITEMS = sum(BANK_COUNTS.values())
