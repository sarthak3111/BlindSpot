"""Pydantic models and schemas for the BlindSpot AI analysis engine."""

from __future__ import annotations
import json
from enum import Enum
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class ClassificationType(str, Enum):
    OBSERVATION = "OBSERVATION"
    HYPOTHESIS = "HYPOTHESIS"


class BlindSpotItem(BaseModel):
    """Represents an individual detected blind spot according to the BlindSpot framework.
    
    Attributes:
        classification: OBSERVATION (directly supported by input) or HYPOTHESIS (plausible concern).
        detected: What was detected in the user's reasoning.
        why_it_matters: The potential impact or why this matters to the decision.
        missing_evidence_or_assumption: What evidence is missing or what assumption is involved.
        investigative_question: One question the user should investigate.
    """
    classification: ClassificationType = Field(
        default=ClassificationType.HYPOTHESIS,
        description="Distinguishes between OBSERVATION (directly supported by user input) and HYPOTHESIS (plausible concern requiring verification)."
    )
    detected: str = Field(
        ...,
        description="Concise description of what was detected in the reasoning."
    )
    why_it_matters: str = Field(
        ...,
        description="Why this blind spot matters to the decision outcome."
    )
    missing_evidence_or_assumption: str = Field(
        ...,
        description="What evidence is missing or what assumption is involved."
    )
    investigative_question: str = Field(
        ...,
        description="One actionable question the user should investigate."
    )

    @field_validator("classification", mode="before")
    @classmethod
    def normalize_classification(cls, value: Any) -> ClassificationType:
        if isinstance(value, ClassificationType):
            return value
        if isinstance(value, str):
            clean = value.strip().upper()
            if "OBSERV" in clean:
                return ClassificationType.OBSERVATION
            return ClassificationType.HYPOTHESIS
        return ClassificationType.HYPOTHESIS

    @model_validator(mode="before")
    @classmethod
    def map_aliases_and_coerce(cls, data: Any) -> Any:
        if isinstance(data, str):
            # Fallback if a plain string is received
            return {
                "classification": ClassificationType.HYPOTHESIS,
                "detected": data,
                "why_it_matters": "Unaddressed factor in reasoning",
                "missing_evidence_or_assumption": "Empirical evidence or validation is not provided",
                "investigative_question": f"What additional facts would test: '{data}'?"
            }
        if not isinstance(data, dict):
            return data

        # Mapping common aliases
        detected = (
            data.get("detected")
            or data.get("what_detected")
            or data.get("what_was_detected")
            or data.get("description")
            or data.get("claim")
            or data.get("item")
            or "Unspecified blind spot"
        )
        why_it_matters = (
            data.get("why_it_matters")
            or data.get("why_matters")
            or data.get("impact")
            or data.get("significance")
            or "May significantly impact the ultimate decision quality."
        )
        missing_evidence = (
            data.get("missing_evidence_or_assumption")
            or data.get("evidence_missing_or_assumption")
            or data.get("evidence_or_assumption")
            or data.get("missing_evidence")
            or data.get("evidence_missing")
            or data.get("assumption")
            or "Underlying basis requires verification."
        )
        question = (
            data.get("investigative_question")
            or data.get("question")
            or data.get("question_to_investigate")
            or data.get("inquiry")
            or "How can this factor be reliably validated?"
        )
        classification = (
            data.get("classification")
            or data.get("type")
            or data.get("category_type")
            or "HYPOTHESIS"
        )

        return {
            "classification": classification,
            "detected": detected,
            "why_it_matters": why_it_matters,
            "missing_evidence_or_assumption": missing_evidence,
            "investigative_question": question
        }


