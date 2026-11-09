"""Task 3: evidence-based ingredient substitution.

Two clearly separated sources:
  * CANDIDATES - which substitutes are worth checking, and their usual ratios and
    effects. This is general cooking knowledge written in this file (labelled
    "general knowledge" in every answer). It is a short list, not an oracle.
  * EVIDENCE   - comes only from the local dataset. For the recipe being adapted
    we take its most similar recipes (TF-IDF), split them into those that still
    use the ingredient and those that don't, and check how often each candidate
    appears in each group.

        rate_without = share of similar recipes WITHOUT the ingredient that use the candidate
        rate_with    = share of similar recipes WITH the ingredient that use the candidate
        lift         = rate_without - rate_with

    A candidate that shows up much more when the ingredient is missing is
    plausibly doing its job. Titles like "eggless" / "dairy-free" count as direct
    evidence. Everything else is indirect (co-occurrence, not a tested swap) and
    is labelled that way.

No internet search is used. Effects on taste/texture are predictions, never
verified outcomes - the dataset has no ratings or results to verify them.
"""
import re
from dataclasses import dataclass, field

from .constraints import lines_with
from .data import Recipe
from .normalize import name_mentions, resolve_restriction, term_regex, violates
from .search import SearchIndex

POOL_SIZE = 1500     # similar recipes examined
MIN_SUPPORT = 3      # fewer supporting recipes than this = weak evidence


@dataclass
class Sub:
    name: str
    term: str            # how it is looked up in the dataset
    ratio: str
    effect: str          # predicted, not verified
    prep: str = ""


@dataclass
class Target:
    key: str
    terms: list[str]     # names that identify this ingredient in a recipe line
    role: str
    free_words: list[str]   # title words that mark a recipe as made without it
    subs: list[Sub]


