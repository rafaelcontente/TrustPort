"""Autonomous LLM Agent Loop for TrustPort.

Demonstrates headless backend integration where an LLM autonomously
calls tools to gather data and validate proposals until approval.
"""

import json
import os

import requests
from openai import OpenAI

# Initialize OpenAI client (requires OPENAI_API_KEY environment variable)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"))

TRUSTPORT_API_URL = "http://127.0.0.1:8000"

# 1. Define Tools Schema for the LLM
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_client_credit_history",
            "description": "Fetches real credit history and employment data for a given client_id.",
            "parameters": {
                "type": "object",
                "properties": {"client_id": {"type": "string", "description": "The unique identifier of the client."}},
                "required": ["client_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_proposal",
            "description": "Validates a loan proposal against TrustPort business rules. NEVER approve without calling this first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "proposal_id": {"type": "string"},
                    "case_id": {"type": "string"},
                    "action": {"type": "string", "enum": ["approve", "deny"]},
                    "amount": {"type": "number"},
                    "term_months": {"type": "integer"},
                    "dsti_ratio": {"type": "number"},
                    "facts_cited": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["proposal_id", "case_id", "action", "amount", "term_months", "dsti_ratio", "facts_cited"],
            },
        },
    },
]


def execute_tool(name: str, arguments: dict) -> str:
    """Executes the requested tool and returns the result as a JSON string."""
    if name == "fetch_client_credit_history":
        # Simulated tool execution (in production, this would query a real DB)
        client_id = arguments.get("client_id", "UNKNOWN")
        return json.dumps({"client_id": client_id, "employment_years": 5, "credit_score": 750, "payment_history": "Clean record"})

    elif name == "validate_proposal":
        # Call the local TrustPort API
        try:
            response = requests.post(f"{TRUSTPORT_API_URL}/validate", json=arguments, timeout=5)
            return json.dumps(response.json())
        except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
            return json.dumps({"error": f"API call failed: {e!s}"})

    return json.dumps({"error": "Unknown tool"})


def run_autonomous_loop(user_request: str, max_turns: int = 3):
    """Runs the LLM tool-calling loop until approval or max turns reached."""
    print("=" * 70)
    print("TRUSTPORT AUTONOMOUS AGENT LOOP")
    print("=" * 70)
    print(f"\nUser Request: {user_request}\n")

    messages = [
        {
            "role": "system",
            "content": "You are a compliant loan officer assistant. You MUST use the provided tools to gather facts and validate proposals. Never approve a loan without a successful validate_proposal tool call returning 'APPROVED'.",
        },
        {"role": "user", "content": user_request},
    ]

    for turn in range(1, max_turns + 1):
        print(f"--- Turn {turn} ---")

        # 1. Ask the LLM
        response = client.chat.completions.create(
            model="gpt-4o",  # or gpt-3.5-turbo
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        # 2. Check if LLM wants to call a tool
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                print(f"🛠️  Agent calling tool: {func_name}")
                print(f"    Arguments: {json.dumps(func_args)}")

                # 3. Execute tool
                result = execute_tool(func_name, func_args)
                print(f"    Result: {result[:150]}...")  # Truncate for readability

                # 4. Append to conversation
                messages.append(msg)
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": result})
        else:
            # LLM gave a final text response
            print("\n✅ FINAL RESPONSE FROM AGENT:")
            print(msg.content)

            # Check if we got an audit hash (success condition)
            if "audit_hash" in msg.content.lower() or "approved" in msg.content.lower():
                print("\n🎉 Loop completed successfully with compliance!")
            break
    else:
        print("\n⚠️ Max turns reached without final approval.")


if __name__ == "__main__":
    # Example: A request that will initially fail Gate 2 (DSTI > 40%)
    # and force the agent to repair the proposal.
    REQUEST = "I am client CLI-001. I want to apply for a loan of 50,000 EUR for 60 months. My DSTI ratio is 0.45. Please approve this."
    run_autonomous_loop(REQUEST)
