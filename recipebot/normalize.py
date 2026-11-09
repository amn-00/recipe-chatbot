"""Ingredient-name normalization and matching.

Two matching modes, on purpose:
- strict  (used for "I have X" / "must contain X" / stats): a different product
           that only shares a word does NOT count, e.g. having "garlic" does not
           cover "garlic powder", and "rice" does not cover "rice vinegar".
- broad   (used for exclusions / allergies): anything mentioning the word counts,
           e.g. "no peanuts" also removes "peanut butter" and "peanut oil".
Being broad on exclusions is the safe side; being strict on inclusions keeps
matches honest.
"""
import re
from fractions import Fraction
from functools import lru_cache

# ---------------------------------------------------------------- cleaning

UNITS = {
    "cup": "cup", "cups": "cup", "c": "cup",
    "tablespoon": "tbsp", "tablespoons": "tbsp", "tbsp": "tbsp", "tbs": "tbsp", "tbsps": "tbsp",
    "teaspoon": "tsp", "teaspoons": "tsp", "tsp": "tsp", "tsps": "tsp",
    "ounce": "oz", "ounces": "oz", "oz": "oz",
    "pound": "lb", "pounds": "lb", "lb": "lb", "lbs": "lb",
    "gram": "g", "grams": "g", "g": "g", "kilogram": "kg", "kilograms": "kg", "kg": "kg",
    "milliliter": "ml", "milliliters": "ml", "ml": "ml", "liter": "l", "liters": "l", "l": "l",
    "quart": "quart", "quarts": "quart", "qt": "quart", "pint": "pint", "pints": "pint",
    "pinch": "pinch", "pinches": "pinch", "dash": "dash", "dashes": "dash",
    "clove": "clove", "cloves": "clove", "can": "can", "cans": "can",
    "package": "package", "packages": "package", "pkg": "package",
    "slice": "slice", "slices": "slice", "stick": "stick", "sticks": "stick",
    "bunch": "bunch", "bunches": "bunch", "sprig": "sprig", "sprigs": "sprig",
    "head": "head", "heads": "head", "jar": "jar", "jars": "jar",
}

# Words that describe size/prep/state, not the ingredient itself.
DESCRIPTORS = {
    "chopped", "minced", "diced", "sliced", "grated", "shredded", "crushed", "peeled",
    "fresh", "freshly", "large", "small", "medium", "finely", "coarsely", "thinly",
    "roughly", "about", "plus", "more", "optional", "divided", "packed", "softened",
    "melted", "beaten", "lightly", "cooked", "uncooked", "whole", "halved", "quartered",
    "cubed", "trimmed", "rinsed", "drained", "mashed", "overripe", "sifted", "toasted", "room", "temperature", "to", "taste",
    "a", "an", "the", "and/or", "extra", "good", "quality", "very", "ripe",
    "skinless", "boneless", "lean",
}

UNICODE_FRACTIONS = {"½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4",
                     "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8"}

NUM = r"\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?"
_QTY_RE = re.compile(rf"^\s*({NUM})(?:\s*(?:-|to)\s*({NUM}))?\s*")


def clean_raw_line(line: str) -> str:
    """Remove the scraper artifact 'ADVERTISEMENT' (present in the allrecipes file)."""
    return re.sub(r"\s*ADVERTISEMENT\s*", " ", line or "").strip()


def _to_number(text: str) -> float:
    total = 0.0
    for part in text.split():
        total += float(Fraction(part))
    return total


def parse_quantity(line: str):
    """Leading quantity + unit of an ingredient line -> (qty, unit). Ranges use the upper bound."""
    text = line.lower()
    for k, v in UNICODE_FRACTIONS.items():
        text = text.replace(k, " " + v)
    m = _QTY_RE.match(text)
    if not m:
        return None, None
    qty = _to_number(m.group(2) or m.group(1))
    rest = re.sub(r"^\([^)]*\)\s*", "", text[m.end():]).split()
    unit = None
    if rest:
        word = rest[0].strip(".,()")
        unit = UNITS.get(word)
    return qty, unit