# Ordered most-specific first: "sour cream" must be found before "cream".
TARGETS = [
    Target("sour cream", ["sour cream"], "tang, moisture and richness",
           ["dairy-free", "vegan", "non-dairy"],
           [Sub("plain yogurt", "yogurt", "1:1", "very similar tang; slightly thinner"),
            Sub("coconut cream", "coconut cream", "1:1", "rich but adds coconut flavour, less tangy")]),
    Target("buttermilk", ["buttermilk"], "acidity for leavening, moisture, tenderness",
           ["dairy-free", "vegan"],
           [Sub("plain yogurt", "yogurt", "3/4 cup yogurt + 1/4 cup water per cup", "similar tang and tenderness"),
            Sub("soy milk", "soy milk", "1 cup + 1 tbsp lemon juice per cup", "less tang; rise may be a little lower",
                "Stir 1 tbsp lemon juice into each cup of soy milk; let stand 5 minutes."),
            Sub("almond milk", "almond milk", "1 cup + 1 tbsp lemon juice per cup", "thinner and less tangy",
                "Stir 1 tbsp lemon juice into each cup of almond milk; let stand 5 minutes.")]),
    Target("cream", ["heavy cream", "whipping cream", "cream", "half-and-half", "half and half"],
           "fat, richness and body; thickens sauces when reduced",
           ["dairy-free", "vegan", "non-dairy", "without cream"],
           [Sub("coconut milk", "coconut milk", "1:1 (full-fat)", "similar body; adds mild coconut flavour"),
            Sub("cashews blended with water", "cashew", "1/2 cup soaked cashews + 1/2 cup water per cup",
                "creamy and neutral; slightly grainy if not blended well",
                "Soak cashews, then blend with water until completely smooth."),
            Sub("olive oil + reserved pasta water", "olive oil", "2 tbsp oil + 1/2 cup pasta water per cup",
                "much lighter, glossy rather than creamy"),
            Sub("vegetable broth", "vegetable broth", "1:1, reduce longer", "thinner and savoury, far less rich")]),
    Target("butter", ["butter"], "fat for flavour, tenderness and browning",
           ["dairy-free", "vegan", "butterless"],
           [Sub("vegetable oil", "vegetable oil", "3/4 the amount of butter", "moister, denser crumb; less buttery flavour"),
            Sub("olive oil", "olive oil", "3/4 the amount of butter", "fruity flavour; fine for savoury dishes"),
            Sub("coconut oil", "coconut oil", "1:1", "closest texture when solid; faint coconut flavour"),
            Sub("applesauce", "applesauce", "1/2 the amount of butter", "lower fat, more cake-like and moist")]),
    Target("milk", ["milk"], "liquid and moisture; some fat and browning",
           ["dairy-free", "vegan", "non-dairy"],
           [Sub("soy milk", "soy milk", "1:1", "very similar; neutral"),
            Sub("almond milk", "almond milk", "1:1", "thinner, slightly nutty"),
            Sub("oat milk", "oat milk", "1:1", "neutral, slightly sweet"),
            Sub("coconut milk", "coconut milk", "1:1 (light) ", "richer, coconut flavour"),
            Sub("water", "water", "1:1", "works but less rich; less browning")]),
    Target("yogurt", ["yogurt", "yoghurt"], "tang, moisture and tenderness",
           ["dairy-free", "vegan"],
           [Sub("sour cream", "sour cream", "1:1", "richer, similar tang"),
            Sub("applesauce", "applesauce", "1:1 (baking only)", "moist, no tang, sweeter"),
            Sub("coconut cream", "coconut cream", "1:1", "rich, coconut flavour, little tang")]),
    Target("cheese", ["parmesan", "cheese", "mozzarella", "cheddar", "romano", "feta"],
           "salty, savoury flavour; melting/binding when heated",
           ["dairy-free", "vegan", "cheeseless"],
           [Sub("nutritional yeast", "nutritional yeast", "about 1/2 the amount", "savoury, cheesy-ish flavour; does not melt"),
            Sub("toasted breadcrumbs", "breadcrumb", "1:1 as a topping", "crunch instead of savoury creaminess")]),
    Target("egg", ["egg"], "binding and structure, moisture, some leavening in baking",
           ["eggless", "egg-free", "egg free", "vegan", "without eggs", "no-egg", "no egg"],
           [Sub("mashed banana", "banana", "1/4 cup per egg", "moister and denser; banana flavour"),
            Sub("applesauce", "applesauce", "1/4 cup per egg", "moist, denser, slightly sweeter"),
            Sub("ground flaxseed + water", "flax", "1 tbsp flax + 3 tbsp water per egg",
                "good binder; slightly nutty, a bit gummy",
                "Mix ground flaxseed with water and let it thicken for 5 minutes."),
            Sub("plain yogurt", "yogurt", "1/4 cup per egg", "tender and moist; slight tang"),
            Sub("buttermilk", "buttermilk", "1/4 cup per egg", "tender; less structure"),
            Sub("silken tofu, blended", "tofu", "1/4 cup per egg", "dense and moist; neutral flavour")]),
    Target("peanut butter", ["peanut butter"], "fat, body and nutty flavour",
           ["peanut-free", "nut-free"],
           [Sub("sunflower seed butter", "sunflower", "1:1", "similar texture; earthier taste"),
            Sub("tahini", "tahini", "1:1", "thinner and more bitter/savoury")]),
    Target("soy sauce", ["soy sauce"], "salt and umami",
           ["soy-free", "gluten-free"],
           [Sub("tamari", "tamari", "1:1", "nearly identical (still soy; usually gluten-free)"),
            Sub("worcestershire sauce", "worcestershire", "1/2 the amount", "tangier, less salty")]),
    Target("wine", ["white wine", "red wine", "wine"], "acidity and depth in sauces",
           ["alcohol-free", "non-alcoholic"],
           [Sub("chicken broth", "chicken broth", "1:1", "savoury, no acidity - add a splash of vinegar"),
            Sub("vegetable broth", "vegetable broth", "1:1", "savoury, no acidity"),
            Sub("red wine vinegar", "vinegar", "1 tbsp vinegar + water to volume", "sharper acidity")]),
]


@dataclass
class Candidate:
    sub: Sub
    support_ids: list[str] = field(default_factory=list)   # similar recipes w/o the ingredient that use it
    direct_ids: list[str] = field(default_factory=list)    # ...whose title says it's made without it
    rate_without: float = 0.0
    rate_with: float = 0.0
    in_recipe: bool = False
    blocked: str = ""        # why it can't be used (restriction)
    status: str = ""         # supported / weak / conflicting / none / blocked

    @property
    def lift(self):
        return self.rate_without - self.rate_with


@dataclass
class TargetResult:
    line: str
    target: Target | None
    candidates: list[Candidate]
    chosen: Candidate | None
    n_with: int
    n_without: int
    note: str


@dataclass
class SubstitutionResult:
    recipe: Recipe
    targets: list[TargetResult]
    ingredients: list[str]
    steps: list[str]
    adapted: bool
    unresolved: list[str]


def find_target(name: str) -> tuple[Target, str] | tuple[None, None]:
    for t in TARGETS:
        for term in t.terms:
            if name_mentions(name, term, strict=True):
                return t, term
    return None, None


def _status(c: Candidate) -> str:
    if c.blocked:
        return "blocked"
    n = len(c.support_ids)
    if n == 0:
        return "none"
    if c.lift <= 0 or c.in_recipe:
        return "conflicting"
    return "supported" if n >= MIN_SUPPORT else "weak"


RANK = {"supported": 0, "weak": 1, "conflicting": 2, "none": 3, "blocked": 4}


