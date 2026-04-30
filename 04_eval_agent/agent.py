from anthropic import Anthropic

client = Anthropic()

TEST_CASES = [
    {
        "input": "What is 2 + 2?",
        "ideal": "4",
        "criteria": "Must contain the number 4",
    },
    {
        "input": "What is the capital of France?",
        "ideal": "Paris",
        "criteria": "Must mention Paris",
    },
    {
        "input": "What color is the sky on a clear day?",
        "ideal": "blue",
        "criteria": "Must mention blue",
    },
    {
        "input": "How many sides does a triangle have?",
        "ideal": "3",
        "criteria": "Must contain the number 3",
    },
    {
        "input": "What is the boiling point of water in Celsius?",
        "ideal": "100",
        "criteria": "Must contain 100",
    },
]


def get_agent_response(question: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": question}],
    )
    return response.content[0].text


def judge(question: str, ideal: str, actual: str, criteria: str) -> float:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=16,
        system=(
            "You are a strict judge. Respond with only 0.0 or 1.0. "
            "1.0 = the response meets the criteria. 0.0 = it does not."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n"
                    f"Ideal answer: {ideal}\n"
                    f"Actual response: {actual}\n"
                    f"Criteria: {criteria}\n"
                    f"Score (0.0 or 1.0):"
                ),
            }
        ],
    )
    try:
        return float(response.content[0].text.strip())
    except ValueError:
        return 0.0


def run_eval():
    scores = []
    for i, test in enumerate(TEST_CASES, 1):
        actual = get_agent_response(test["input"])
        score = judge(test["input"], test["ideal"], actual, test["criteria"])
        scores.append(score)
        status = "PASS" if score >= 0.5 else "FAIL"
        print(f"[{i}] {status} | {test['input'][:45]:<45} | score={score}")

    avg = sum(scores) / len(scores)
    print(f"\nFinal Score: {avg:.1%}  ({int(sum(scores))}/{len(scores)} passed)")


if __name__ == "__main__":
    run_eval()
