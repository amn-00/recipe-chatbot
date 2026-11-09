"""Task 1 analytics. Everything is computed in Python over the COMPLETE filtered
set - the LLM never produces a number. Each result carries the filters used,
the number of recipes analysed and the method, so the answer can state them.
"""
import statistics
from collections import Counter
from dataclasses import dataclass

from .constraints import Constraints
from .data import Recipe
from .normalize import canonical, is_pantry


@dataclass
class StatResult:
    title: str
    filters: str
    analysed: int          # size of the filtered set
    total: int             # size of the whole dataset (denominator for percentages)
    method: str
    rows: list             # the actual answer (numbers or ranked recipes)


def _filtered(recipes, c: Constraints):
    return [r for r in recipes if c.ok(r)]


def count(recipes: list[Recipe], c: Constraints) -> StatResult:
    hits = _filtered(recipes, c)
    pct = 100 * len(hits) / len(recipes) if recipes else 0.0
    return StatResult(
        "Recipe count", c.describe(), len(hits), len(recipes),
        "Counted recipes passing every filter. Percentage = count / total recipes in scope. "
        "Ingredient match: cleaned ingredient name contains the word (plural-insensitive, "
        "synonyms merged); different products such as 'garlic powder' do NOT count as 'garlic'.",
        [("count", len(hits)), ("percent_of_dataset", round(pct, 2))],
    )


def top_ingredients(recipes, c: Constraints, limit: int = 10) -> StatResult:
    hits = _filtered(recipes, c)
    counter = Counter()
    for r in hits:
        counter.update({canonical(n) for n in r.names if n and not is_pantry(n)})
    rows = [(name, n, round(100 * n / len(hits), 1)) for name, n in counter.most_common(limit)] if hits else []
    return StatResult(
        "Most common ingredients", c.describe(), len(hits), len(recipes),
        "Number of recipes whose cleaned ingredient names include each name (counted once per recipe). "
        "Cleaning drops quantities, units, size/prep words and text after a comma. "
        "Salt, pepper and water are left out.",
        rows,
    )


def ingredient_count_stats(recipes, c: Constraints) -> StatResult:
    hits = _filtered(recipes, c)
    sizes = [r.n_ingredients for r in hits]
    rows = []
    if sizes:
        rows = [("mean", round(statistics.mean(sizes), 2)), ("median", statistics.median(sizes)),
                ("min", min(sizes)), ("max", max(sizes))]
    return StatResult(
        "Ingredients per recipe", c.describe(), len(hits), len(recipes),
        "Ingredient count = number of non-empty ingredient lines in the original record.",
        rows,
    )


def step_count_stats(recipes, c: Constraints) -> StatResult:
    hits = _filtered(recipes, c)
    steps = [r.n_steps for r in hits]
    rows = []
    if steps:
        rows = [("mean", round(statistics.mean(steps), 2)), ("median", statistics.median(steps)),
                ("min", min(steps)), ("max", max(steps))]
    return StatResult("Instruction steps per recipe", c.describe(), len(hits), len(recipes),
                      "Step = one non-empty line/paragraph of the original instructions.", rows)


def rank_by_steps(recipes, c: Constraints, limit: int = 5, fewest: bool = True) -> StatResult:
    hits = _filtered(recipes, c)
    hits.sort(key=lambda r: (r.n_steps if fewest else -r.n_steps, r.id))
    return StatResult(
        f"{'Fewest' if fewest else 'Most'} instruction steps", c.describe(), len(hits), len(recipes),
        "Step = one non-empty line/paragraph of the original instructions. "
        "Ties broken by recipe ID so the ranking is reproducible.",
        [(r.id, r.title, r.n_steps) for r in hits[:limit]],
    )


OPS = {
    "count": count,
    "top_ingredients": top_ingredients,
    "ingredient_count": ingredient_count_stats,
    "step_count": step_count_stats,
    "rank_steps": rank_by_steps,
}
