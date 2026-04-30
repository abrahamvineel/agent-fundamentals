# agent-primitives

Eight focused implementations. Each one teaches one concept.
No frameworks until built from scratch. Built to understand
agents deeply, not just use them.

---

## Project Philosophy

- One agent = one concept. Nothing more.
- Every agent must fit in a single file under 100 lines.
- No LangChain, no LangGraph, no CrewAI until Agent 8.
- If you cannot rewrite an agent from memory — stay on it.
- Build → experiment → break → fix → understand → move on.

---

## Repo Structure

```
agent-primitives/
├── CLAUDE.md
├── README.md
├── requirements.txt        # anthropic, fastmcp, pydantic
├── .env                    # ANTHROPIC_API_KEY=... (never commit)
├── .env.example            # ANTHROPIC_API_KEY=your_key_here
├── .gitignore              # .env, __pycache__, *.db, .DS_Store
├── 01_nano_agent/
│   ├── README.md
│   └── agent.py
├── 02_memory_agent/
│   ├── README.md
│   └── agent.py
├── 03_reflexion_agent/
│   ├── README.md
│   └── agent.py
├── 04_eval_agent/
│   ├── README.md
│   └── agent.py
├── 05_mcp_agent/
│   ├── README.md
│   └── server.py
├── 06_self_healing_agent/
│   ├── README.md
│   └── agent.py
├── 07_handoff_agent/
│   ├── README.md
│   └── agent.py
└── 08_auto_debugger/
    ├── README.md
    ├── agent.py
    ├── tools.py
    └── eval/
        ├── bugs/
        └── run_benchmark.py
```

---

## Environment

```bash
pip install anthropic fastmcp pydantic
```

All agents use environment variable for API key:

```python
import os
from anthropic import Anthropic
client = Anthropic()  # reads ANTHROPIC_API_KEY automatically
```

Always use `claude-haiku-4-5-20251001` for learning.
It is cheap. Mistakes cost almost nothing.
Switch to `claude-sonnet-4-6` only for Agent 8.

---

## The Sequence

| # | Folder | Concept | Max Lines |
|---|--------|---------|-----------|
| 1 | 01_nano_agent | ReAct loop from scratch | 80 |
| 2 | 02_memory_agent | State persistence with SQLite | 90 |
| 3 | 03_reflexion_agent | Learning from failure | 100 |
| 4 | 04_eval_agent | LLM-as-judge measurement | 80 |
| 5 | 05_mcp_agent | MCP tool protocol | 50 |
| 6 | 06_self_healing_agent | Robustness and retry | 90 |
| 7 | 07_handoff_agent | Multi-agent orchestration | 100 |
| 8 | 08_auto_debugger | Everything combined | 200 |

---

## Agent 1: NanoAgent

**File:** `01_nano_agent/agent.py`

**Concept:** The `while True` loop IS the agent.
The LLM decides which tool to call and when to stop.
You write zero if/else routing logic.

**Tools to implement:**
- `add(a, b)` — adds two numbers
- `multiply(a, b)` — multiplies two numbers

**Test question:**
```
"What is (15 * 4) + (23 * 2)?"
```

**Expected behavior:**
- Claude calls multiply twice
- Claude calls add once
- Claude returns final answer
- You wrote no routing logic

**Key things to understand:**
- `stop_reason == "end_turn"` means Claude is done
- `stop_reason == "tool_use"` means Claude wants a tool
- `messages` list must grow each loop — append both
  the assistant response AND the tool result
- Removing `messages.append()` breaks memory within the run

**Experiments to run after it works:**
1. Remove the `while True` — replace with single API call.
   What breaks? Why can Claude not finish the task?
2. Remove `messages.append()` inside the loop.
   Claude forgets what happened. Why?
3. Print `len(messages)` at start of each loop.
   Watch it grow: 1, 3, 5, 7...
   Understand why it grows by exactly 2 each time.
4. Add a third tool. Ask a question that needs all three.

**You own this agent when:**
You can delete agent.py, open a blank file, and
rewrite it from memory without looking at anything.

---

## Agent 2: Memory Agent

**File:** `02_memory_agent/agent.py`

**Concept:** Agents are stateless between runs.
The `messages` list resets every time you call `run()`.
SQLite fixes this by persisting facts to disk.

**Tools to implement:**
- `remember(fact: str)` — saves fact to SQLite
- `recall()` — returns all saved facts from SQLite

