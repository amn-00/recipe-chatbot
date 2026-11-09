"""Command-line chatbot.  Usage:  python chat.py   (add --debug to see the parsed intent)"""
import sys

from recipebot.bot import Bot
from recipebot.engine import load_index
from recipebot.llm import LLMParser


def main():
    debug = "--debug" in sys.argv
    index = load_index()
    rep = index.report
    print(f"Loaded {rep.loaded} recipes from {', '.join(rep.files)} (skipped: {rep.skipped})")
    bot = Bot(index, LLMParser())
    print("Ask about recipes. Type 'reset' to clear restrictions, 'quit' to exit.\n")
    while True:
        try:
            msg = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if msg.lower() in {"quit", "exit", "q"}:
            break
        if not msg:
            continue
        try:
            if debug:
                intent = bot.parser.parse(msg, bot.s.summary())
                print(f"[intent] {intent}")
                reply = bot.handle_intent(intent, msg)
            else:
                reply = bot.handle(msg)
        except Exception as e:  # keep the session alive on API/network errors
            reply = f"Error: {e}"
        print(f"\nbot> {reply}\n")


if __name__ == "__main__":
    main()
