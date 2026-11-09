"""LLM = natural-language parser only.

Turns the user's message (plus a short summary of the current session) into an
Intent. Works with any OpenAI-compatible endpoint: Groq (default) or Google AI
Studio's Gemini OpenAI-compatible endpoint. Temperature 0.
"""
import json
import os
import re
from pathlib import Path

from .intent import Intent

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You turn a user's message to a recipe chatbot into ONE JSON object.
You do NOT answer the question, count, rank or invent recipes. Code does that.

Keys (omit or use null/[] when not mentioned):
- intent: one of
    "search"      find recipes by dish name / ingredients / description
    "show"        show full ingredients + instructions of a recipe
    "ask"         a question about ONE recipe: does it contain X, is it dairy-free, how many steps. Put X in include
    "stats"       counts, percentages, most common ingredients, averages/medians, ranking by steps
    "match"       user lists ingredients they HAVE and wants recipes using them
    "substitute"  replace/remove an ingredient in a recipe
    "unsupported" asks for something the dataset does not contain (calories, nutrition, cook time, ratings, price)
    "reset"       start over / clear restrictions
    "help", "chat"
- query: search text (dish name or description), e.g. "penne pasta". For "stats": a dish name that must be in the recipe title.
  For a vague request, write concrete dish or ingredient words that could appear in a recipe
- include: ingredients that MUST be in the recipe, singular words, e.g. ["garlic","onion"].
  For "match", only when the user says the recipe must use them (e.g. "use all of them")
- exclude: things to avoid: ingredients ("peanut") or diet words ("dairy","eggs","nuts","gluten","meat","vegetarian","vegan")
- allow: things the user now says ARE allowed again
- max_steps: integer limit on instruction steps
- have: for "match": [{"name": "egg", "qty": 2, "unit": null}] (qty/unit only if the user gave them)
- prefer: ordering preferences from ["most_matched","fewest_extra","fewest_steps"], most important first
- recipe: which recipe: an id like "ar:abc123", "#2" for the 2nd result shown, or a dish name like "banana bread"
- remove: the ingredient to replace (for "substitute")
- stat: "count" | "top_ingredients" | "ingredient_count" | "step_count" | "rank_steps"
- fewest: false only if the user wants the MOST steps
- limit: number of results requested
- new_topic: true if the user starts a different search instead of refining the current one
- of_those: true if a "stats" question is about the results just shown ("of those", "among these")
- missing: for "unsupported", what is missing (e.g. "calories")

Follow-up rules (use the session state):
- A new restriction like "I cannot have dairy" or "exclude eggs too" refines the ACTIVE task: keep that
  task's intent ("search", "match" or "stats") and put only the NEW restriction in exclude.
  If the active task is "stats", also repeat last_stat as stat.
- "this recipe", "it" -> selected_recipe if there is one, otherwise "#1". "the first one" -> "#1".
Output JSON only."""

EXAMPLES = [
    ("Find a penne pasta recipe", {"intent": "search", "query": "penne pasta"}),
    ("I cannot have dairy", {"intent": "search", "exclude": ["dairy"]}),
    ("How many recipes contain both garlic and onion? What percentage is that?",
     {"intent": "stats", "stat": "count", "include": ["garlic", "onion"]}),
    ("How many banana bread recipes are there?", {"intent": "stats", "stat": "count", "query": "banana bread"}),
    ("Among recipes containing tomato, which five have the fewest instruction steps?",
     {"intent": "stats", "stat": "rank_steps", "include": ["tomato"], "limit": 5}),
    ("I have eggs, onions, tomatoes, and rice. Suggest five recipes, no peanuts, at most six steps, fewest extra ingredients",
     {"intent": "match", "have": [{"name": "egg"}, {"name": "onion"}, {"name": "tomato"}, {"name": "rice"}],
      "exclude": ["peanut"], "max_steps": 6, "prefer": ["most_matched", "fewest_extra"], "limit": 5}),
    ("Exclude eggs too", {"intent": "match", "exclude": ["eggs"]}),
    ("I have chicken, rice and peas. Only recipes that use all of them.",
     {"intent": "match", "have": [{"name": "chicken"}, {"name": "rice"}, {"name": "pea"}],
      "include": ["chicken", "rice", "pea"]}),
    ("Something light for a hot summer day", {"intent": "search", "query": "summer salad gazpacho chilled soup"}),
    ("Does the first one contain garlic?", {"intent": "ask", "recipe": "#1", "include": ["garlic"]}),
    ("How many of those contain garlic?", {"intent": "stats", "stat": "count", "include": ["garlic"], "of_those": True}),
    ("Take this banana bread recipe and remove eggs", {"intent": "substitute", "recipe": "banana bread", "remove": "egg"}),
    ("How many calories are in it?", {"intent": "unsupported", "missing": "calories", "recipe": "#1"}),
]


def _load_dotenv():
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


class LLMParser:
    def __init__(self):
        _load_dotenv()
        key = os.getenv("LLM_API_KEY")
        if not key:
            raise RuntimeError("Set LLM_API_KEY (Groq or Google AI Studio key). See README.")
        from openai import OpenAI
        self.client = OpenAI(api_key=key, base_url=os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL))
        self.model = os.getenv("LLM_MODEL", DEFAULT_MODEL)

    def complete(self, messages: list[dict]) -> str:
        resp = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0)
        return resp.choices[0].message.content or ""

    def parse(self, message: str, state_summary: dict) -> Intent:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for user, out in EXAMPLES:
            messages += [{"role": "user", "content": user}, {"role": "assistant", "content": json.dumps(out)}]
        messages.append({"role": "user", "content":
                         f"Session state: {json.dumps(state_summary)}\nMessage: {message}"})
        return Intent.from_dict(_extract_json(self.complete(messages)))
