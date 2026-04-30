from anthropic import Anthropic

client = Anthropic()


def attempt(task: str, past_reflections: list) -> str:
    reflection_context = ""
    if past_reflections:
        reflection_context = "\n\nReflections from past attempts:\n" + "\n".join(
            f"- {r}" for r in past_reflections
        )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Complete this task exactly as specified:"
                    f"{reflection_context}\n\nTask: {task}"
                ),
            }
        ],
    )
    return response.content[0].text


def evaluate(task: str, result: str) -> float:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=64,
        system="You are a strict evaluator. Respond with only a decimal number between 0.0 and 1.0. Nothing else.",
        messages=[
            {
                "role": "user",
                "content": f"Task: {task}\n\nResult:\n{result}\n\nScore (0.0 to 1.0):",
            }
        ],
    )
    try:
        return float(response.content[0].text.strip())
    except ValueError:
        return 0.0


def reflect(task: str, result: str, score: float) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Task: {task}\n\nResult:\n{result}\n\nScore: {score}\n\n"
                    "In one sentence, what went wrong and what should be done differently next time?"
                ),
            }
        ],
    )
    return response.content[0].text.strip()


def run(task: str, max_attempts: int = 3) -> str:
    reflections = []

    for attempt_num in range(1, max_attempts + 1):
        print(f"\n--- Attempt {attempt_num}/{max_attempts} ---")
        result = attempt(task, reflections)
        score = evaluate(task, result)
        print(f"Result preview: {result[:120]}")
        print(f"Score: {score:.2f}")

        if score >= 0.8:
            print("Success!")
            return result

        reflection = reflect(task, result, score)
        print(f"Reflection: {reflection}")
        reflections.append(reflection)

    print(f"Completed {max_attempts} attempts. Best effort returned.")
    return result


if __name__ == "__main__":
    task = (
        "Write exactly 3 bullet points about photosynthesis. "
        "Each bullet must be under 10 words. "
        "Start each with a dash (-). Nothing else."
    )
    run(task)
