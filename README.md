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

- **IDs and data.** ID = `<source>:<original key>` (`ar`, `epi`, `fn`), so it is stable and unique across files. Original text is kept; only the scraper word `ADVERTISEMENT` is removed. Incomplete records are skipped and counted at startup.
- **Step rule.** One step = one non-empty line of the instructions, ignoring video links, photo credits and equipment lists. Reproducible, but some recipes are one long paragraph.
- **Normalization.** Each ingredient line is cleaned to a name (`2 cups finely chopped onions, divided` -> `onions`). Matching ignores plurals and uses a small synonym table. Two modes:
  - *Strict* for "contains" and "I have": `garlic` does not cover `garlic powder`.
  - *Broad* for restrictions: any mention on the whole original line counts, so "no peanuts" also removes peanut oil. Diet words map to categories with exceptions (coconut milk is not dairy).
- **Retrieval.** TF-IDF over title (counted twice) and ingredient names, because queries are mostly dish names and ingredients. It is deterministic and needs no model download. For vague requests the LLM writes concrete search words, shown in the answer. Restrictions are checked on every match, not a top-k.
- **Computation.** Counts, averages and rankings run in Python over the complete filtered set. Percentages use all loaded recipes, or the current results for "of those" questions. Ties are broken by recipe ID. The LLM never sees or produces these numbers.
- **Follow-ups.** The session keeps the active task and its query or ingredients, and a new restriction refines it. Restrictions stay on, shown under each answer, until `reset` or until the user allows the item again. `#2` means the 2nd result shown last.
- **LLM safety net.** The LLM sometimes dropped a hard rule in testing, so "no dairy"-style restrictions and "use all of them" are also read from the message by a small regex.
- **Matching (Task 2).** Hard constraints are filters, never score penalties. Ranking order: most of your ingredients used, fewest extra ingredients (salt, pepper and water assumed), fewest steps, then recipe ID. If nothing qualifies, the answer says NO MATCH and shows the closest recipes separately, labelled with what they violate. Quantities are compared only when the units match; otherwise they are marked "not verified".
- **Substitution (Task 3).** A short hand-written table proposes candidates, ratios and predicted effects, labelled as general knowledge. Evidence comes only from local data: among the 1,500 most similar recipes, compare how often a candidate appears without the ingredient versus with it. Titles like "eggless" count as direct evidence; the rest is labelled indirect. Status is supported (3+ recipes, positive difference), weak (1-2), conflicting (not more common without it, or already in the recipe), none, or blocked by a restriction. The answer gives updated ingredients and instructions, or no adaptation if nothing is supported. Effects are predictions, and nothing is claimed to be medically safe.
- **External search.** Not used. All evidence is local; the only outside knowledge is the labelled table.
- **Unsupported questions.** Calories, nutrition, cooking time, ratings and price aren't in the data, so the bot says so instead of estimating.

## Evaluation

`eval/cases.py` has 10 conversations (21 turns) across all three tasks, including multi-turn follow-ups, statistics, a no-match case and weak substitution evidence. Checks test properties that must hold on any data, for example: results after "no dairy" contain no dairy, rankings really are the minimum, and cited recipe IDs exist. Transcripts are in `eval/RESULTS.md` and the plain LLM comparison is in `eval/BASELINE.md`.

Results on the full data (122,937 recipes, model `openai/gpt-oss-120b`; LLM parses can vary between runs):

- **Worked.** 26/26 checks passed with expected requests fed straight to the engine, and 26/26 with the LLM parsing messages. 18/21 parses matched the expected request; the 3 differences were harmless.
- **Failed along the way.** The LLM sometimes dropped a hard rule ("use all three", "without dairy"), which broke 2 checks. A prompt example did not reliably fix it, so those phrases are now also read by a regex. The parser is still the weakest link: a restriction worded in a way the regex doesn't cover depends on the LLM catching it.
- **One-shot LLM.** With no data, it reported about 31,900 garlic-and-onion recipes (25.6%) in one run and about 24,500 (19.6%) in another, both presented as analysis, and invented an "official count" of 124,815 recipes. The computed answer is 16,552 (13.46% of 122,937), the same on every run; its count also treats garlic powder as garlic, which ours doesn't. For the five tomato recipes with the fewest steps, it returned code and no recipe IDs.

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
