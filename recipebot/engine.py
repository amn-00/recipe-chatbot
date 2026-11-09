"""Load data + build the search index once, then reuse a pickle.

The cache is rebuilt automatically if any JSON file changes (name/size/mtime),
or if the code that decides what goes in the index changes.
"""
import pickle
from pathlib import Path

from .data import DATA_DIR, load_recipes
from .search import SearchIndex


def load_index(raw_dir: Path = DATA_DIR / "raw", cache: Path = DATA_DIR / "index.pkl") -> SearchIndex:
    code = [Path(__file__).parent / name for name in ("data.py", "normalize.py", "search.py")]
    stamp = [(p.name, p.stat().st_size, p.stat().st_mtime) for p in sorted(raw_dir.glob("*.json")) + code]
    if cache.exists():
        with open(cache, "rb") as f:
            saved = pickle.load(f)
        if saved["stamp"] == stamp:
            return saved["index"]
    print("Building index (first run only)...")
    recipes, report = load_recipes(raw_dir)
    index = SearchIndex(recipes, min_df=1 if len(recipes) < 1000 else 2)
    index.report = report
    cache.parent.mkdir(parents=True, exist_ok=True)
    with open(cache, "wb") as f:
        pickle.dump({"stamp": stamp, "index": index}, f)
    return index
