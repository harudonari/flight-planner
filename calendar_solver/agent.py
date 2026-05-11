import os
from dotenv import load_dotenv
import anthropic
import json
from solver import solve

load_dotenv()
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Define the tool schema — this tells Claude what the solver accepts
SOLVER_TOOL = {
    "name": "calendar_solver",
    "description": (
        "Given structured trip constraints, finds all valid non-overlapping "
        "trip date windows that minimize vacation day usage. Returns ranked "
        "combined plans ready for flight search."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "vacation_days_remaining": {
                "type": "integer",
                "description": "Total paid weekdays the user can take off"
            },
            "year": {
                "type": "integer",
                "description": "The year to plan trips in"
            },
            "trips": {
                "type": "array",
                "description": "List of trips to plan",
                "items": {
                    "type": "object",
                    "properties": {
                        "id":                 {"type": "string"},
                        "destination":        {"type": "string"},
                        "departure_cities":   {"type": "array", "items": {"type": "string"}},
                        "min_duration_days":  {"type": "integer", "description": "The minumum duration of the trip in days"}
                    },
                    "required": ["id", "destination", "departure_cities", "min_duration_days"]
                }
            },
            "blackout_dates": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Dates unavailable in YYYY-MM-DD format"
            },
            "earliest_start": {"type": "string", "description": "YYYY-MM-DD"},
            "latest_end":     {"type": "string", "description": "YYYY-MM-DD"},
            "max_trips": {"type": "integer", "description": "The maximum number of trips that can be planned"}
        },
        "required": ["vacation_days_remaining", "year", "trips", "earliest_start", "latest_end"]
    }
}

def format_solver_error_for_claude(error_result: dict) -> str:
    """Given a solve() result with status='error', return a clear message
    to send back as the tool_result so Claude knows what went wrong and
    can correct its input.

    Example output:
    'The calendar_solver returned an error: Missing required field: earliest_start.
    Please call the tool again with all required fields included.'
    """
    error = error_result["message"]
    return f"The calendar_solver returned an error: {error}. Please call the tool again with correct fields included."

def format_top_plans(solver_result: dict, n: int = 3) -> str:
    """Given a successful solve() result, format the top N combined plans
    as a compact readable string to include in the tool_result sent to Claude.
    This reduces token usage compared to sending the full raw JSON.

    Example output:
    Top 3 plans:
    Plan 1 (score: 0.91, vacation days: 3):
      trip_nyc:     2026-05-15 → 2026-05-18  [weekend ✓]  cost: 1d
      trip_chicago: 2026-06-19 → 2026-06-22  [weekend ✓]  cost: 1d
      trip_seattle: 2026-07-10 → 2026-07-13  [weekend ✓]  cost: 1d
    ...
    """
    available_plans = n if solver_result["metadata"]["combinations_returned"] >= n else solver_result["metadata"]["combinations_returned"]
    result = [f"Top {available_plans} plans:"]
    plans = solver_result["combined_plans"]
    for i in range(available_plans):
        plan = plans[i]
        formatted = [f"Plan {i+1} (score: {round(plan["total_score"], 2)}, vacation days: {plan["total_vacation_days"]}):"]

        for window in plan["windows"]:
            weekend = "[weekend ✓]" if window["weekend_anchored"] else "[weekend x]"
            holiday = "[holiday ✓]" if window["overlaps_holiday"] else "[holiday x]"
            trip = f"{window["trip_id"]}: {window["start_date"]} →  {window["end_date"]} {weekend} {holiday} cost: {window["vacation_days_cost"]} days score: {round(window["score"], 2)}"
            formatted.append(trip)

        result.extend(formatted)
    
    return "\n".join(result)


class TripPlannerAgent:
    """Stateful agent that maintains conversation history across turns."""

    def __init__(self):
        self.history: list[dict] = []
        self.system_prompt = """You are a helpful travel planning assistant.
            Your job is to help users plan trips efficiently using their available vacation days.

            When a user describes their trip goals, first acknolwedge the request then extract
            their constraints and describe the plan you will search for. If user agrees with the described plan, 
            call the calendar_solver tool to find the best date windows. Then present the top 3
            combined plans clearly, highlighting:
            - The dates for each trip
            - How many vacation days each plan uses
            - Which trips are weekend-anchored (most efficient)

            If the user wants to adjust constraints (different dates, more/fewer days,
            add a destination), update the constraints and call the solver again.
            Always be concise and focus on actionable recommendations."""
        self.model = "claude-haiku-4-5"
        self.max_tokens = 1024

    def chat(self, user_message: str) -> str:
        """Add the user message to history, run the tool cycle if needed,
        append Claude's response to history, and return the response text.

        Important: history must include both the assistant's tool_use message
        AND your tool_result message when a tool is called, before Claude's
        final response. The full sequence in history after a tool call:

        [...previous turns...]
        {"role": "user",      "content": "<user message>"}
        {"role": "assistant", "content": [ToolUseBlock, ...]}   ← Claude's tool call
        {"role": "user",      "content": [tool_result block]}   ← your result
        {"role": "assistant", "content": [TextBlock]}           ← Claude's final reply
        """
        self.history.append({
            "role": "user",
            "content": user_message
        })
        # send the user message to Claude with tools
        response = client.messages.create(
        model=self.model,
        max_tokens=self.max_tokens,
        tools=[SOLVER_TOOL],
        messages=self.history)

        if response.stop_reason == "tool_use":  # tool use requested

            self.history.append({
                "role": "assistant",
                "content": response.content
            })
            
            # call the tool
            tool_use = next(block for block in response.content if block.type == "tool_use")
            solver_result = solve(tool_use.input)

            if solver_result["status"] == "error":
                tool_result = format_solver_error_for_claude(solver_result)
            else:
                tool_result = format_top_plans(solver_result)

            self.history.append({
                "role": "user",
                "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": tool_result
                            }
                        ]
            })

            follow_up = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                tools=[SOLVER_TOOL],
                messages=self.history
            )

            self.history.append({
                "role": "assistant",
                "content": follow_up.content
            })
            return follow_up.content[0].text
    
        self.history.append({
            "role": "assistant",
            "content": response.content
        })
        return response.content[0].text

def call_api(prompt: str, options: dict, context: dict) -> dict:
    agent = TripPlannerAgent()
    return {"output": agent.chat(prompt)}

if __name__ == "__main__":
    agent = TripPlannerAgent()
    
    print(agent.chat(
        "I have 10 vacation days in 2026. I want to visit NYC, Chicago, and Seattle. "
        "Flying from SFO, minimum 4 days each. Search May through December."
    ))
    print("---")
    print(agent.chat("Can you make the NYC trip at least 5 days instead?"))
    print("---")
    print(agent.chat("Which plan uses the fewest vacation days?"))
