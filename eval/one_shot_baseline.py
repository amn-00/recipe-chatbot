"""One-shot LLM vs this system, on questions with a checkable answer.

The plain LLM gets the question only (no data). We then compare with the
computed answer and check whether any recipe IDs it gives actually exist.

    python -m eval.one_shot_baseline        (needs LLM_API_KEY; writes eval/BASELINE.md)
"""
import re
from pathlib import Path

from recipebot.constraints import Constraints
from recipebot.engine import load_index
from recipebot.llm import LLMParser
from recipebot import stats

OUT = Path(__file__).resolve().parent / "BASELINE.md"
CONTEXT = "Answer about the Recipe Box dataset (~125k recipes from allrecipes, epicurious and foodnetwork). "


def main():
    index = load_index()
    llm = LLMParser()
    ask = lambda q: llm.complete([{"role": "user", "content": CONTEXT + q}])
    rows = []

    q = "How many recipes contain both garlic and onion, and what percentage of the dataset is that? Give numbers."
    truth = dict(stats.count(index.recipes, Constraints(include=["garlic", "onion"])).rows)
    rows.append((q, ask(q), f"{truth['count']} recipes = {truth['percent_of_dataset']}% of {len(index.recipes)}"))

    q = ("Among recipes containing tomato, list the five with the fewest instruction steps, "
         "with their recipe IDs and step counts.")
    ranked = stats.rank_by_steps(index.recipes, Constraints(include=["tomato"]), limit=5).rows
    rows.append((q, ask(q), "; ".join(f"{rid} ({t}, {n} steps)" for rid, t, n in ranked)))

    q = "How many calories are in a typical banana bread recipe from this dataset?"
    rows.append((q, ask(q), "Not answerable: the dataset has no nutrition fields (system refuses)."))

    lines = ["# One-shot LLM baseline vs grounded system\n", f"Model: `{llm.model}`\n"]
    for q, answer, truth in rows:
        ids = re.findall(r"\b(?:ar|epi|fn):[\w.\-/]+", answer)
        real = [i for i in ids if i in index.by_id]
        lines += [f"## {q}\n", "**One-shot LLM:**\n", "```", answer.strip()[:1500], "```",
                  f"**System (computed):** {truth}\n",
                  f"IDs cited by the LLM: {len(ids)}, of which exist in the data: {len(real)}\n"]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
