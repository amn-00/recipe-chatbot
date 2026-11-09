"""Conversation layer: session state + turning engine results into answers.

Flow per turn:  message -> LLM -> Intent -> merge with session -> engine -> formatted text.
All facts in an answer come from engine results; the text here is templates only.
"""
import re
from dataclasses import dataclass, field

from . import stats
from .constraints import Constraints, lines_violating, lines_with
from .data import Recipe
from .intent import Intent
from .matching import Have, drop_excluded, match_recipes
from .normalize import resolve_restriction, singular
from .search import SearchIndex
from .substitute import adapt

UNSUPPORTED_RE = re.compile(r"\b(?:calories?|nutrition|protein|carbs?|carbohydrates?|sodium|cholesterol|fat content|"
                            r"ratings?|reviews?|prices?|costs?|cook(?:ing)? time|prep(?:aration)? time|total time)\b", re.I)
DATASET_FIELDS = "title, ingredient lines and instruction text"
# Hard rules must not depend on the LLM catching them, so these two are also read straight from the message.
RESTRICTION_RE = re.compile(r"\b(?:without|no|avoid|exclude|cannot have|can't have)\s+"
                            r"(dairy|eggs?|peanuts?|nuts?|gluten|meat)\b", re.I)
USE_ALL_RE = re.compile(r"\b(?:use|uses|using|contain|contains|containing|include|includes|including)\s+all\b", re.I)


@dataclass
class Session:
    mode: str | None = None                  # "search", "match" or "stats"
    query: str | None = None
    stat: str | None = None                  # last statistic asked for
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)   # persists across tasks until reset/allow
    max_steps: int | None = None
    have: list[Have] = field(default_factory=list)
    prefer: list[str] = field(default_factory=list)
    last_ids: list[str] = field(default_factory=list)  # results shown last, for "#2"
    selected: str | None = None                         # recipe being discussed

    def summary(self) -> dict:
        return {"active_task": self.mode, "last_stat": self.stat, "query": self.query, "include": self.include,
                "exclude": self.exclude, "max_steps": self.max_steps,
                "have": [str(h) for h in self.have], "last_results": self.last_ids[:5],
                "selected_recipe": self.selected}

    def constraints(self) -> Constraints:
        return Constraints(list(self.include), list(self.exclude), self.max_steps)


def _add_unique(base: list[str], new: list[str]) -> list[str]:
    out = list(base)
    for x in new:
        if x.lower() not in [y.lower() for y in out]:
            out.append(x)
    return out


