"""The structured request the chat layer passes to the engine.

The LLM only fills this in. It never answers, counts or ranks anything.
`Intent.from_dict` validates and coerces whatever the model returns, so a bad
or partial JSON can't crash the engine or smuggle in fields.
"""
from dataclasses import dataclass, field

INTENTS = {"search", "show", "ask", "stats", "match", "substitute", "unsupported", "reset", "help", "chat"}
STAT_OPS = {"count", "top_ingredients", "ingredient_count", "step_count", "rank_steps"}


@dataclass
class Intent:
    intent: str = "chat"
    query: str | None = None              # free text for search, e.g. "penne pasta"
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    allow: list[str] = field(default_factory=list)    # lift an earlier exclusion
    max_steps: int | None = None
    have: list[dict] = field(default_factory=list)    # [{"name", "qty", "unit"}]
    prefer: list[str] = field(default_factory=list)
    recipe: str | None = None             # id, "#2" (from last results) or a dish name
    remove: str | None = None             # ingredient to substitute
    stat: str | None = None
    fewest: bool = True
    limit: int | None = None
    new_topic: bool = False
    of_those: bool = False                # stats about the results just shown
    missing: str | None = None            # for "unsupported": what the dataset lacks

    @classmethod
    def from_dict(cls, d: dict) -> "Intent":
        def strs(v):
            return [str(x).strip() for x in (v or []) if str(x).strip()] if isinstance(v, list) else []

        def opt_int(v):
            try:
                return int(v) if v is not None and str(v).strip() != "" else None
            except (TypeError, ValueError):
                return None

        def opt_str(v):
            return str(v).strip() or None if v not in (None, "", "null") else None

        have = []
        for h in d.get("have") or []:
            if isinstance(h, str):
                h = {"name": h}
            if isinstance(h, dict) and h.get("name"):
                qty = h.get("qty")
                try:
                    qty = float(qty) if qty not in (None, "") else None
                except (TypeError, ValueError):
                    qty = None
                have.append({"name": str(h["name"]).strip(), "qty": qty, "unit": opt_str(h.get("unit"))})

        intent = d.get("intent") if d.get("intent") in INTENTS else "chat"
        stat = d.get("stat") if d.get("stat") in STAT_OPS else None
        if intent == "stats" and stat is None:
            stat = "count"
        return cls(
            intent=intent, query=opt_str(d.get("query")), include=strs(d.get("include")),
            exclude=strs(d.get("exclude")), allow=strs(d.get("allow")), max_steps=opt_int(d.get("max_steps")),
            have=have, prefer=strs(d.get("prefer")), recipe=opt_str(d.get("recipe")),
            remove=opt_str(d.get("remove")), stat=stat, fewest=d.get("fewest", True) is not False,
            limit=opt_int(d.get("limit")), new_topic=bool(d.get("new_topic")), of_those=bool(d.get("of_those")), missing=opt_str(d.get("missing")),
        )