**Database setup:**
```python
import sqlite3
db = sqlite3.connect("memory.db")
db.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY,
        content TEXT,
        created_at TEXT
    )
""")
db.commit()
```

**Test sequence (two separate Python runs):**
```python
# Run 1
run("Remember that my name is Ahmed and I grow paddy rice")

# Run 2 (new process — messages list is empty)
run("What do you know about me?")
# Claude calls recall() and finds Ahmed
```

**Key things to understand:**
- `messages` list = memory within one run (disappears)
- SQLite = memory across runs (persists to disk)
- Production agents need both kinds
- Open `memory.db` in DB Browser for SQLite
  — your memories are just rows in a table

**Experiments to run:**
1. Delete `memory.db`. Run recall immediately.
   What does Claude say? Now remember something.
   Now recall. Watch the difference.
2. What if recall() returns an empty list?
   Does your function handle this gracefully?
3. Add a `forget(fact_id)` tool.
   How does Claude decide when to use it?

**You own this agent when:**
You can explain the difference between
messages-list memory and SQLite memory
without looking at code.

---

## Agent 3: Reflexion Agent

**File:** `03_reflexion_agent/agent.py`

**Concept:** Agents improve without retraining.
Instead of updating model weights, the agent writes
what went wrong in plain English, stores it, and
reads it before the next attempt.

**No tools needed for this agent.**
Three functions only:
- `attempt(task, past_reflections)` — one try at the task
- `evaluate(task, result)` — LLM scores result 0.0 to 1.0
- `reflect(task, result, score)` — LLM writes what went wrong

**Main loop:**
```python
reflections = []
for attempt_num in range(1, max_attempts + 1):
    result = attempt(task, reflections)
    score = evaluate(task, result)
    if score >= 0.8:
        return result  # success
    reflection = reflect(task, result, score)
    reflections.append(reflection)
    # loop — next attempt sees all past reflections
```

**Test task:**
```
"Write exactly 3 bullet points about photosynthesis.
Each bullet must be under 10 words.
Start each with a dash (-). Nothing else."
```

This task has strict, checkable rules.
Score is easy to calculate objectively.

**Experiments to run:**
1. Remove `reflection_context` from the attempt prompt.
   Run the same task. Does it still improve?
   Compare scores with and without reflections.
2. Print `reflections` list before each attempt.
   Watch it grow. Read what the agent says about itself.
3. Set `max_attempts=1`. Run 10 times.
   How often does it succeed on first try?
   Set `max_attempts=3`. Run 10 times.
   Does more attempts help? By how much?

**You own this agent when:**
You can explain why Reflexion improves performance
without any model training or code changes.

---

## Agent 4: Eval Agent

**File:** `04_eval_agent/agent.py`

**Concept:** "It looks right" is not a measurement.
LLM-as-judge turns subjective quality into a number.
You need numbers to know if your agent is improving.

**No tools needed for this agent.**
Two functions only:
- `get_agent_response(question)` — the agent being tested
- `judge(question, ideal, actual, criteria)` — scores 0.0 or 1.0

**Write 5 test cases minimum:**
```python
TEST_CASES = [
    {
        "input": "What is 2 + 2?",
        "ideal": "4",
        "criteria": "Must contain the number 4"
    },
    # ... 4 more
]
```

**Run eval loop:**
```python
for test in TEST_CASES:
    actual = get_agent_response(test["input"])
    score = judge(test["input"], test["ideal"],
                  actual, test["criteria"])
    scores.append(score)

print(f"Score: {sum(scores)/len(scores):.1%}")
```

**Experiments to run:**
1. Write a deliberately bad judge prompt —
   one that always gives 1.0 regardless.
   Eval shows 100%. This shows why judge quality matters.
   Fix the prompt. Watch score become realistic.
2. Change the agent model from haiku to sonnet.
   Run eval again. Does score improve?
   How much more does it cost per run?
3. Add 5 trick questions you expect the agent to fail.
   What is the failure rate on those specifically?

**You own this agent when:**
You can write a judge prompt that is fair,
specific, and produces consistent scores.

---

## Agent 5: MCP Agent

**File:** `05_mcp_agent/server.py`

**Concept:** MCP exposes your functions as tools
that any MCP-compatible client can call.
Claude Desktop, Cursor, other agents — all can use them.

**Install:**
```bash
pip install fastmcp
```

