"""Run the evaluation set and write eval/RESULTS.md.

    python -m eval.run_eval                 # deterministic: expected intents -> engine
    python -m eval.run_eval --llm           # LLM parses the messages too (needs LLM_API_KEY)
    python -m eval.run_eval --data tests/fixtures/raw   # run on the small test fixture
"""
import argparse
import time
from pathlib import Path

from eval.cases import CONVERSATIONS
from recipebot.bot import Bot
from recipebot.data import DATA_DIR
from recipebot.engine import load_index
from recipebot.intent import Intent

OUT = Path(__file__).resolve().parent / "RESULTS.md"
PARSE_FIELDS = ["intent", "query", "include", "exclude", "max_steps", "remove", "stat"]


def _norm(v):
    if isinstance(v, list):
        return sorted(x.lower().rstrip("s") for x in v)
    return v.lower() if isinstance(v, str) else v


def parse_agreement(expected: Intent, got: Intent) -> list[str]:
    diffs = []
    for f in PARSE_FIELDS:
        a, b = _norm(getattr(expected, f)), _norm(getattr(got, f))
        if a != b and not (f == "query" and a and b and set(a.split()) <= set(b.split())):
            diffs.append(f"{f}: expected {a!r}, got {b!r}")
    exp_have = sorted(h["name"].lower().rstrip("s") for h in expected.have)
    got_have = sorted(h["name"].lower().rstrip("s") for h in got.have)
    if exp_have != got_have:
        diffs.append(f"have: expected {exp_have}, got {got_have}")
    return diffs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true")
    ap.add_argument("--data", default=str(DATA_DIR / "raw"))
    args = ap.parse_args()

    data = Path(args.data)
    index = load_index(data, data.parent / "index.pkl")
    parser = None
    if args.llm:
        from recipebot.llm import LLMParser
        parser = LLMParser()

    lines = [f"# Evaluation results\n",
             f"Data: `{data}` - {len(index.recipes)} recipes loaded, skipped: {index.report.skipped}  ",
             f"Mode: {'LLM parsing' if args.llm else 'expected intents (deterministic, no LLM)'}\n"]
    passed = total = parse_ok = parse_total = 0
    for name, turns in CONVERSATIONS.items():
        bot = Bot(index, parser)
        lines.append(f"## {name}\n")
        for message, expected, checks in turns:
            exp = Intent.from_dict(expected)
            if parser:
                got = parser.parse(message, bot.s.summary())
                diffs = parse_agreement(exp, got)
                parse_total += 1
                parse_ok += not diffs
                intent = got
            else:
                intent, diffs = exp, []
            t0 = time.time()
            reply = bot.handle_intent(intent, message)
            secs = time.time() - t0
            shown = reply.splitlines()
            if len(shown) > 45:
                shown = shown[:45] + [f"... ({len(reply.splitlines()) - 45} more lines)"]
            lines += [f"**User:** {message}\n", "```", *shown, "```",
                      f"_{secs:.1f}s_" + (f" | parse diffs: {diffs}" if diffs else "")]
            for check in checks:
                ok, detail = check(bot, reply, None)
                total += 1
                passed += ok
                lines.append(f"- {'PASS' if ok else 'FAIL'} `{check.__qualname__.split('.')[0]}`: {detail}")
            lines.append("")
    summary = f"**Checks passed: {passed}/{total}**"
    if parser:
        summary += f"  |  **LLM parses matching expected intent: {parse_ok}/{parse_total}**"
    lines.insert(3, summary + "\n")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(summary.replace("**", ""))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
