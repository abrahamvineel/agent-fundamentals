import os
from anthropic import Anthropic

client = Anthropic()

tools = [
    {
        "name": "add",
        "description": "Add two numbers together. Use when you need addition.",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
        },
    },
    {
        "name": "multiply",
        "description": "Multiply two numbers together. Use when you need multiplication.",
        "input_schema": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
        },
    },
]


def add(a: float, b: float) -> float:
    return a + b


def multiply(a: float, b: float) -> float:
    return a * b


def run(question: str):
    messages = [{"role": "user", "content": question}]

    for step in range(10):
        print(f"\n[step {step+1}] messages in context: {len(messages)}")
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
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
                if block.name == "add":
                    result = add(**block.input)
                elif block.name == "multiply":
                    result = multiply(**block.input)
                print(f"  tool: {block.name}({block.input}) = {result}")
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result),
                    }
                )

        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    run("What is (15 * 4) + (23 * 2)?")
