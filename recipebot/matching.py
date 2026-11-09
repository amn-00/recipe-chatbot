"""Task 2: rank EXISTING recipes against the ingredients a user has.

Ranking is lexicographic, so every position can be explained in one line:
  1. more of your ingredients used        (higher is better)
  2. fewer extra ingredients you'd need   (salt, pepper, water assumed in pantry)
  3. fewer instruction steps
  4. recipe ID (only to make ties reproducible)
The user can reorder 1-3 with `prefer`.

Hard constraints (exclusions, max steps) are filters, never score penalties.
If nothing passes them we say so, and show the closest recipes separately,
each labelled with the constraint it breaks.
"""
import re
from dataclasses import dataclass, field

from .constraints import Constraints, lines_with
from .data import Recipe
from .normalize import UNITS, is_pantry, parse_quantity, singular, violates

DEFAULT_ORDER = ["most_matched", "fewest_extra", "fewest_steps"]
COOKED = re.compile(r"\bcooked\b", re.I)   # 2 cups raw rice != 2 cups cooked rice


@dataclass
class Have:
    name: str
    qty: float | None = None
    unit: str | None = None

    def __str__(self):
        if self.qty is None:
            return self.name
        return f"{self.qty:g} {self.unit + ' ' if self.unit else ''}{self.name}"


@dataclass
class Match:
    recipe: Recipe
    matched: list[str]                 # your ingredients the recipe uses
    unused: list[str]                  # your ingredients it doesn't use
    extra: list[str]                   # recipe lines you don't have (excluding pantry)
    pantry: list[str]                  # recipe lines assumed available
    quantity_notes: list[str]
    violations: list[str] = field(default_factory=list)

    def key(self, order):
        parts = {"most_matched": -len(self.matched), "fewest_extra": len(self.extra),
                 "fewest_steps": self.recipe.n_steps}
        return tuple(parts[o] for o in order) + (self.recipe.id,)


@dataclass
class MatchResult:
    results: list[Match]
    no_match: bool
    closest: list[Match]               # only filled when no_match; each violates something
    n_candidates: int
    n_eligible: int
    order: list[str]
    constraints: Constraints


def _quantity_note(item: Have, lines: list[str]) -> str | None:
    if item.qty is None:
        return None
    for line in lines:
        if bool(COOKED.search(line)) != bool(COOKED.search(item.name)):
            return f"{item.name}: quantity not verified ('{line}' is cooked, yours is not, or vice versa)"
        need, unit = parse_quantity(line)
        if need is not None and unit == UNITS.get((item.unit or "").lower(), item.unit):   # "cups" == "cup"
            verdict = "enough" if item.qty >= need else f"NOT enough (recipe needs {need:g})"
            return f"{item.name}: you have {item}, recipe uses '{line}' -> {verdict}"
    return f"{item.name}: quantity not verified (recipe line '{lines[0]}' uses a different or no unit)"


def score_recipe(recipe: Recipe, have: list[Have]) -> Match:
    matched, unused, notes, covered = [], [], [], set()
    for item in have:
        lines = lines_with(recipe, item.name, strict=True)
        if lines:
            matched.append(item.name)
            covered.update(lines)
            note = _quantity_note(item, lines)
            if note:
                notes.append(note)
        else:
            unused.append(item.name)
    extra, pantry = [], []
    for line, name in zip(recipe.ingredients, recipe.names):
        if line in covered:
            continue
        (pantry if is_pantry(name) else extra).append(line)
    return Match(recipe, matched, unused, extra, pantry, notes)


def match_recipes(recipes: list[Recipe], have: list[Have], constraints: Constraints,
                  prefer: list[str] | None = None, limit: int = 5) -> MatchResult:
    order = [p for p in (prefer or []) if p in DEFAULT_ORDER]
    order += [p for p in DEFAULT_ORDER if p not in order]

    # Candidates = recipes using at least one of your ingredients.
    candidates = [r for r in recipes if any(lines_with(r, h.name) for h in have)]
    eligible, rejected = [], []
    for r in candidates:
        bad = constraints.violations(r)
        (rejected if bad else eligible).append((r, bad))

    scored = sorted((score_recipe(r, have) for r, _ in eligible), key=lambda m: m.key(order))
    if scored:
        return MatchResult(scored[:limit], False, [], len(candidates), len(eligible), order, constraints)

    # Nothing passes the hard constraints: show the closest, clearly marked.
    closest = []
    for r, bad in rejected:
        m = score_recipe(r, have)
        m.violations = bad
        closest.append(m)
    closest.sort(key=lambda m: (len(m.violations),) + m.key(order))
    return MatchResult([], True, closest[:3], len(candidates), 0, order, constraints)


def drop_excluded(have: list[Have], excluded: list[str]) -> tuple[list[Have], list[str]]:
    """'Exclude eggs too' must also remove eggs from what we try to use."""
    keep, dropped = [], []
    for h in have:
        if any(violates(singular(h.name), word) for word in excluded):
            dropped.append(h.name)
        else:
            keep.append(h)
    return keep, dropped