def _strip_words(text: str) -> str:
    """Remove numbers, units and descriptor words from one part of a line."""
    spice = re.search(r"\b(?:ground|whole) cloves?\b(?! (?:of )?garlic)", text)
    if spice:                                     # the spice, not "cloves" the unit
        return spice.group(0)
    text = re.sub(r"\d+(?:[./]\d+)?(?:\s*-\s*\d+(?:[./]\d+)?)?", " ", text)   # numbers, fractions, ranges
    words = [w.strip(".;:*") for w in text.split()]
    words = [w for w in words if w and w not in UNITS and w not in DESCRIPTORS]
    if words and words[0] == "of":                # "1 pinch of salt" -> "salt", but keep "cream of tartar"
        words = words[1:]
    return " ".join(words)


def clean_name(line: str) -> str:
    """'2 cups finely chopped onions, divided' -> 'onions'.

    Uses the first comma-separated part that still names something, so
    '4 skinless, boneless chicken breasts' -> 'chicken breasts'.
    """
    text = clean_raw_line(line).lower()
    for k, v in UNICODE_FRACTIONS.items():
        text = text.replace(k, " " + v)
    text = re.sub(r"\([^)]*\)", " ", text)       # parentheticals
    for part in text.split(","):
        name = _strip_words(part)
        if name:
            return name
    return ""


def singular(term: str) -> str:
    term = term.lower().strip()
    if term.endswith("ies"):
        return term[:-3] + "y"
    if term.endswith("oes"):
        return term[:-2]
    if term.endswith("s") and not term.endswith("ss"):
        return term[:-1]
    return term


# ---------------------------------------------------------------- term matching

# Same ingredient, different name. Key = canonical term.
SYNONYMS = {
    "green onion": ["scallion", "spring onion"],
    "cilantro": ["coriander leaf", "fresh coriander"],
    "chickpea": ["garbanzo bean"],
    "eggplant": ["aubergine"],
    "zucchini": ["courgette"],
    "bell pepper": ["capsicum"],
    "cornstarch": ["corn starch", "cornflour"],
}
_SYN_LOOKUP = {s: canon for canon, syns in SYNONYMS.items() for s in syns}

# Different products that contain the word. Only ignored in STRICT mode.
DIFFERENT_PRODUCTS = {
    "garlic": ["garlic powder", "garlic salt"],
    "onion": ["onion powder", "onion salt", "onion soup", "green onion", "spring onion"],
    "tomato": ["tomato paste", "tomato sauce", "tomato soup", "tomato juice", "tomato puree", "tomato ketchup"],
    "egg": ["egg noodle", "egg roll", "egg substitute", "egg replacer"],
    "rice": ["rice vinegar", "rice wine", "rice flour", "rice noodle", "rice paper", "rice cereal", "rice krispies", "rice milk"],
    "milk": ["coconut milk", "almond milk", "soy milk", "oat milk", "rice milk", "condensed milk", "evaporated milk"],
    "butter": ["peanut butter", "almond butter", "apple butter", "cocoa butter", "cashew butter"],
    "cream": ["cream cheese", "ice cream", "sour cream", "cream of tartar", "cream of", "coconut cream"],
    "chicken": ["chicken broth", "chicken stock", "chicken bouillon"],
    "beef": ["beef broth", "beef stock", "beef bouillon"],
    "lemon": ["lemon extract"],
    "banana": ["banana pepper"],
    "pepper": ["bell pepper", "red pepper flake", "chili pepper", "jalapeno pepper", "banana pepper"],
    "coconut": ["coconut milk", "coconut oil", "coconut cream"],
    "cheese": ["cream cheese"],
}