class Bot:
    def __init__(self, index: SearchIndex, parser=None):
        self.index = index
        self.recipes = index.recipes
        self.parser = parser
        self.s = Session()

    # ------------------------------------------------------------- entry points

    def handle(self, message: str) -> str:
        intent = self.parser.parse(message, self.s.summary())
        return self.handle_intent(intent, message)

    def handle_intent(self, it: Intent, message: str = "") -> str:
        if it.intent in ("search", "match", "stats", "substitute"):
            for word in RESTRICTION_RE.findall(message):
                if singular(word) not in [singular(e) for e in it.exclude]:
                    it.exclude.append(word.lower())
        if it.intent == "match" and USE_ALL_RE.search(message):
            it.include = [h["name"] for h in it.have]
        if it.intent in ("show", "ask", "stats", "chat", "help") and UNSUPPORTED_RE.search(message):
            it.intent, it.missing = "unsupported", UNSUPPORTED_RE.search(message).group(0)
        handler = {
            "search": self._search, "show": self._show, "ask": self._ask, "stats": self._stats, "match": self._match,
            "substitute": self._substitute, "unsupported": self._unsupported, "reset": self._reset,
        }.get(it.intent, self._help)
        return handler(it)

    # ------------------------------------------------------------- state helpers

    def _update_restrictions(self, it: Intent):
        self.s.exclude = _add_unique(self.s.exclude, it.exclude)
        if it.allow:
            allowed = {a.lower() for a in it.allow}
            self.s.exclude = [e for e in self.s.exclude if e.lower() not in allowed]

    def _resolve_recipe(self, ref: str | None) -> tuple[Recipe | None, str]:
        if ref and ref in self.index.by_id:
            return self.index.by_id[ref], ""
        m = re.fullmatch(r"#?(\d+)", ref or "")
        if m:
            n = int(m.group(1))
            return (self.index.by_id[self.s.last_ids[n - 1]], "") if 0 < n <= len(self.s.last_ids) else (None, "")
        if ref:
            # A dish name: use the best match, and say which one we picked.
            if self.s.selected and ref.lower() in self.index.by_id[self.s.selected].title.lower():
                return self.index.by_id[self.s.selected], ""
            res, _, _ = self.index.search(ref, Constraints(), limit=1)
            if res:
                r = res[0][0]
                return r, f"Using '{r.title}' ({r.id}) as the recipe. Give an ID to use a different one.\n"
            return None, ""
        if self.s.selected:
            return self.index.by_id[self.s.selected], ""
        if self.s.last_ids:
            return self.index.by_id[self.s.last_ids[0]], ""
        return None, ""

    def _footer(self) -> str:
        return f"\nActive restrictions: {', '.join(self.s.exclude)}" if self.s.exclude else ""

    # ------------------------------------------------------------- Task 1: search

    def _search(self, it: Intent) -> str:
        if it.new_topic or self.s.mode != "search":
            self.s.mode, self.s.query, self.s.include, self.s.max_steps = "search", None, [], None
        self.s.query = it.query or self.s.query
        self.s.include = _add_unique(self.s.include, it.include)
        self.s.max_steps = it.max_steps if it.max_steps is not None else self.s.max_steps
        self._update_restrictions(it)
        c = self.s.constraints()
        if not self.s.query and not c.include:
            return "What should I search for? A dish name or some ingredients."

        results, n_cand, n_ok = self.index.search(self.s.query or "", c, limit=it.limit or 5)
        self.s.last_ids = [r.id for r, _ in results]
        head = f"Search: '{self.s.query or ''}' | filters: {c.describe()}\n"
        if not results:
            return head + (f"No recipe matches. {n_cand} recipes matched the search text, but none passed the "
                           f"filters. I did not relax any restriction.") + self._footer()
        out = [head + f"{n_ok} of {n_cand} text matches pass the filters. Top {len(results)}:"]
        for i, (r, score) in enumerate(results, 1):
            out.append(f"\n{i}. {r.title}  [{r.id}]  (relevance {score:.2f}, {r.n_ingredients} ingredients, "
                       f"{r.n_steps} steps)")
            out += self._evidence(r, c)
        out.append("\nSay 'show #N' for full ingredients and instructions.")
        return "\n".join(out) + self._footer()

    def _evidence(self, r: Recipe, c: Constraints) -> list[str]:
        lines = []
        for term in c.include:
            lines.append(f"   contains {term}: " + "; ".join(lines_with(r, term)))
        for word in c.exclude:
            kind, vals = resolve_restriction(word)
            label = "/".join(vals) if kind == "category" else word
            lines.append(f"   no {label}: checked all {r.n_ingredients} ingredient lines, none match")
        if c.exclude or c.include:
            lines.append("   ingredients: " + " | ".join(r.ingredients))
        return lines

    def _show(self, it: Intent) -> str:
        r, note = self._resolve_recipe(it.recipe)
        if r is None:
            return "Which recipe? Give an ID or a result number like #1."
        self.s.selected = r.id
        out = [note + f"{r.title}  [{r.id}]", "\nIngredients:"] + [f"  - {x}" for x in r.ingredients]
        out += ["\nInstructions:"] + [f"  {i}. {s}" for i, s in enumerate(r.steps, 1)]
        flagged = [(w, lines_violating(r, w)) for w in self.s.exclude]
        flagged = [(w, ls) for w, ls in flagged if ls]
        for w, ls in flagged:
            out.append(f"\nWarning - contains {w}: " + "; ".join(ls))
        return "\n".join(out)

    def _ask(self, it: Intent) -> str:
        r, note = self._resolve_recipe(it.recipe)
        if r is None:
            return "Which recipe? Give an ID or a result number like #1."
        self.s.selected = r.id
        out = [note + f"{r.title}  [{r.id}]  - {r.n_ingredients} ingredients, {r.n_steps} steps"]
        for term in it.include:
            lines = lines_violating(r, term)
            out.append(f"{term}: yes - " + "; ".join(lines) if lines
                       else f"{term}: no - not in any of its {r.n_ingredients} ingredient lines")
        return "\n".join(out)

    def _stats(self, it: Intent) -> str:
        if it.of_those and self.s.mode == "match":
            return "I can only count within search results or earlier statistics, not ingredient matches."
        self._update_restrictions(it)
        self.s.stat = it.stat
        pool, scope = self.recipes, "the dataset"
        if it.of_those and self.s.mode == "search":        # "how many of those contain garlic?"
            found, _, _ = self.index.search(self.s.query or "", self.s.constraints(), limit=len(self.recipes))
            pool, scope = [r for r, _ in found], f"the search results for '{self.s.query}'"
            c = Constraints(include=it.include, exclude=list(self.s.exclude), max_steps=it.max_steps)
        else:
            # "Of those", or a turn that only adds a restriction, refines the last stats question.
            # Anything else starts fresh.
            refining = self.s.mode == "stats" and not it.new_topic and (
                it.of_those or (not (it.include or it.query) and (it.exclude or it.max_steps is not None)))
            if refining:
                self.s.include = _add_unique(self.s.include, it.include)
                self.s.max_steps = it.max_steps if it.max_steps is not None else self.s.max_steps
            else:
                self.s.mode, self.s.query, self.s.include, self.s.max_steps = "stats", it.query, list(it.include), it.max_steps
            c = self.s.constraints()
            c.title = self.s.query
        op = stats.OPS[it.stat]
        if it.stat == "rank_steps":
            res = op(pool, c, limit=it.limit or 5, fewest=it.fewest)
            self.s.last_ids = [row[0] for row in res.rows]
        elif it.stat == "top_ingredients":
            res = op(pool, c, limit=it.limit or 10)
        else:
            res = op(pool, c)
        out = [f"{res.title}", f"Filters: {res.filters}",
               f"Recipes analysed: {res.analysed} (total in {scope}: {res.total})", ""]
        if not res.rows:
            out.append("No recipes pass these filters, so there is nothing to compute.")
        elif it.stat == "count":
            d = dict(res.rows)
            out.append(f"Count: {d['count']}  ->  {d['count']} / {res.total} = {d['percent_of_dataset']}% of {scope}")
        elif it.stat == "rank_steps":
            out += [f"{i}. {t}  [{rid}]  - {n} steps" for i, (rid, t, n) in enumerate(res.rows, 1)]
        elif it.stat == "top_ingredients":
            out += [f"{i}. {name}: {n} recipes ({p}%)" for i, (name, n, p) in enumerate(res.rows, 1)]
        else:
            out += [f"{k}: {v}" for k, v in res.rows]
        out += ["", f"Method: {res.method}"]
        return "\n".join(out) + self._footer()

    # ------------------------------------------------------------- Task 2: match

    def _match(self, it: Intent) -> str:
        if it.new_topic or self.s.mode != "match":
            self.s.mode, self.s.have, self.s.include, self.s.max_steps, self.s.prefer = "match", [], [], None, []
        if it.have:
            self.s.have = [Have(h["name"], h["qty"], h["unit"]) for h in it.have]
        self.s.include = _add_unique(self.s.include, it.include)   # "must use X" is a hard constraint
        self.s.max_steps = it.max_steps if it.max_steps is not None else self.s.max_steps
        self.s.prefer = it.prefer or self.s.prefer
        self._update_restrictions(it)
        self.s.have, dropped = drop_excluded(self.s.have, self.s.exclude)
        if not self.s.have:
            return "Tell me which ingredients you have." + self._footer()

        c = self.s.constraints()
        res = match_recipes(self.recipes, self.s.have, c, self.s.prefer, limit=it.limit or 5)
        out = [f"Your ingredients: {', '.join(str(h) for h in self.s.have)}",
               f"Hard constraints: {c.describe()}",
               f"Ranking: {' > '.join(res.order)} > recipe ID (salt, pepper, water assumed in pantry)"]
        if all(h.qty is None for h in self.s.have):
            out.append("No quantities given: name-level match only; quantity sufficiency was not verified.")
        if dropped:
            out.append(f"Removed from your ingredients because they are now excluded: {', '.join(dropped)}")
        out.append(f"{res.n_candidates} recipes use at least one of your ingredients; {res.n_eligible} pass the constraints.")
        if res.no_match:
            self.s.last_ids = []
            out.append("\nNO MATCH: no recipe satisfies all hard constraints.")
            if res.closest:
                out.append("Closest alternatives - each one VIOLATES a constraint, shown only for reference:")
                for i, m in enumerate(res.closest, 1):
                    out.append(f"\n{i}. {m.recipe.title}  [{m.recipe.id}]  VIOLATES: {'; '.join(m.violations)}")
                    out += self._match_lines(m)
            return "\n".join(out) + self._footer()
        self.s.last_ids = [m.recipe.id for m in res.results]
        for i, m in enumerate(res.results, 1):
            out.append(f"\n{i}. {m.recipe.title}  [{m.recipe.id}]  - {m.recipe.n_steps} steps")
            out += self._match_lines(m)
            out.append(f"   why here: uses {len(m.matched)}/{len(self.s.have)} of yours, needs {len(m.extra)} extra, "
                       f"{m.recipe.n_steps} steps")
        return "\n".join(out) + self._footer()

    @staticmethod
    def _match_lines(m) -> list[str]:
        out = [f"   matched: {', '.join(m.matched) or '-'}",
               f"   not used from your list: {', '.join(m.unused) or '-'}",
               f"   missing / extra required: {'; '.join(m.extra) or 'none'}"]
        if m.pantry:
            out.append(f"   pantry (assumed): {'; '.join(m.pantry)}")
        out += [f"   qty: {n}" for n in m.quantity_notes]
        return out

    # ------------------------------------------------------------- Task 3: substitute

    def _substitute(self, it: Intent) -> str:
        self._update_restrictions(it)
        r, note = self._resolve_recipe(it.recipe)
        if r is None:
            return "Which recipe should I adapt? Give an ID, a result number like #1, or a dish name."
        self.s.selected = r.id
        res = adapt(self.index, r, it.remove, list(self.s.exclude))
        out = [note + f"Adapting: {r.title}  [{r.id}]",
               f"Change requested: remove {it.remove or '-'}; restrictions: {', '.join(self.s.exclude) or 'none'}"]
        if not res.targets:
            out.append("\nNothing in this recipe matches that ingredient or breaks the restrictions. No change needed.")
            return "\n".join(out)

        for t in res.targets:
            out.append(f"\n- Line: '{t.line}'")
            if t.target is None:
                out.append(f"  {t.note}")
                continue
            out.append(f"  Role (general knowledge): {t.target.role}")
            out.append(f"  Local evidence pool: {t.n_without + t.n_with} most similar recipes "
                       f"({t.n_without} without it, {t.n_with} with it)")
            for c in t.candidates:
                if c.status == "blocked":
                    out.append(f"    x {c.sub.name}: not allowed ({c.blocked})")
                    continue
                cite = ", ".join(c.support_ids[:5]) + (" ..." if len(c.support_ids) > 5 else "")
                line = (f"    {'>' if c is t.chosen else ' '} {c.sub.name}: {c.status} - in {len(c.support_ids)} similar "
                        f"recipes without it ({c.rate_without:.0%}) vs {c.rate_with:.0%} of those with it")
                out.append(line + (f"; e.g. {cite}" if cite else ""))
                if c.direct_ids:
                    out.append(f"      direct (title says made without it): {', '.join(c.direct_ids[:5])}")
                if c.in_recipe:
                    out.append("      note: already in this recipe, so its evidence is confounded")
            out.append(f"  {t.note}")
            if t.chosen:
                out.append(f"  Predicted effect (not verified): {t.chosen.sub.effect}")

        if not res.adapted:
            out.append("\nI can't support a reliable adaptation from the local data, so I'm not giving one.")
            return "\n".join(out) + self._footer()
        out += ["\nUpdated ingredients:"] + [f"  - {x}" for x in res.ingredients]
        out += ["\nRevised instructions:"] + [f"  {i}. {s}" for i, s in enumerate(res.steps, 1)]
        if res.unresolved:
            out.append("\nNOT resolved (no supported substitute): " + "; ".join(res.unresolved)
                       + ". The adapted recipe still contains these, so it does NOT meet the restriction.")
        out.append("\nNotes: ratios and roles are general cooking knowledge; evidence is local recipe co-occurrence, "
                   "not tested outcomes. No internet search was used. This is not a medical/allergy safety guarantee "
                   "- check product labels.")
        return "\n".join(out) + self._footer()

    # ------------------------------------------------------------- misc

    def _unsupported(self, it: Intent) -> str:
        what = it.missing or "that"
        out = [f"The dataset doesn't contain {what}. Each recipe only has a {DATASET_FIELDS} - "
               f"no nutrition, timing, rating or price fields - so I won't estimate it."]
        r, _ = self._resolve_recipe(it.recipe) if (it.recipe or self.s.selected) else (None, "")
        if r is not None and re.search(r"time", what, re.I):
            timed = [s for s in r.steps if re.search(r"\b\d+\s*(?:to\s*\d+\s*)?(?:min|minute|hour|hr)", s, re.I)]
            if timed:
                out.append(f"\nWhat the instructions of '{r.title}' say, as written (not a total time):")
                out += [f"  - {s}" for s in timed]
        return "\n".join(out)

    def _reset(self, it: Intent) -> str:
        self.s = Session()
        return "Cleared. All searches, ingredients and restrictions are reset."

    def _help(self, it: Intent) -> str:
        return ("I can: search recipes ('find a penne pasta recipe'), answer stats ('how many recipes contain "
                "garlic and onion?'), match your ingredients ('I have eggs, rice and onions'), and adapt a "
                "recipe ('remove eggs from #1'). Restrictions like 'no dairy' stay on until you say 'reset'.")
