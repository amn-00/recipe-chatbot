"""Reproducible evaluation set.

Each conversation is a list of turns: (user message, expected intent, checks).
- Without --llm, the expected intent is fed straight to the engine, so results are
  fully deterministic (no API key needed).
- With --llm, the LLM parses the message instead, and we also score whether its
  parse agrees with the expected intent.

Checks verify properties that must hold on ANY version of the data (filters
respected, rankings sorted, numbers consistent, citations real), so they don't
depend on hard-coded answers.
"""
import re

from recipebot.constraints import lines_violating, lines_with
from recipebot.matching import DEFAULT_ORDER, score_recipe


def _results(bot):
    return [bot.index.by_id[i] for i in bot.s.last_ids]


def _clean_adapted(line):
    """For a replaced line keep only the substitute's name ('applesauce - 1/4 cup per egg [replaces ..]'
    -> 'applesauce'); the ratio text and annotation legitimately mention the old ingredient."""
    if "[replaces:" in line:
        return line.split("[replaces:")[0].rsplit(" - ", 1)[0]
    return re.sub(r"\s*\[NOT replaced[^\]]*\]", "", line)


# ---------------------------------------------------------------- checks

def says(text):
    def check(bot, reply, sub):
        return (text in reply, f"reply contains {text!r}")
    return check


def has_results(bot, reply, sub):
    return (len(bot.s.last_ids) > 0, f"{len(bot.s.last_ids)} results")


def top_mentions(word):
    def check(bot, reply, sub):
        rs = _results(bot)
        hit = [r.id for r in rs if word in r.title.lower() or lines_with(r, word)]
        return (len(hit) > 0, f"{len(hit)}/{len(rs)} results mention '{word}'")
    return check


def none_violate(restriction):
    def check(bot, reply, sub):
        bad = [(r.id, lines_violating(r, restriction)) for r in _results(bot) if lines_violating(r, restriction)]
        return (not bad, f"violations: {bad}" if bad else f"all {len(bot.s.last_ids)} results free of {restriction}")
    return check


def query_kept(text):
    def check(bot, reply, sub):
        return (bot.s.query == text, f"active query = {bot.s.query!r}")
    return check


def count_consistent(terms):
    def check(bot, reply, sub):
        from recipebot.constraints import Constraints
        from recipebot.stats import count
        both = dict(count(bot.recipes, Constraints(include=terms)).rows)["count"]
        singles = [dict(count(bot.recipes, Constraints(include=[t])).rows)["count"] for t in terms]
        again = dict(count(bot.recipes, Constraints(include=terms)).rows)["count"]
        pct = round(100 * both / len(bot.recipes), 2)
        ok = both <= min(singles) and both == again and f"{pct}%" in reply and str(len(bot.recipes)) in reply
        return (ok, f"both={both}, singles={singles}, re-run={again}, percent={pct}% stated with denominator")
    return check


def ranked_by_steps(term, n):
    def check(bot, reply, sub):
        rs = _results(bot)
        steps = [r.n_steps for r in rs]
        all_steps = sorted(r.n_steps for r in bot.recipes if lines_with(r, term))
        ok = (len(rs) == min(n, len(all_steps)) and steps == sorted(steps)
              and all(lines_with(r, term) for r in rs) and steps == all_steps[:len(steps)])
        return (ok, f"steps={steps}; global fewest={all_steps[:n]}")
    return check


def match_valid(max_steps, excluded):
    def check(bot, reply, sub):
        rs = _results(bot)
        problems = [r.id for r in rs if r.n_steps > max_steps or any(lines_violating(r, w) for w in excluded)]
        order = bot.s.prefer or ["most_matched", "fewest_extra", "fewest_steps"]
        order = order + [o for o in DEFAULT_ORDER if o not in order]
        keys = [score_recipe(r, bot.s.have).key(order) for r in rs]
        ok = rs and not problems and keys == sorted(keys)
        return (bool(ok), f"{len(rs)} results, constraint breaks: {problems or 'none'}, sorted: {keys == sorted(keys)}")
    return check


def have_dropped(name):
    def check(bot, reply, sub):
        names = [h.name for h in bot.s.have]
        return (all(name not in n for n in names), f"have now = {names}")
    return check


def no_match_reported(bot, reply, sub):
    ok = "NO MATCH" in reply and not bot.s.last_ids
    closest = reply.count("VIOLATES")
    return (ok, f"no-match stated: {ok}; closest alternatives shown (each labelled VIOLATES): {closest}")


def substitution_grounded(removed):
    def check(bot, reply, sub):
        r = bot.index.by_id[bot.s.selected]
        evidence_part = reply.split("Updated ingredients")[0]
        cited = [c for c in re.findall(r"\b(?:ar|epi|fn):[\w.\-/]+", evidence_part) if c != r.id]
        fake = [c for c in cited if c not in bot.index.by_id]
        contradict = [c for c in cited if c in bot.index.by_id and lines_with(bot.index.by_id[c], removed)]
        adapted = "Updated ingredients:" in reply
        leftover = []
        if adapted:
            block = reply.split("Updated ingredients:")[1].split("Revised instructions:")[0]
            leftover = [l for l in block.splitlines() if l.strip().startswith("-")
                        and removed in _clean_adapted(l).lower() and "NOT replaced" not in l]
        refused = "can't support" in reply
        ok = not fake and not contradict and (adapted or refused) and not leftover
        return (ok, f"adapted={adapted}, refused={refused}, cited {len(cited)} ids (missing from data: {fake}; "
                    f"still containing {removed}: {contradict}), '{removed}' left in new lines: {leftover or 'none'}")
    return check


