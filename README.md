# Recipe Box Chatbot

A conversational chatbot that searches, analyses, matches and adapts recipes from the
[Recipe Box dataset](https://eightportions.com/datasets/Recipes/) (all three JSON files, ~125k recipes).

The main idea: **the LLM only understands the question; code produces every fact.**
The LLM turns a message into a small JSON request (intent, ingredients, restrictions...).
Search, counts, rankings and substitution evidence are all computed in Python over the data,
and every answer shows the filters, the number of recipes analysed and the recipe IDs behind it.

## Run it

Needs Python 3.10+.

```bash
pip install -r requirements.txt
python scripts/download_data.py          # puts the 3 JSON files in data/raw/
cp .env.example .env                     # add a free Groq or Google AI Studio key
python chat.py                           # first run builds the index (~1 min), then it's cached
```

If the download script fails, download `recipes_raw.zip` from the dataset page and unzip the three
`recipes_raw_nosource_*.json` files into `data/raw/`.

`python chat.py --debug` also prints the parsed request for each message.

Tests and evaluation:

```bash
pytest -q                                # unit tests on a small fixture (no key, no download)
python -m eval.run_eval                  # eval set on the full data, deterministic, no key -> eval/RESULTS.md
python -m eval.run_eval --llm            # same, but the LLM parses the messages too
python -m eval.one_shot_baseline         # plain LLM vs this system -> eval/BASELINE.md
```

## Example session

```
you> Find a penne pasta recipe
you> I cannot have dairy                  -> same search, now filtered, with ingredient evidence
you> How many recipes contain both garlic and onion? What percentage is that?
you> Among recipes containing tomato, which five have the fewest instruction steps?
you> I have eggs, onions, tomatoes and rice. Five recipes, no peanuts, at most 6 steps
you> Exclude eggs too
you> Take this banana bread recipe and remove eggs
you> Replace the cream in #1 without dairy
you> reset
```

## How it works

```
message -> LLM (JSON request only) -> session merge -> engine -> templated answer
                                                        |- search.py      Task 1 search
                                                        |- stats.py       Task 1 analytics
                                                        |- matching.py    Task 2
                                                        |- substitute.py  Task 3
```

| File | What it does |
|---|---|
| `recipebot/data.py` | Loads the 3 files, stable IDs, step rule, drops invalid records |
| `recipebot/normalize.py` | Ingredient-name cleaning, synonyms, strict/broad matching, diet categories |
| `recipebot/constraints.py` | Hard filters (must contain / exclude / max steps) with evidence lines |
| `recipebot/search.py` | TF-IDF index over title + ingredient names |
| `recipebot/stats.py` | Counts, percentages, common ingredients, mean/median, step rankings |
| `recipebot/matching.py` | Ranks recipes against what you have |
| `recipebot/substitute.py` | Evidence-based substitution and adapted recipe |
| `recipebot/intent.py`, `llm.py` | Request schema + LLM parser (any OpenAI-compatible API) |
| `recipebot/bot.py` | Session state (follow-ups) and answer formatting |

## Design decisions

**Data and IDs.** ID = `<source>:<original key>` (`ar`, `epi`, `fn`), so it is stable and never collides
across files. Title, ingredient lines and instructions are kept as in the file; only the scraper
artifact `ADVERTISEMENT` is removed. Records with no title, ingredients or instructions are skipped and
counted (shown at startup).

**Step rule.** One step = one non-empty line (paragraph) of the original instructions, ignoring lines
that aren't cooking steps (video links, photo credits, equipment lists). Simple and reproducible, but it
depends on how each site formatted the text (some recipes are one paragraph).

**Ingredient normalization.** Each line is cleaned to a name: quantities, units, parentheticals and
size/prep words are removed, and the name is the first comma-separated part that still names something
(`2 cups finely chopped onions, divided` -> `onions`, `4 skinless, boneless chicken breasts` ->
`chicken breasts`). Matching is word-boundary and plural-insensitive, with a small synonym table
(scallion = green onion, garbanzo = chickpea...). Two modes:
- **strict** for "contains" / "I have": different products don't count. `garlic` does not cover
  `garlic powder`, `rice` does not cover `rice vinegar`, `tomato` does not cover `tomato paste`.
- **broad** for exclusions: anything on the whole original line mentioning the word counts, so a cleaning
  mistake can't let a forbidden item through. "No peanuts" also removes peanut oil
  and peanut butter. Over-excluding is the safe side for restrictions.

Diet words map to categories (`dairy`, `egg`, `nuts`, `gluten`, `vegetarian`, `vegan`...) with explicit
exceptions (coconut milk and peanut butter are not dairy, nutmeg is not a nut).

**Retrieval.** TF-IDF (unigrams + bigrams) over title (counted twice) + cleaned ingredient names.
Queries are dish names and ingredients, which are lexical, so TF-IDF works well, is deterministic,
fast, needs no model download and is easy to explain. Restrictions are applied to **every** scored
recipe, not to a small top-k, so "no dairy" can't be lost after retrieval.

**Computation.** Counts, percentages, means, medians and rankings run over the complete filtered set.
Percentages use all loaded recipes as the denominator, unless the question is about current search results. Ties are broken by recipe ID so results are
reproducible. The LLM never sees or produces these numbers.

**Follow-ups.** The session keeps the active task (search or match), its query/ingredients and the
restrictions. A new restriction refines the active task. Restrictions stay on (shown under every
answer) until the user says `reset` or allows the item again; they are never dropped silently.
"#2" refers to the 2nd result shown last. For statistics, a turn that only adds a restriction ("and
without dairy?") refines the last question; a turn with its own filters starts a new one. "How many of
those..." counts within the full set of current search results, and that set becomes the denominator.

**LLM safety net.** Testing showed the LLM sometimes drops a hard rule, so "no dairy"-style restrictions
and "use all of them" are also read from the message by a small regex in `bot.py`.

**Vague requests.** For something like "light for summer", the LLM rewrites the request into concrete
dish and ingredient words. The search text is shown in the answer, and results still come only from the data.

**Matching (Task 2).** Candidates = recipes using at least one of your ingredients. Hard constraints
are filters, never score penalties. Ranking is lexicographic so every position has a one-line reason:
1) more of your ingredients used, 2) fewer extra ingredients needed (salt, pepper, water assumed in the
pantry and listed separately), 3) fewer steps, 4) recipe ID. The user can reorder 1-3. Each result shows
matched, not-used and extra-required ingredients. If nothing passes the constraints, the answer says
**NO MATCH** and shows the closest recipes separately, each labelled with what it violates.
Quantities are compared only when the recipe line uses the same unit (and both are raw or both
cooked); otherwise it says "not verified".