def evaluate_target(index: SearchIndex, recipe: Recipe, line: str, name: str,
                    restrictions: list[str], pool) -> TargetResult:
    target, term = find_target(name)
    if target is None:
        return TargetResult(line, None, [], None, 0, 0,
                            "No substitute candidates are known for this ingredient, so no adaptation is proposed.")
    has_it = [r for r in pool if lines_with(r, term, strict=True)]
    has_id = {r.id for r in has_it}
    without = [r for r in pool if r.id not in has_id]
    free = re.compile("|".join(re.escape(w) for w in target.free_words), re.I)

    cands = []
    for sub in target.subs:
        c = Candidate(sub)
        blocked = [w for w in restrictions if violates(sub.term, w)]
        if name_mentions(sub.term, target.key, strict=True):
            blocked.append(target.key)
        if blocked:
            c.blocked = "conflicts with: " + ", ".join(blocked)
        c.support_ids = [r.id for r in without if lines_with(r, sub.term)]
        c.direct_ids = [r.id for r in without if free.search(r.title) and lines_with(r, sub.term)]
        n_with_sub = sum(1 for r in has_it if lines_with(r, sub.term))
        c.rate_without = len(c.support_ids) / len(without) if without else 0.0
        c.rate_with = n_with_sub / len(has_it) if has_it else 0.0
        c.in_recipe = bool(lines_with(recipe, sub.term))
        c.status = _status(c)
        cands.append(c)
    cands.sort(key=lambda c: (RANK[c.status], -len(c.direct_ids), -c.lift, -len(c.support_ids)))

    chosen = cands[0] if cands and cands[0].status in ("supported", "weak") else None
    if chosen is None:
        note = ("Local evidence is not enough to support any substitute that fits the restrictions. "
                "No adaptation is proposed for this line.")
    elif chosen.status == "weak":
        note = f"WEAK evidence: only {len(chosen.support_ids)} similar recipe(s) support this. Treat as a guess."
    else:
        note = "Evidence is indirect (similar recipes made without it), not a tested swap." if not chosen.direct_ids \
            else "Includes direct evidence: similar recipes whose titles say they are made without it."
        runner = next((c for c in cands[1:] if c.status == "supported"), None)
        if runner and runner.lift >= 0.8 * chosen.lift:
            note += f" Evidence is split: '{runner.sub.name}' is almost as well supported."
    return TargetResult(line, target, cands, chosen, len(has_it), len(without), note)


def _mentions_regex(target: Target) -> re.Pattern:
    """Matches a run of target words, so 'Parmesan cheese' becomes one replacement."""
    alt = "|".join(term_regex(t).pattern for t in sorted(target.terms, key=len, reverse=True))
    return re.compile(rf"(?:{alt})(?:\s+(?:{alt}))*", re.I)


VERBS = {"butter": "Grease", "cream": "Beat"}     # "Butter a pan" is an action, not the ingredient


def _rewrite_step(step: str, t: TargetResult) -> str:
    verb = VERBS.get(t.target.key)
    if verb:
        step = re.sub(rf"(^|[.!;]\s+){t.target.key}(?=\s+(?:and flour\s+)?(?:a|an|the|your|two|one|together|sugar|butter)\b)",
                      rf"\g<1>{verb}", step, flags=re.I)
    return _mentions_regex(t.target).sub(t.chosen.sub.name, step)


def adapt(index: SearchIndex, recipe: Recipe, remove: str | None, restrictions: list[str]) -> SubstitutionResult:
    # Lines to change = the ingredient the user named + anything breaking a restriction.
    def is_named(line, name):
        if not remove:
            return False
        if resolve_restriction(remove)[0] == "category":     # "remove dairy"
            return violates(line.lower(), remove)
        return name_mentions(name, remove, strict=True)       # "remove cream" (not cream cheese)

    to_change = []
    for line, name in zip(recipe.ingredients, recipe.names):
        if is_named(line, name) or any(violates(line.lower(), w) for w in restrictions):
            to_change.append((line, name))

    pool = [r for r, _ in index.similar(recipe, POOL_SIZE)]
    targets = [evaluate_target(index, recipe, line, name, restrictions, pool) for line, name in to_change]

    ingredients, prep, unresolved = [], [], []
    replaced = {t.line: t for t in targets}
    for line in recipe.ingredients:
        t = replaced.get(line)
        if t is None:
            ingredients.append(line)
        elif t.chosen:
            ingredients.append(f"{t.chosen.sub.name} - {t.chosen.sub.ratio}   [replaces: {line}]")
            if t.chosen.sub.prep:
                prep.append(t.chosen.sub.prep)
        else:
            ingredients.append(f"{line}   [NOT replaced - see notes]")
            unresolved.append(line)

    steps = [f"[added] {p}" for p in prep]
    for step in recipe.steps:
        new = step
        for t in targets:
            if t.chosen:
                new = _rewrite_step(new, t)
        steps.append(f"[changed] {new}" if new != step else step)

    adapted = any(t.chosen for t in targets)
    return SubstitutionResult(recipe, targets, ingredients, steps, adapted, unresolved)
