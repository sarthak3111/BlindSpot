# BlindSpot — AI Critical-Thinking & Decision Quality Analysis Engine

> **Purpose**: Improve the **QUALITY OF THE USER'S REASONING**, not make the decision.

BlindSpot is an AI analysis engine built around a strict critical-thinking framework. It illuminates hidden assumptions, overlooked factors, internal contradictions, evidence gaps, and meaningful trade-offs without nudging, recommending, or deciding for the user.

---

## 🎯 The Reasoning Framework

### Strict Negative Constraints (MUST NOT)
- ❌ **MUST NOT** recommend an option
- ❌ **MUST NOT** rank the user's options
- ❌ **MUST NOT** tell the user what they should choose
- ❌ **MUST NOT** claim certainty about facts not provided
- ❌ **MUST NOT** invent missing information
- ❌ **MUST NOT** tell the user which decision to make

### Active Diagnostic Objectives (SHOULD)
- 🔍 **Identify assumptions** the user appears to be making
- 🔍 **Identify relevant factors** missing from their reasoning
- 🔍 **Identify contradictions or tensions** between their stated priorities and reasoning
- 🔍 **Identify claims** where important evidence is missing
- 🔍 **Identify meaningful trade-offs**
- ❓ **Generate questions** that help the user investigate those blind spots

### Grounding & Classification
Every detected blind spot is strictly grounded in the user's input and categorized as:
1. `OBSERVATION` — Directly supported by facts/statements in the user's input.
2. `HYPOTHESIS` — A plausible concern or risk that requires empirical verification.

For each blind spot, the engine explains:
1. **What was detected**
2. **Why it matters**
3. **What evidence is missing or what assumption is involved**
4. **One investigative question** the user should explore

---

## 📦 Output JSON Schema

The engine outputs structured JSON conforming strictly to the requested schema:

```json
{
  "decision_summary": "Objective synthesis of the dilemma without taking a side.",
  "core_tension": "The central trade-off or conflict in the reasoning.",
  "assumptions": [
    {
      "classification": "OBSERVATION",
      "detected": "What was detected in the reasoning",
      "why_it_matters": "Why this blind spot matters to decision quality",
      "missing_evidence_or_assumption": "Evidence missing or underlying assumption",
      "investigative_question": "One inquiry to test or investigate this item"
    }
  ],
  "overlooked_factors": [],
  "contradictions": [],
  "evidence_gaps": [],
  "tradeoffs": [],
  "questions_to_explore": [
    "High-impact investigative inquiry..."
  ]
}
```

---

## 🚀 Quickstart

### 1. Installation

```bash
cd D:\blindspot
pip install -e .
```

### 2. Command Line Interface (CLI)

#### Analyze directly via arguments:
```bash
python -m blindspot "I want to quit my corporate job to launch an AI startup. I feel I can definitely make $30k MRR in 6 months."
```

#### Output raw structured JSON:
```bash
python -m blindspot --json "Should we build our vector database in-house or buy SaaS?"
```

#### Output formatted Markdown:
```bash
python -m blindspot --markdown --file examples/career_crossroads.json
```

#### Pipe input from stdin:
```bash
cat dilemma.txt | python -m blindspot --json
```

---

## 🌐 Web Application & REST API

Start the interactive server:

```bash
python -m blindspot.api.app
# Server runs at http://localhost:5000
```

### Endpoints:
- `POST /api/analyze` — Run decision analysis on JSON payload:
  ```json
  {
    "user_input": "Your reasoning text...",
    "options": ["Option A", "Option B"],
    "context": "Stated priorities...",
    "provider": "gemini | openai | anthropic | heuristic",
    "temperature": 0.2
  }
  ```
- `GET /api/health` — Service health and active provider status.
- `GET /api/schema` — JSON Schema definition for validation.
- `GET /` — Interactive web UI for testing dilemmas with visual badges for `OBSERVATION` vs `HYPOTHESIS`.

---

## 🔌 Supported LLM Providers

BlindSpot includes a pluggable provider architecture:

1. **Google Gemini (`GeminiProvider`)**
   - Configured via `GEMINI_API_KEY` (default model: `gemini-2.5-flash`).
2. **OpenAI & Compatible (`OpenAICompatibleProvider`)**
   - Configured via `OPENAI_API_KEY` and optional `OPENAI_BASE_URL` (compatible with Groq, Ollama, vLLM, OpenRouter).
3. **Anthropic Claude (`AnthropicProvider`)**
   - Configured via `ANTHROPIC_API_KEY` (default model: `claude-3-5-haiku-20241022`).
4. **Heuristic Engine (`HeuristicMockProvider`)**
   - Deterministic local analytical engine that requires **no external API keys**, ideal for offline environments, CI/CD, and testing.

---

## 🛡️ Guardrails & Safety Enforcers

BlindSpot includes an integrated `GuardrailValidator`:
- **Scans for recommendations**: Flags phrases like *"I recommend"*, *"You should choose"*, *"The best option is"*.
- **Scans for ranking**: Flags phrases like *"Ranked #1"*, *"In order of preference"*.
- **Scans for directive choice**: Prevents telling the user what decision to make.
- **Validates classification**: Asserts all items are designated `OBSERVATION` or `HYPOTHESIS`.
- **Enforces 4 required facets**: Asserts `detected`, `why_it_matters`, `missing_evidence_or_assumption`, and `investigative_question` are present.

In strict mode (`strict_guardrails=True`), any critical violation triggers self-correction or raises `GuardrailViolationError`.

---

## 🧪 Running the Test Suite

```bash
python -m pytest tests -v
```

All 24 unit and integration tests verify:
- Complete framework adherence
- Strict schema compliance
- Zero recommendations and rankings
- Reversibility, four-facet item validation, and classification checks
- Parser recovery from malformed JSON and markdown fences
- API endpoint health and validation responses
