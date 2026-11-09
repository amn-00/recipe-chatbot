"""Unit tests on a small fixture in the real dataset format. Run: pytest -q"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from recipebot.bot import UNSUPPORTED_RE, Bot
from recipebot.constraints import Constraints, lines_violating
from recipebot.data import Recipe, load_recipes, split_steps
from recipebot.intent import Intent
from recipebot.matching import Have, _quantity_note, match_recipes
from recipebot.normalize import clean_name, is_pantry, name_mentions, parse_quantity, violates
from recipebot.search import SearchIndex
from recipebot.substitute import TARGETS, Candidate, Sub, _rewrite_step, _status
from recipebot import stats

RAW = Path(__file__).parent / "fixtures" / "raw"


@pytest.fixture(scope="module")
def index():
    recipes, _ = load_recipes(RAW)
    return SearchIndex(recipes, min_df=1)


# ---------------------------------------------------------------- normalization

def test_clean_name_and_quantity():
    assert clean_name("2 cups finely chopped onions, divided") == "onions"
    assert clean_name("1 (28 ounce) can crushed tomatoes") == "tomatoes"
    assert clean_name("1 cup flourADVERTISEMENT") == "flour"
    assert parse_quantity("1 1/2 cups milk") == (1.5, "cup")
    assert parse_quantity("½ cup sugar") == (0.5, "cup")
    assert parse_quantity("3 large eggs") == (3.0, None)


def test_clean_name_commas_and_of():
    assert clean_name("4 skinless, boneless chicken breast halves") == "chicken breast halves"
    assert violates(clean_name("4 skinless, boneless chicken breast halves"), "vegetarian")
    assert clean_name("1 large, ripe tomato") == "tomato"
    assert clean_name("1 pinch of salt") == "salt"
    assert not violates(clean_name("1 teaspoon cream of tartar"), "dairy")
    assert not name_mentions(clean_name("1 can cream of mushroom soup"), "cream")


def test_restrictions_check_the_whole_original_line():
    line = "1 (8 pound) cured, bone-in ham"
    recipe = Recipe("x:1", "Ham", [line], "Bake.", [clean_name(line)], ["Bake."])
    assert lines_violating(recipe, "vegetarian") == [line]


def test_step_rule_ignores_non_steps():
    assert split_steps("Watch how to make this recipe.\nMix.\nPhotograph by Someone\nBake.") == ["Mix.", "Bake."]


def test_strict_vs_broad():
    assert not name_mentions("garlic powder", "garlic", strict=True)
    assert name_mentions("garlic powder", "garlic", strict=False)
    assert not name_mentions("rice vinegar", "rice")
    assert name_mentions("scallions", "green onion")          # synonym
    assert not name_mentions("eggplant", "egg", strict=False)  # word boundary


def test_categories():
    assert violates("heavy cream", "dairy") and violates("parmesan cheese", "no dairy")
    assert not violates("coconut milk", "dairy") and not violates("peanut butter", "dairy")
    assert violates("peanut oil", "peanuts") and not violates("nutmeg", "nuts")
    assert violates("chicken broth", "vegetarian")
    assert is_pantry("salt and pepper") and not is_pantry("bell pepper")


def test_loader_ids_and_steps():
    recipes, report = load_recipes(RAW)
    ids = [r.id for r in recipes]
    assert len(ids) == len(set(ids)) and all(i.split(":")[0] in {"ar", "epi", "fn"} for i in ids)
    assert report.skipped["empty record"] == 1 and report.skipped["no title"] == 1
    assert split_steps("a\n\nb\nADVERTISEMENT\n") == ["a", "b"]


# ---------------------------------------------------------------- Task 1

def test_search_refines_with_restriction(index):
    res, _, _ = index.search("penne pasta", Constraints(exclude=["dairy"]))
    assert res and all(not lines_violating(r, "dairy") for r, _ in res)


def test_stats_use_full_set(index):
    c = stats.count(index.recipes, Constraints(include=["garlic", "onion"]))
    brute = sum(1 for r in index.recipes
                if any(name_mentions(n, "garlic") for n in r.names) and any(name_mentions(n, "onion") for n in r.names))
    assert dict(c.rows)["count"] == brute
    ranked = stats.rank_by_steps(index.recipes, Constraints(include=["tomato"]), limit=5)
    steps = [n for _, _, n in ranked.rows]
    assert steps == sorted(steps)


# ---------------------------------------------------------------- Task 2

def test_match_and_no_match(index):
    have = [Have(x) for x in ["egg", "onion", "tomato", "rice"]]
    res = match_recipes(index.recipes, have, Constraints(exclude=["peanut"], max_steps=6))
    assert not res.no_match and all(m.recipe.n_steps <= 6 for m in res.results)
    none = match_recipes(index.recipes, [Have("saffron")], Constraints(max_steps=1))
    assert none.no_match and all(m.violations for m in none.closest)


# ---------------------------------------------------------------- chat wiring (fake LLM)

class FakeParser:
    def __init__(self, replies):
        self.replies = iter(replies)

    def parse(self, message, state):
        return Intent.from_dict(next(self.replies))


def test_follow_up_keeps_query_and_adds_restriction(index):
    bot = Bot(index, FakeParser([{"intent": "search", "query": "penne pasta"},
                                 {"intent": "search", "exclude": ["dairy"]}]))
    bot.handle("Find a penne pasta recipe")
    reply = bot.handle("I cannot have dairy")
    assert bot.s.query == "penne pasta" and "excludes dairy" in reply
    assert all(not lines_violating(index.by_id[i], "dairy") for i in bot.s.last_ids)


def test_substitution_cites_real_recipes(index):
    bot = Bot(index, FakeParser([{"intent": "substitute", "recipe": "banana bread", "remove": "egg"}]))
    reply = bot.handle("remove eggs from banana bread")
    assert "Updated ingredients" in reply or "can't support" in reply
    assert "ar:ar0004" in reply            # the eggless banana bread is cited as evidence


def test_unsupported_and_bad_llm_output(index):
    bot = Bot(index, FakeParser([{"intent": "search", "query": "banana bread"}, {"intent": "nonsense", "max_steps": "x"}]))
    bot.handle("banana bread")
    assert "doesn't contain" in bot.handle_intent(Intent(intent="unsupported", missing="calories"), "calories?")
    assert "I can" in bot.handle("???")    # invalid intent falls back to help, no crash


def test_normal_requests_are_not_refused(index):
    bot = Bot(index, None)
    reply = bot.handle_intent(Intent(intent="search", query="banana bread"), "Find a spaghetti carbonara recipe")
    assert "doesn't contain" not in reply
    assert not UNSUPPORTED_RE.search("grating carrots for a Costa Rican carbonara")
    assert UNSUPPORTED_RE.search("how many calories?")


def test_stats_title_filter_and_follow_up(index):
    bot = Bot(index, None)
    reply = bot.handle_intent(Intent(intent="stats", stat="count", query="banana bread"), "")
    expected = sum("banana bread" in r.title.lower() for r in index.recipes)
    assert f"Recipes analysed: {expected} " in reply and expected < len(index.recipes)
    reply = bot.handle_intent(Intent(intent="stats", stat="count", exclude=["dairy"]), "and without dairy?")
    assert "title contains 'banana bread'" in reply and "excludes dairy" in reply
    reply = bot.handle_intent(Intent(intent="stats", stat="count", include=["garlic"]), "how many have garlic?")
    assert "title contains" not in reply and "excludes dairy" in reply   # restriction stays until reset


def test_result_number_out_of_range_is_not_guessed(index):
    bot = Bot(index, None)
    bot.handle_intent(Intent(intent="search", query="banana bread"), "")
    assert "Which recipe?" in bot.handle_intent(Intent(intent="show", recipe="#99"), "")


def test_candidate_already_in_recipe_is_conflicting():
    c = Candidate(Sub("mashed banana", "banana", "", ""), support_ids=["a", "b", "c"],
                  rate_without=0.5, rate_with=0.1, in_recipe=True)
    assert _status(c) == "conflicting"


def test_hard_rules_are_kept_if_the_llm_misses_them(index):
    bot = Bot(index, None)
    bot.handle_intent(Intent(intent="search", query="pasta", exclude=["peanut"]), "pasta with no peanuts and no dairy")
    assert bot.s.exclude == ["peanut", "dairy"]
    bot = Bot(index, None)
    have = [{"name": "saffron", "qty": None, "unit": None}, {"name": "rice", "qty": None, "unit": None}]
    bot.handle_intent(Intent(intent="match", have=have), "only recipes that use all of them")
    assert bot.s.include == ["saffron", "rice"]


def test_ground_cloves_stay_an_ingredient():
    assert clean_name("1/4 teaspoon ground cloves") == "ground cloves"
    assert clean_name("2 cloves garlic") == "garlic"
    assert clean_name("2 whole cloves garlic") == "garlic"


def test_quantity_accepts_plural_units():
    assert "enough" in _quantity_note(Have("rice", 2, "cups"), ["1 cup rice"])


def test_butter_as_a_verb_is_not_replaced_by_the_ingredient():
    butter = SimpleNamespace(target=next(t for t in TARGETS if t.key == "butter"),
                             chosen=SimpleNamespace(sub=SimpleNamespace(name="vegetable oil")))
    assert _rewrite_step("Butter a pan. Melt the butter.", butter) == "Grease a pan. Melt the vegetable oil."


def test_ask_about_one_recipe(index):
    bot = Bot(index, None)
    bot.handle_intent(Intent(intent="search", query="banana bread"), "")
    reply = bot.handle_intent(Intent(intent="ask", recipe="#1", include=["banana", "anchovy"]), "")
    assert "banana: yes" in reply and "anchovy: no" in reply and "steps" in reply


def test_stats_of_those_uses_the_search_results(index):
    bot = Bot(index, None)
    bot.handle_intent(Intent(intent="search", query="banana bread"), "")
    expected = len(index.search("banana bread", Constraints(), limit=len(index.recipes))[0])
    reply = bot.handle_intent(Intent(intent="stats", stat="count", include=["banana"], of_those=True), "")
    assert f"total in the search results for 'banana bread': {expected})" in reply


def test_intent_coercion():
    it = Intent.from_dict(json.loads('{"intent":"match","have":["egg",{"name":"rice","qty":"2","unit":"cup"}],"max_steps":"6"}'))
    assert it.max_steps == 6 and it.have[1]["qty"] == 2.0 and it.have[0]["name"] == "egg"