**Implement 3-4 tools:**
```python
from fastmcp import FastMCP
mcp = FastMCP("Learning MCP")

@mcp.tool()
def get_current_time() -> str:
    """Get the current time"""
    ...

@mcp.tool()
def flip_coin() -> str:
    """Flip a fair coin"""
    ...

@mcp.tool()
def calculate(expression: str) -> str:
    """Evaluate a math expression like '2 + 2'"""
    ...

if __name__ == "__main__":
    mcp.run()
```

**Connect to Claude Desktop:**

Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "learning-mcp": {
      "command": "python",
      "args": ["/full/absolute/path/to/05_mcp_agent/server.py"]
    }
  }
}
```

Restart Claude Desktop after editing config.

**Test in Claude Desktop:**
- "What time is it?"
- "Flip a coin"
- "What is 847 multiplied by 23?"

**Experiments to run:**
1. Add a new tool while Claude Desktop is open.
   Restart Claude Desktop. Ask Claude to use new tool.
2. Write a tool with a vague description like "does stuff".
   Does Claude know when to use it?
   Improve the description. Does behavior change?
3. Deliberately raise an Exception inside a tool.
   What does Claude tell the user when a tool fails?

**You own this agent when:**
Claude Desktop calls your function and you see
your Python code executing in real time.

---

## Agent 6: Self-Healing Agent

**File:** `06_self_healing_agent/agent.py`

**Concept:** Production agents must handle failures
without crashing. Three patterns: schema validation,
retry with backoff, graceful degradation.

**Use Pydantic for strict output schema:**
```python
from pydantic import BaseModel
from typing import Literal

class AgentResponse(BaseModel):
    answer: str
    confidence: Literal["high", "medium", "low"]
    reasoning: str
```

**Healing loop:**
```python
last_error = None
for attempt in range(1, max_retries + 1):
    try:
        prompt = base_prompt
        if last_error:
            prompt += f"\nYour last response failed: {last_error}\nFix it."
        raw = call_llm(prompt)
        result = AgentResponse.model_validate_json(raw)
        return result  # success
    except ValidationError as e:
        last_error = str(e)
    except Exception as e:
        last_error = str(e)
        time.sleep(2 ** attempt)  # exponential backoff

# Graceful degradation — never crash
return AgentResponse(
    answer="Unable to get reliable answer",
    confidence="low",
    reasoning=f"Failed after {max_retries} attempts"
)
```

**Experiments to run:**
1. Remove `last_error` from the retry prompt.
   Claude does not know what went wrong.
   Does it still fix itself? Compare success rates.
2. Change schema to require an integer field.
   Claude often returns a string for integers.
   Watch the validation catch it. Watch retry fix it.
3. Set `max_retries=1`. Run 20 times.
   Count failures. Set `max_retries=3`. Run 20 times.
   Count failures. Calculate the difference.

**You own this agent when:**
You can explain what graceful degradation means
and why returning a low-confidence answer is better
than raising an exception.

---

## Agent 7: Handoff Agent

**File:** `07_handoff_agent/agent.py`

**Concept:** One orchestrator agent routes to specialist
agents. The orchestrator does not answer questions —
it decides who should answer them.

**Implement one orchestrator + three specialists:**

Specialists are plain functions:
```python
def specialist_agent(question: str, specialty: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=f"You are a {specialty} specialist. Be concise.",
        messages=[{"role": "user", "content": question}]
    )
    return response.content[0].text
