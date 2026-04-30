import sys
import sqlite3
from datetime import datetime
from anthropic import Anthropic

client = Anthropic()

db = sqlite3.connect("memory.db")
db.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY,
        content TEXT,
        created_at TEXT
    )
""")
db.commit()


def remember(fact: str) -> str:
    db.execute(
        "INSERT INTO memories (content, created_at) VALUES (?, ?)",
        (fact, datetime.now().isoformat()),
    )
    db.commit()
    return f"Remembered: {fact}"


def recall() -> str:
    rows = db.execute(
        "SELECT id, content, created_at FROM memories ORDER BY id"
    ).fetchall()
    if not rows:
        return "No memories stored yet."
    return "\n".join(f"[{r[0]}] {r[1]} (saved: {r[2][:10]})" for r in rows)


tools = [
    {
        "name": "remember",
        "description": "Save an important fact to long-term memory so it persists across conversations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "The fact to remember"}
            },
            "required": ["fact"],
        },
    },
    {
        "name": "recall",
        "description": "Retrieve all facts previously saved to long-term memory.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def run(question: str):
    messages = [{"role": "user", "content": question}]

    for step in range(10):
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
                    print(f"Agent: {block.text}")
            return

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = remember(**block.input) if block.name == "remember" else recall()
                print(f"  tool: {block.name} → {result[:80]}")
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )
        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What do you know about me?"
    run(question)