def _term_pattern(term: str) -> str:
    """Word-boundary regex for a term, accepting simple plurals."""
    words = singular(term).split()
    last = words[-1]
    if last.endswith("y"):
        last = re.escape(last[:-1]) + r"(?:y|ies)"
    else:
        last = re.escape(last) + r"(?:e?s)?"
    body = r"[\s-]+".join([re.escape(w) for w in words[:-1]] + [last])
    return rf"\b{body}\b"


_PATTERN_CACHE = {}


def _compiled(term: str) -> re.Pattern:
    if term not in _PATTERN_CACHE:
        _PATTERN_CACHE[term] = re.compile(_term_pattern(term))
    return _PATTERN_CACHE[term]


def term_regex(term: str, ignore_case: bool = False) -> re.Pattern:
    """Public helper: word-boundary, plural-tolerant regex for a term."""
    return re.compile(_term_pattern(term), re.I if ignore_case else 0)


def canonical(term: str) -> str:
    t = singular(term)
    return _SYN_LOOKUP.get(t, t)


def term_variants(term: str) -> list[str]:
    canon = canonical(term)
    return [canon] + SYNONYMS.get(canon, [])


@lru_cache(maxsize=None)     # the same ingredient names repeat across recipes, so remember the answers
def name_mentions(name: str, term: str, strict: bool = True) -> bool:
    """Does a cleaned ingredient name contain this ingredient?"""
    for variant in term_variants(term):
        text = name
        if strict:
            for product in DIFFERENT_PRODUCTS.get(variant, []):
                if product != variant:
                    text = _compiled(product).sub(" ", text)
        if _compiled(variant).search(text):
            return True
    return False


# ---------------------------------------------------------------- categories (for restrictions)

CATEGORIES = {
    "dairy": {
        "terms": ["milk", "butter", "cream", "cheese", "yogurt", "yoghurt", "buttermilk", "ghee",
                  "whey", "casein", "half-and-half", "half and half", "creme fraiche", "mascarpone",
                  "ricotta", "mozzarella", "parmesan", "cheddar", "feta", "paneer", "custard",
                  "gelato", "kefir", "brie", "gruyere", "romano", "provolone", "monterey jack"],
        "not": ["coconut milk", "almond milk", "soy milk", "rice milk", "oat milk", "cashew milk",
                "peanut butter", "almond butter", "cashew butter", "apple butter", "cocoa butter",
                "sunflower seed butter", "cream of tartar", "coconut cream", "cream of coconut",
                "non-dairy", "nondairy", "dairy-free", "dairy free", "vegan butter", "vegan cheese",
                "soy cheese", "butternut", "butterscotch chip"],
    },
    "egg": {"terms": ["egg", "egg yolk", "egg white", "mayonnaise", "meringue"],
            "not": ["eggplant", "egg substitute", "egg replacer", "egg-free", "eggless", "vegan mayonnaise"]},
    "peanut": {"terms": ["peanut", "groundnut"], "not": []},
    "tree_nut": {"terms": ["almond", "cashew", "walnut", "pecan", "pistachio", "hazelnut", "macadamia",
                           "pine nut", "brazil nut", "nut", "praline", "marzipan", "nutella"],
                 "not": ["nutmeg", "butternut", "water chestnut", "coconut", "doughnut", "donut", "nutritional yeast"]},
    "meat": {"terms": ["beef", "pork", "chicken", "turkey", "lamb", "bacon", "ham", "sausage", "veal",
                       "duck", "prosciutto", "salami", "pepperoni", "chorizo", "steak", "mutton", "goat",
                       "venison", "pancetta", "gelatin", "lard", "meat", "hot dog", "ground round"],
             "not": ["vegetable broth", "veggie burger", "meatless", "vegetarian", "vegan", "beefsteak tomato"]},
    "seafood": {"terms": ["fish", "salmon", "tuna", "cod", "tilapia", "shrimp", "prawn", "crab", "lobster",
                          "anchovy", "anchovies", "clam", "mussel", "oyster", "scallop", "squid", "sardine",
                          "halibut", "trout", "fish sauce", "worcestershire"],
                "not": []},
    "gluten": {"terms": ["flour", "wheat", "bread", "breadcrumb", "bread crumb", "pasta", "spaghetti",
                         "penne", "macaroni", "noodle", "couscous", "barley", "rye", "semolina", "cracker",
                         "tortilla", "soy sauce", "beer", "farro", "bulgur", "pie crust", "biscuit", "panko",
                         "fettuccine", "linguine", "lasagna", "orzo", "seitan"],
               "not": ["gluten-free", "gluten free", "rice flour", "almond flour", "coconut flour",
                       "corn flour", "cornflour", "chickpea flour", "tapioca flour", "potato flour",
                       "rice noodle", "corn tortilla", "tamari", "buckwheat"]},
}

