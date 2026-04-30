from anthropic import Anthropic

client = Anthropic()

SPECIALISTS = {
    "ask_math_specialist": "mathematics",
    "ask_science_specialist": "science",
    "ask_history_specialist": "history",
}

tools = [
    {
        "name": "ask_math_specialist",
        "description": (
            "Route to the math specialist for calculations, equations, algebra, "
            "geometry, statistics, or any question involving numbers."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The math question to answer"}
            },
            "required": ["question"],
        },
    },
    {
        "name": "ask_science_specialist",
        "description": (
            "Route to the science specialist for biology, chemistry, physics, "
            "ecology, astronomy, or any natural science topic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The science question to answer"}
            },
            "required": ["question"],
        },
    },
    {
        "name": "ask_history_specialist",
        "description": (
            "Route to the history specialist for historical events, dates, "
            "civilizations, wars, famous people, or anything from the past."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The history question to answer"}
            },
            "required": ["question"],
        },
    },
]


def specialist_agent(question: str, specialty: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=f"You are a {specialty} specialist. Answer concisely in 2-3 sentences.",
        messages=[{"role": "user", "content": question}],
    )
    return response.content[0].text


def orchestrator(question: str):
    print(f"\nQuestion: {question}")
    messages = [{"role": "user", "content": question}]

    for step in range(8):
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=(
                "You are an orchestrator. Your only job is to route questions to the "
                "right specialist using the tools. Do not answer questions yourself. "
                "Combine specialist answers into a final response for the user."
            ),
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"Answer: {block.text}")
            return

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                specialty = SPECIALISTS[block.name]
                result = specialist_agent(block.input["question"], specialty)
                print(f"  → {specialty}: {result[:80]}...")
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )
        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    orchestrator("What year did Newton formulate calculus?")
    orchestrator("What is the square root of 144?")
    orchestrator("How does photosynthesis work?")
    orchestrator("Compare math in Newton's era to modern calculus")
