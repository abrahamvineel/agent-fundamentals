import time
from anthropic import Anthropic
from pydantic import BaseModel, ValidationError
from typing import Literal

client = Anthropic()


class AgentResponse(BaseModel):
    answer: str
    confidence: Literal["high", "medium", "low"]
    reasoning: str


BASE_PROMPT = """\
Answer the question and respond with valid JSON only.
No markdown, no code fences — raw JSON matching this schema exactly:
{{
  "answer": "<your answer>",
  "confidence": "<high|medium|low>",
  "reasoning": "<one sentence explaining your confidence level>"
}}

Question: {question}"""


def call_llm(prompt: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def strip_fences(raw: str) -> str:
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


def run(question: str, max_retries: int = 3) -> AgentResponse:
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            prompt = BASE_PROMPT.format(question=question)
            if last_error:
                prompt += f"\n\nYour last response failed validation: {last_error}\nFix the JSON and try again."

            raw = call_llm(prompt)
            result = AgentResponse.model_validate_json(strip_fences(raw))
            print(f"[attempt {attempt}] OK — {result.answer} (confidence: {result.confidence})")
            return result

        except ValidationError as e:
            last_error = str(e)
            print(f"[attempt {attempt}] ValidationError: {last_error[:80]}")

        except Exception as e:
            last_error = str(e)
            print(f"[attempt {attempt}] Error: {last_error}")
            time.sleep(2**attempt)

    print(f"Graceful degradation after {max_retries} failed attempts.")
    return AgentResponse(
        answer="Unable to get reliable answer",
        confidence="low",
        reasoning=f"Failed after {max_retries} attempts. Last error: {last_error}",
    )


if __name__ == "__main__":
    result = run("What is the speed of light in meters per second?")
    print(f"\nFinal:\n{result.model_dump_json(indent=2)}")