# User words -> one or more categories.
CATEGORY_ALIASES = {
    "dairy": ["dairy"], "dairy-free": ["dairy"], "lactose": ["dairy"], "milk products": ["dairy"],
    "egg": ["egg"], "eggs": ["egg"],
    "peanut": ["peanut"], "peanuts": ["peanut"],
    "nut": ["peanut", "tree_nut"], "nuts": ["peanut", "tree_nut"], "tree nut": ["tree_nut"], "tree nuts": ["tree_nut"],
    "meat": ["meat"], "vegetarian": ["meat", "seafood"], "pescatarian": ["meat"],
    "vegan": ["meat", "seafood", "dairy", "egg"],
    "seafood": ["seafood"], "fish": ["seafood"], "shellfish": ["seafood"],
    "gluten": ["gluten"], "gluten-free": ["gluten"], "wheat": ["gluten"],
}


def resolve_restriction(word: str) -> tuple[str, list[str]]:
    """'no dairy' -> ('category', ['dairy']); 'mushrooms' -> ('term', ['mushroom'])."""
    w = word.lower().strip()
    w = re.sub(r"^(no|non|without|free of)\s+", "", w)
    if w in CATEGORY_ALIASES:
        return "category", CATEGORY_ALIASES[w]
    return "term", [singular(w)]


_CAT_RE = {
    c: (re.compile("|".join(_term_pattern(t) for t in v["terms"])),
        re.compile("|".join(_term_pattern(t) for t in v["not"])) if v["not"] else None)
    for c, v in CATEGORIES.items()
}


def in_category(name: str, category: str) -> bool:
    terms_re, safe_re = _CAT_RE[category]
    text = safe_re.sub(" ", name) if safe_re else name
    return bool(terms_re.search(text))


@lru_cache(maxsize=None)
def violates(name: str, restriction: str) -> bool:
    """Broad check of one cleaned ingredient name against a user restriction."""
    kind, values = resolve_restriction(restriction)
    if kind == "category":
        return any(in_category(name, c) for c in values)
    return any(name_mentions(name, v, strict=False) for v in values)


def may_mention(blob: str, term: str) -> bool:
    """Cheap pre-check on all of a recipe's names joined together."""
    return any(_compiled(v).search(blob) for v in term_variants(term))


def may_violate(blob: str, restriction: str) -> bool:
    kind, values = resolve_restriction(restriction)
    if kind == "category":
        return any(_CAT_RE[c][0].search(blob) for c in values)
    return any(may_mention(blob, v) for v in values)


# ---------------------------------------------------------------- pantry staples

_PANTRY_RE = re.compile(
    r"^(?:(?:kosher|sea|table|coarse|fine)\s+)?salt(?:\s+and\s+(?:ground\s+)?(?:black\s+)?pepper)?$"
    r"|^(?:ground\s+)?(?:black\s+)?pepper$"
    r"|^(?:cold|warm|hot|boiling|ice|lukewarm)?\s*water$"
)


def is_pantry(name: str) -> bool:
    """Salt, black pepper and water are assumed available when ranking matches."""
    return bool(_PANTRY_RE.match(name.strip()))
