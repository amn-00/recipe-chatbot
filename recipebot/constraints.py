"""Hard constraints shared by search, stats and matching.

Every check returns the ingredient lines that caused it, so answers can show
evidence instead of just saying "dairy-free".
"""
from dataclasses import dataclass, field

from .data import Recipe
from .normalize import may_mention, may_violate, name_mentions, term_regex, violates


def lines_with(recipe: Recipe, term: str, strict: bool = True) -> list[str]:
    if not may_mention(recipe.blob, term):
        return []
    return [line for line, name in zip(recipe.ingredients, recipe.names) if name_mentions(name, term, strict)]


def lines_violating(recipe: Recipe, restriction: str) -> list[str]:
    # Restrictions check the whole original line, so a cleaning mistake can't let a forbidden item through.
    if not may_violate(recipe.raw_blob, restriction):
        return []
    return [line for line in recipe.ingredients if violates(line.lower(), restriction)]


@dataclass
class Constraints:
    include: list[str] = field(default_factory=list)   # must contain all (strict match)
    exclude: list[str] = field(default_factory=list)   # must contain none (broad match)
    max_steps: int | None = None
    title: str | None = None                           # phrase the title must contain (used by stats)

    def violations(self, recipe: Recipe) -> list[str]:
        """Empty list = recipe is eligible. Otherwise human-readable reasons."""
        out = []
        if self.title and not term_regex(self.title, ignore_case=True).search(recipe.title):
            out.append(f"title does not contain '{self.title}'")
        if self.max_steps is not None and recipe.n_steps > self.max_steps:
            out.append(f"has {recipe.n_steps} steps (max {self.max_steps})")
        for term in self.include:
            if not lines_with(recipe, term):
                out.append(f"does not contain '{term}'")
        for word in self.exclude:
            bad = lines_violating(recipe, word)
            if bad:
                out.append(f"contains {word}: " + "; ".join(f"'{b}'" for b in bad))
        return out

    def ok(self, recipe: Recipe) -> bool:
        if self.max_steps is not None and recipe.n_steps > self.max_steps:
            return False
        return not self.violations(recipe)

    def describe(self) -> str:
        parts = []
        if self.title:
            parts.append(f"title contains '{self.title}'")
        if self.include:
            parts.append("contains " + " AND ".join(self.include))
        if self.exclude:
            parts.append("excludes " + ", ".join(self.exclude))
        if self.max_steps is not None:
            parts.append(f"at most {self.max_steps} steps")
        return "; ".join(parts) if parts else "no filters"
