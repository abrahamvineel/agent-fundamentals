import datetime
import random
from fastmcp import FastMCP

mcp = FastMCP("Learning MCP")


@mcp.tool()
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@mcp.tool()
def flip_coin() -> str:
    """Flip a fair coin and return heads or tails."""
    return random.choice(["heads", "tails"])


@mcp.tool()
def calculate(expression: str) -> str:
    """Evaluate a basic math expression like '2 + 2' or '15 * 4 / 2'."""
    allowed = set("0123456789+-*/(). ")
    if not all(c in allowed for c in expression):
        return "Error: only digits and basic operators ( + - * / ( ) . ) are allowed"
    try:
        result = eval(expression)  # noqa: S307 — input sanitized to digits and operators only
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def word_count(text: str) -> str:
    """Count the number of words in the given text."""
    count = len(text.split())
    return f"{count} word{'s' if count != 1 else ''}"


if __name__ == "__main__":
    mcp.run()
