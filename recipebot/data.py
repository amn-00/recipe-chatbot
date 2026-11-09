"""Load the Recipe Box dataset (all three JSON files) into Recipe objects.

Stable ID  = "<source>:<original key>", e.g. "ar:rmK12Uau.ntP510KeImX506H6Mr6jTu".
             The source prefix (ar / epi / fn) avoids collisions between files.
Originals  = title, ingredient lines and instructions are kept exactly as in the
             file; only the scraper artifact "ADVERTISEMENT" is stripped.
Step rule  = one step = one non-empty line (paragraph) of the original
             instructions text, ignoring lines that are not cooking steps
             (video links, photo credits, equipment lists).
"""
import json
import re
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from .normalize import clean_name, clean_raw_line

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SOURCES = {"ar": "allrecipes", "epi": "epicurious", "fn": "foodnetwork"}
NOT_A_STEP = re.compile(r"^(watch how to make this recipe|photograph by|special equipment:|this recipe was)", re.I)


@dataclass
class Recipe:
    id: str
    title: str
    ingredients: list[str]          # original lines (ADVERTISEMENT removed)
    instructions: str               # original text
    names: list[str] = field(default_factory=list)   # cleaned names, aligned with ingredients
    steps: list[str] = field(default_factory=list)

    @cached_property
    def blob(self) -> str:
        """All cleaned names joined; used for fast pre-checks before per-line matching."""
        return " | ".join(self.names)

    @cached_property
    def raw_blob(self) -> str:
        """All original lines joined, lower-case; the same pre-check for restrictions."""
        return " | ".join(self.ingredients).lower()

    @property
    def n_steps(self) -> int:
        return len(self.steps)

    @property
    def n_ingredients(self) -> int:
        return len(self.ingredients)


def split_steps(instructions: str) -> list[str]:
    lines = [clean_raw_line(s) for s in (instructions or "").split("\n")]
    return [s for s in lines if s and not NOT_A_STEP.match(s)]


def _source_of(path: Path) -> str:
    for code in SOURCES:
        if path.stem.endswith("_" + code):
            return code
    return path.stem


@dataclass
class LoadReport:
    files: list[str]
    loaded: int
    skipped: dict  # reason -> count


def load_recipes(raw_dir: Path) -> tuple[list[Recipe], LoadReport]:
    files = sorted(raw_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No JSON files in {raw_dir}. Run: python scripts/download_data.py")
    recipes, skipped = [], {"empty record": 0, "no title": 0, "no ingredients": 0, "no instructions": 0}
    for path in files:
        source = _source_of(path)
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        for key, rec in raw.items():
            if not rec:
                skipped["empty record"] += 1
                continue
            title = (rec.get("title") or "").strip()
            lines = [clean_raw_line(x) for x in (rec.get("ingredients") or [])]
            lines = [x for x in lines if x]
            instructions = rec.get("instructions") or ""
            steps = split_steps(instructions)
            if not title:
                skipped["no title"] += 1
            elif not lines:
                skipped["no ingredients"] += 1
            elif not steps:
                skipped["no instructions"] += 1
            else:
                recipes.append(Recipe(
                    id=f"{source}:{key}", title=title, ingredients=lines, instructions=instructions,
                    names=[clean_name(x) for x in lines], steps=steps,
                ))
    return recipes, LoadReport([p.name for p in files], len(recipes), skipped)