class AnalysisResult(BaseModel):
    """The structured result of the BlindSpot analysis engine."""
    decision_summary: str = Field(
        ...,
        description="Objective summary of the user's dilemma without taking a stance."
    )
    core_tension: str = Field(
        ...,
        description="The primary tension, conflict, or trade-off in the reasoning."
    )
    assumptions: List[BlindSpotItem] = Field(
        default_factory=list,
        description="Assumptions the user appears to be making."
    )
    overlooked_factors: List[BlindSpotItem] = Field(
        default_factory=list,
        description="Relevant factors missing from their reasoning."
    )
    contradictions: List[BlindSpotItem] = Field(
        default_factory=list,
        description="Contradictions or tensions between stated priorities and reasoning."
    )
    evidence_gaps: List[BlindSpotItem] = Field(
        default_factory=list,
        description="Claims where important evidence is missing."
    )
    tradeoffs: List[BlindSpotItem] = Field(
        default_factory=list,
        description="Meaningful trade-offs inherent in the dilemma."
    )
    questions_to_explore: List[str] = Field(
        default_factory=list,
        description="High-impact questions to help the user investigate blind spots."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata including provider, model, latency, and guardrail validation."
    )

    @field_validator("questions_to_explore", mode="before")
    @classmethod
    def normalize_questions(cls, value: Any) -> List[str]:
        if not value:
            return []
        if isinstance(value, list):
            res = []
            for item in value:
                if isinstance(item, str):
                    res.append(item.strip())
                elif isinstance(item, dict):
                    q = item.get("question") or item.get("investigative_question") or str(item)
                    res.append(str(q).strip())
                else:
                    res.append(str(item).strip())
            return res
        if isinstance(value, str):
            return [value.strip()]
        return []

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary strictly matching the requested JSON schema."""
        return self.model_dump(exclude={"metadata"})

    def to_json(self, indent: int = 2) -> str:
        """Serialize to formatted JSON."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_markdown(self) -> str:
        """Render a clean, human-readable markdown report."""
        lines = [
            "# BlindSpot Analysis Report",
            "",
            "> **Purpose**: Improve reasoning quality without deciding, ranking, or recommending.",
            "",
            f"### Decision Summary\n{self.decision_summary}\n",
            f"### Core Tension\n{self.core_tension}\n"
        ]

        def _format_section(title: str, items: List[BlindSpotItem]):
            lines.append(f"### {title} ({len(items)})")
            if not items:
                lines.append("_None detected directly in the reasoning._\n")
                return
            for i, item in enumerate(items, 1):
                badge = f"`[{item.classification.value}]`"
                lines.extend([
                    f"**{i}. {badge} {item.detected}**",
                    f"- **Why It Matters**: {item.why_it_matters}",
                    f"- **Evidence/Assumption**: {item.missing_evidence_or_assumption}",
                    f"- **Investigative Question**: *{item.investigative_question}*",
                    ""
                ])

        _format_section("Assumptions", self.assumptions)
        _format_section("Overlooked Factors", self.overlooked_factors)
        _format_section("Contradictions & Tensions", self.contradictions)
        _format_section("Evidence Gaps", self.evidence_gaps)
        _format_section("Trade-Offs", self.tradeoffs)

        lines.append(f"### Key Questions to Explore ({len(self.questions_to_explore)})")
        for q in self.questions_to_explore:
            lines.append(f"- {q}")
        lines.append("")

        return "\n".join(lines)


class AnalysisRequest(BaseModel):
    """Input payload for the BlindSpot analysis engine."""
    user_input: str = Field(
        ...,
        description="The user's stated reasoning, dilemmas, options, and arguments."
    )
    options: Optional[List[str]] = Field(
        default=None,
        description="Optional list of discrete options the user is weighing."
    )
    context: Optional[str] = Field(
        default=None,
        description="Optional context or stated priorities."
    )
    provider: Optional[str] = Field(
        default=None,
        description="LLM provider name: 'gemini', 'openai', 'anthropic', or 'heuristic'."
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model identifier to use."
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Sampling temperature (low values recommended for critical-thinking precision)."
    )
    strict_guardrails: bool = Field(
        default=True,
        description="Whether to run post-generation guardrail validation."
    )