def restriction_respected(restriction):
    def check(bot, reply, sub):
        if "Updated ingredients:" not in reply:
            return ("can't support" in reply, "no adaptation given; refusal stated")
        block = reply.split("Updated ingredients:")[1].split("Revised instructions:")[0]
        from recipebot.normalize import clean_name, violates
        bad = [l for l in block.splitlines() if l.strip().startswith("-") and "NOT replaced" not in l
               and violates(clean_name(_clean_adapted(l.strip()[2:])), restriction)]
        unresolved_flagged = ("NOT replaced" not in block) or ("does NOT meet the restriction" in reply)
        return (not bad and unresolved_flagged, f"silent violations: {bad or 'none'}; unresolved lines flagged: {unresolved_flagged}")
    return check


def evidence_labelled(bot, reply, sub):
    labels = [w for w in ("WEAK", "conflicting", "confounded", "split", "indirect", "NOT resolved",
                          "can't support", "No substitute candidates")
              if w in reply]
    return (bool(labels), f"uncertainty labels present: {labels}")


def says_missing(bot, reply, sub):
    return ("doesn't contain" in reply and "won't estimate" in reply, "states the field is missing, no estimate")


# ---------------------------------------------------------------- conversations

CONVERSATIONS = {
    "T1 multi-turn search + restriction": [
        ("Find a penne pasta recipe", {"intent": "search", "query": "penne pasta"},
         [has_results, top_mentions("penne")]),
        ("I cannot have dairy", {"intent": "search", "exclude": ["dairy"]},
         [has_results, none_violate("dairy"), query_kept("penne pasta")]),
        ("Show me the first one", {"intent": "show", "recipe": "#1"}, []),
    ],
    "T1 follow-ups about the results": [
        ("Find a penne pasta recipe", {"intent": "search", "query": "penne pasta"}, [has_results]),
        ("How many of those contain garlic?", {"intent": "stats", "stat": "count", "include": ["garlic"], "of_those": True},
         [says("the search results for 'penne pasta'")]),
        ("Does the first one contain garlic?", {"intent": "ask", "recipe": "#1", "include": ["garlic"]},
         [says("garlic: ")]),
    ],
    "T1 aggregate statistics": [
        ("How many recipes contain both garlic and onion? What percentage of the dataset is that?",
         {"intent": "stats", "stat": "count", "include": ["garlic", "onion"]},
         [count_consistent(["garlic", "onion"])]),
        ("Among recipes containing tomato, which five have the fewest instruction steps?",
         {"intent": "stats", "stat": "rank_steps", "include": ["tomato"], "limit": 5},
         [ranked_by_steps("tomato", 5)]),
        ("What are the 10 most common ingredients?", {"intent": "stats", "stat": "top_ingredients", "limit": 10}, []),
        ("What is the average and median number of ingredients?", {"intent": "stats", "stat": "ingredient_count"}, []),
    ],
    "T2 ingredient matching + follow-up": [
        ("I have eggs, onions, tomatoes, and rice. Suggest five recipes using as many of these as possible, "
         "with no peanuts and at most six instruction steps. Prefer recipes that need the fewest additional ingredients.",
         {"intent": "match", "have": [{"name": "egg"}, {"name": "onion"}, {"name": "tomato"}, {"name": "rice"}],
          "exclude": ["peanut"], "max_steps": 6, "prefer": ["most_matched", "fewest_extra"], "limit": 5},
         [has_results, match_valid(6, ["peanut"])]),
        ("Exclude eggs too", {"intent": "match", "exclude": ["eggs"]},
         [has_results, have_dropped("egg"), match_valid(6, ["peanut", "eggs"])]),
    ],
    "T2 quantities": [
        ("I have 2 cups rice and 3 eggs, what can I make?",
         {"intent": "match", "have": [{"name": "rice", "qty": 2, "unit": "cup"}, {"name": "egg", "qty": 3}]},
         [has_results]),
    ],
    "T2 no-match case": [
        ("I have saffron, durian and quinoa. Only recipes that use all three, at most 3 steps.",
         {"intent": "match", "have": [{"name": "saffron"}, {"name": "durian"}, {"name": "quinoa"}],
          "include": ["saffron", "durian", "quinoa"], "max_steps": 3, "new_topic": True},
         [no_match_reported]),
    ],
    "T3 egg-free banana bread": [
        ("Take this banana bread recipe and remove eggs. Use only ingredients that appear in the dataset. "
         "What replacements have evidence from related baked recipes, and how might the texture change?",
         {"intent": "substitute", "recipe": "banana bread", "remove": "egg"},
         [substitution_grounded("egg"), evidence_labelled]),
    ],
    "T3 dairy-free cream pasta": [
        ("Find a creamy penne alfredo with heavy cream", {"intent": "search", "query": "creamy penne alfredo heavy cream",
                                                          "include": ["cream"]}, [has_results]),
        ("Replace the cream in #1 without dairy. Prefer examples from recipes already in the database.",
         {"intent": "substitute", "recipe": "#1", "remove": "cream", "exclude": ["dairy"]},
         [restriction_respected("dairy"), evidence_labelled]),
    ],
    "T3 weak / unsupported substitution": [
        ("Remove the saffron from a saffron paella", {"intent": "substitute", "recipe": "saffron paella", "remove": "saffron"},
         [evidence_labelled]),
    ],
    "Unsupported attribute": [
        ("Find a banana bread recipe", {"intent": "search", "query": "banana bread", "new_topic": True}, [has_results]),
        ("How many calories are in the first one?", {"intent": "unsupported", "missing": "calories", "recipe": "#1"},
         [says_missing]),
        ("What's its total cooking time?", {"intent": "unsupported", "missing": "total cooking time", "recipe": "#1"},
         [says_missing]),
    ],
}