**Substitution (Task 3).** Two sources, kept separate in every answer:
- *Candidates* (which substitutes to check, typical ratio, role of the ingredient, predicted effect)
  come from a short hand-written table of general cooking knowledge in `substitute.py`, and are
  labelled as such.
- *Evidence* comes only from the local data. Take the 1,500 recipes most similar to the one being
  adapted, split them into those that still use the ingredient and those that don't, and for each
  candidate compare how often it appears in each group. A candidate that is much more common when the
  ingredient is absent is plausibly replacing it. Recipes whose titles say "eggless", "dairy-free",
  "vegan"... are shown as direct evidence; the rest is labelled indirect (co-occurrence, not a tested
  swap). Status per candidate: supported (>= 3 recipes and positive difference), weak (1-2), conflicting
  (appears as often or more when the ingredient is still used, or is already in the recipe), none, or
  blocked by a restriction.

The answer gives an updated ingredient list and revised instructions (changed lines are marked).
Lines that break a restriction are also adapted; if one can't be supported, it is marked **NOT
replaced** and the answer says the recipe does not meet the restriction. If no candidate has local
support, no adaptation is given. Effects on taste/texture are predictions: the dataset has no
ratings or outcomes to verify them. Nothing is claimed to be medically safe.

**External search.** Not used. All evidence is local; the only outside knowledge is the labelled
candidate table.

**Unsupported questions.** Calories, nutrition, cooking time, ratings and price aren't in the data.
The bot says so instead of estimating. For time questions it quotes the timed instruction lines as
written, clearly not as a total.

## Evaluation

`eval/cases.py` has 10 conversations (21 turns) across all three tasks: multi-turn refinement, aggregate
statistics, ranking, matching with a follow-up, quantities, a no-match case, two substitutions, a
substitution with no supported candidate, and unsupported attributes. Checks test properties that must
hold on any data, for example:
- every result after "no dairy" has no dairy line
- the garlic+onion count is <= each single count, identical on re-run, and the answer states the
  percentage with its denominator
- the 5 fewest-step tomato recipes really are the global minimum
- match results respect max steps and exclusions and are sorted by the stated key
- every recipe ID cited as substitution evidence exists and doesn't contain the removed ingredient
- adapted ingredients contain no restricted item unless it is explicitly flagged as not replaced

Results with full transcripts: `eval/RESULTS.md`. With `--llm`, it also reports how many LLM parses
matched the expected request.

**One-shot LLM vs this system** (`eval/BASELINE.md`): a plain LLM asked "how many recipes contain both
garlic and onion?" or "which five tomato recipes have the fewest steps, with IDs?" has no access to the
data, so it can only guess a number or invent IDs; the script checks its IDs against the dataset. The
system computes the count over the full data and cites only real IDs. For calories, the system refuses
because the field doesn't exist.

**Results** (full data, 122,937 recipes, model `openai/gpt-oss-120b`; LLM parses can vary between runs):
- With expected requests fed straight to the engine: 26/26 checks passed.
- With the LLM parsing the messages: 26/26 checks passed and 18/21 parses matched the expected request. The
  3 differences were harmless (`heavy cream` vs `cream`, a shorter search query, a repeated query).
- What failed along the way: in earlier runs the LLM sometimes dropped a hard rule ("use all three", "without
  dairy"), which broke 2 checks. A prompt example did not reliably fix it, so those phrases are now also read
  by a regex in code. The parser is still the weakest link: a restriction worded in a way the regex doesn't
  cover depends on the LLM catching it.
- One-shot LLM: with no data it reported about 31,900 garlic-and-onion recipes (about 25.6%) in one run and
  about 24,500 (19.6%) in another, both presented as analysis, and invented an "official count" of 124,815
  recipes. The computed answer is 16,552 (13.46% of 122,937), reproducible on every run. Its count also treats
  garlic powder as garlic, which ours doesn't. Asked for the five tomato recipes with the fewest steps, it
  said it couldn't access the data and returned code with no recipe IDs.

## Limitations

- Ingredient cleaning is rule-based, so some lines are parsed imperfectly (e.g. brand names, odd formats).
- The diet category lists are reasonable but not exhaustive (e.g. margarine may contain dairy). Not an
  allergy guarantee.
- The step count depends on each site's paragraph formatting.
- Instruction rewriting is word replacement (e.g. "Melt olive oil"), so changed lines are marked for review.
- The substitution candidate table is short; ingredients outside it get "no candidates known".

## AI tools

I wrote the first version of the chatbot. I used Claude Code to review it and debug it against the
full dataset. Claude Code also implemented the fixes that came out of that, added a few features
(questions about a single recipe, "of those" statistics, the regex safety net for hard restrictions),
added unit tests and eval cases, ran the evaluation, and updated parts of this README. I reviewed these
changes and can explain and modify every part.
