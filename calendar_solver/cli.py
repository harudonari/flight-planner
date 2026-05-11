"""
Flight Planner — Claude-powered trip planning agent
Run: python cli.py
"""
from agent import TripPlannerAgent

WELCOME = """
╔══════════════════════════════════════════════════╗
║         Flight Planner — Powered by Claude       ║
╚══════════════════════════════════════════════════╝

Tell me your trip goals in plain English. For example:
  "I have 10 vacation days in 2026, want to visit Tokyo and London,
   flying from SFO, at least 5 days each, between June and December."

Type 'quit' to exit, 'reset' to start a new conversation.
"""

def main():
    agent = TripPlannerAgent()
    print(WELCOME)

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Goodbye!")
            break
        if user_input.lower() == "reset":
            agent = TripPlannerAgent()
            print("Conversation reset.\n")
            continue

        print("\nAssistant: ", end="", flush=True)
        response = agent.chat(user_input)
        print(response)
        print()

if __name__ == "__main__":
    main()