```

Orchestrator tools:
```python
tools = [
    {
        "name": "ask_math_specialist",
        "description": "For calculations, equations, numbers",
        ...
    },
    {
        "name": "ask_science_specialist",
        "description": "For biology, chemistry, physics",
        ...
    },
    {
        "name": "ask_history_specialist",
        "description": "For historical events and dates",
        ...
    }
]
```

**Test questions:**
```python
orchestrator("What year did Newton formulate calculus?")
orchestrator("What is the square root of 144?")
orchestrator("How does photosynthesis work?")
orchestrator("Compare math in Newton's era to modern calculus")
```

The last question should route to BOTH math and history.
Watch the orchestrator call two specialists.

**Experiments to run:**
1. Ask a question that fits no specialist.
   What does the orchestrator do?
   Does it handle this gracefully?
2. Make all three tool descriptions identical.
   Which specialist gets called? Is it consistent?
   This shows how descriptions drive routing.
3. Add a fourth specialist for a domain you choose.
   Write questions that route to it.
   Verify the routing is correct.

**You own this agent when:**
You can explain why the orchestrator's tool descriptions
control which specialist gets called — and why this
is the same mechanism as in your farming project
except the LLM is making the routing decision.

---

## Agent 8: AutoDebugger

**File:** `08_auto_debugger/agent.py`

**Only start Agent 8 after you can rewrite
Agents 1-7 from memory without looking.**

**Concept:** Everything from agents 1-7 combined
on a real problem. The agent reads failing tests,
diagnoses bugs, applies fixes, runs tests to verify,
and reflects when fixes don't work.

**Combines:**
- Agent 1: the ReAct while-True loop
- Agent 2: memory of past bugs in this codebase
- Agent 3: Reflexion when fix attempt fails
- Agent 4: eval suite measuring fix rate
- Agent 5: MCP server exposing fix_bug as a tool
- Agent 6: self-healing when tools fail
- Agent 7: separate read_agent and fix_agent

**Tools:**
- `read_file(path)` — returns file contents
- `edit_file(path, old_text, new_text)` — applies fix
- `run_tests(test_file)` — returns pass/fail + output

**The loop:**
```
Read error → Read source file → Hypothesize bug →
Edit file → Run tests → Passed? Done : Reflect → Retry
```

**Benchmark:**
Create 20 files in `eval/bugs/` each with one deliberate bug.
Create matching test files that catch each bug.
Measure: how many does the agent fix in ≤ 3 attempts?
Record in `benchmark_results.tsv`:
```
date        without_reflexion   with_reflexion
2026-04-29  45%                 71%
```

That improvement is your resume metric.

---

## Rules When Helping With This Project

1. Never write the complete agent code unprompted.
   Ask the user to attempt it first.
   Only help when they are stuck on something specific.

2. When user shows broken code, ask:
   "What do you think is wrong?" before explaining.
   Guide them to the answer — don't give it.

3. Keep all agents under their line limits.
   If a solution needs more lines — it is too complex.
   Find the simpler version.

4. When user wants to add a feature, ask:
   "Which concept does this teach?"
   If it does not teach something new — do not add it.

5. The experiments after each agent are mandatory.
   Do not let the user skip them.
   Understanding comes from breaking things, not reading.

6. Use `claude-haiku-4-5-20251001` for all agents
   except Agent 8 which may use `claude-sonnet-4-6`.
   Haiku mistakes are cheap. Learning is the goal.

7. If user asks to add LangGraph or LangChain to
   agents 1-7 — decline. Frameworks hide the concepts.
   Frameworks are allowed only in Agent 8 if the user
   has already built 1-7 from scratch.

---

## Common Errors and Fixes

**`AuthenticationError`**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# or create .env file with the key
```

**`tool_use_id does not match`**
The id in your tool_result must exactly match the
id from the tool_use block in the response.
```python
# Get the id from the response block
tool_use_id = block.id
# Use that exact id in tool_result
"tool_use_id": tool_use_id
```

**`ValidationError` from Pydantic**
The LLM returned text that does not match the schema.
Strip markdown code fences before parsing:
```python
clean = raw.strip()
if clean.startswith("```"):
    clean = clean.split("```")[1]
    if clean.startswith("json"):
        clean = clean[4:]
result = MyModel.model_validate_json(clean)
```

**`stop_reason` is always `"end_turn"` — tools never called**
Check that your tool schema is correct.
The `input_schema` must have `"type": "object"`.
The description must clearly say when to use the tool.

**Agent loops forever**
Add a step counter and max_steps limit:
```python
for step in range(max_steps):  # not while True
    ...
```

**MCP server not showing in Claude Desktop**
Path in config must be absolute, not relative.
Restart Claude Desktop after every config change.
Check Claude Desktop logs for server errors.

---

## Progress Tracking

Update this table as you complete each agent:

| Agent | Built | Experiments Done | Can Rewrite From Memory |
|-------|-------|-----------------|------------------------|
| 01 NanoAgent | ☐ | ☐ | ☐ |
| 02 Memory | ☐ | ☐ | ☐ |
| 03 Reflexion | ☐ | ☐ | ☐ |
| 04 Eval | ☐ | ☐ | ☐ |
| 05 MCP | ☐ | ☐ | ☐ |
| 06 Self-Healing | ☐ | ☐ | ☐ |
| 07 Handoff | ☐ | ☐ | ☐ |
| 08 AutoDebugger | ☐ | ☐ | ☐ |

Only move to the next agent when all three boxes
for the current agent are checked.