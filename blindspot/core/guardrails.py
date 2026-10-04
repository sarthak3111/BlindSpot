"""Guardrails and compliance enforcement for the BlindSpot AI analysis engine."""

from __future__ import annotations
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from blindspot.core.models import AnalysisResult, ClassificationType, BlindSpotItem


class ViolationSeverity(str):
    CRITICAL = "CRITICAL"  # Blatant violation (e.g., direct recommendation or ranking)
    WARNING = "WARNING"    # Potential drift or weak grounding


class GuardrailViolation(BaseModel):
    rule: str
    severity: str
    message: str
    context_snippet: Optional[str] = None


class GuardrailReport(BaseModel):
    passed: bool
    violations: List[GuardrailViolation] = Field(default_factory=list)
    warnings: List[GuardrailViolation] = Field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        return any(v.severity == ViolationSeverity.CRITICAL for v in self.violations)


class GuardrailValidator:
    """Validates that an analysis strictly adheres to the BlindSpot constraints:
    - MUST NOT recommend an option
    - MUST NOT rank options
    - MUST NOT tell the user what they should choose
    - MUST distinguish between OBSERVATION and HYPOTHESIS
    - MUST populate all 4 required facets for each blind spot
    """

    # Recommendation and decision-forcing patterns
    RECOMMENDATION_PATTERNS = [
        r"\bi\s+recommend\b",
        r"\bwe\s+recommend\b",
        r"\bmy\s+recommendation\b",
        r"\byou\s+should\s+(choose|pick|select|go\s+with|take|opt\s+for|decide\s+on)\b",
        r"\byou\s+ought\s+to\s+(choose|pick|select|go\s+with)\b",
        r"\bthe\s+best\s+(option|choice|decision|alternative)\s+is\b",
        r"\bthe\s+clear\s+winner\s+is\b",
        r"\b(option|choice)\s+[A-Za-z0-9]+\s+is\s+(better|superior|preferable)\b",
        r"\bi\s+advise\s+you\s+to\s+(choose|pick|select)\b",
        r"\bgo\s+with\s+(option|choice)\b",
        r"\byou\s+must\s+decide\s+to\b",
        r"\bthe\s+right\s+decision\s+is\b",
        r"\bthe\s+optimal\s+choice\s+is\b"
    ]

    # Ranking patterns
    RANKING_PATTERNS = [
        r"\branked?\s*#?\s*\d+\b",
        r"\brank\s+(order|ordering)\b",
        r"\bin\s+order\s+of\s+preference\b",
        r"\b(first|second|third)\s+choice\s+is\b",
        r"\bscores?\s+(higher|lower)\s+than\b",
        r"\branks?\s+(higher|lower|above|below)\b"
    ]

    def __init__(self, custom_disallowed_phrases: Optional[List[str]] = None):
        self.disallowed_phrases = custom_disallowed_phrases or []

    def validate(self, result: AnalysisResult, user_input: str = "") -> GuardrailReport:
        violations: List[GuardrailViolation] = []
        warnings: List[GuardrailViolation] = []

        # 1. Text scans for recommendation & ranking across all fields
        all_text_blocks = self._extract_all_text(result)

        for location, text in all_text_blocks.items():
            lower_text = text.lower()

            for pattern in self.RECOMMENDATION_PATTERNS:
                match = re.search(pattern, lower_text)
                if match:
                    violations.append(GuardrailViolation(
                        rule="NO_RECOMMENDATION",
                        severity=ViolationSeverity.CRITICAL,
                        message=f"Found explicit recommendation pattern '{match.group(0)}' in {location}.",
                        context_snippet=text[max(0, match.start() - 30): min(len(text), match.end() + 30)]
                    ))

            for pattern in self.RANKING_PATTERNS:
                match = re.search(pattern, lower_text)
                if match:
                    violations.append(GuardrailViolation(
                        rule="NO_RANKING",
                        severity=ViolationSeverity.CRITICAL,
                        message=f"Found ranking pattern '{match.group(0)}' in {location}.",
                        context_snippet=text[max(0, match.start() - 30): min(len(text), match.end() + 30)]
                    ))

            for phrase in self.disallowed_phrases:
                if phrase.lower() in lower_text:
                    violations.append(GuardrailViolation(
                        rule="DISALLOWED_PHRASE",
                        severity=ViolationSeverity.CRITICAL,
                        message=f"Disallowed phrase '{phrase}' detected in {location}.",
                        context_snippet=text
                    ))

        # 2. Check structure and classification for all blind spot categories
        categories = {
            "assumptions": result.assumptions,
            "overlooked_factors": result.overlooked_factors,
            "contradictions": result.contradictions,
            "evidence_gaps": result.evidence_gaps,
            "tradeoffs": result.tradeoffs
        }

        total_items = 0
        for cat_name, items in categories.items():
            for idx, item in enumerate(items, 1):
                total_items += 1
                loc = f"{cat_name}[{idx}]"

                # Check classification
                if item.classification not in (ClassificationType.OBSERVATION, ClassificationType.HYPOTHESIS):
                    violations.append(GuardrailViolation(
                        rule="INVALID_CLASSIFICATION",
                        severity=ViolationSeverity.CRITICAL,
                        message=f"Item at {loc} has invalid classification '{item.classification}'. Must be OBSERVATION or HYPOTHESIS.",
                        context_snippet=item.detected
                    ))

                # Check required fields
                if not item.detected or len(item.detected.strip()) < 5:
                    violations.append(GuardrailViolation(
                        rule="INSUFFICIENT_DETECTION",
                        severity=ViolationSeverity.CRITICAL,
                        message=f"Item at {loc} is missing 'detected' description.",
                        context_snippet=str(item)
                    ))

                if not item.why_it_matters or len(item.why_it_matters.strip()) < 5:
                    warnings.append(GuardrailViolation(
                        rule="MISSING_IMPACT",
                        severity=ViolationSeverity.WARNING,
                        message=f"Item at {loc} has minimal or missing 'why_it_matters'.",
                        context_snippet=item.detected
                    ))

                if not item.missing_evidence_or_assumption or len(item.missing_evidence_or_assumption.strip()) < 5:
                    warnings.append(GuardrailViolation(
                        rule="MISSING_EVIDENCE_OR_ASSUMPTION",
                        severity=ViolationSeverity.WARNING,
                        message=f"Item at {loc} has missing 'missing_evidence_or_assumption'.",
                        context_snippet=item.detected
                    ))

                if not item.investigative_question or len(item.investigative_question.strip()) < 5:
                    warnings.append(GuardrailViolation(
                        rule="MISSING_INVESTIGATIVE_QUESTION",
                        severity=ViolationSeverity.WARNING,
                        message=f"Item at {loc} is missing 'investigative_question'.",
                        context_snippet=item.detected
                    ))

        # 3. Decision summary check
        if not result.decision_summary or len(result.decision_summary.strip()) < 10:
            warnings.append(GuardrailViolation(
                rule="WEAK_DECISION_SUMMARY",
                severity=ViolationSeverity.WARNING,
                message="Decision summary is empty or too short to be meaningful."
            ))

        if not result.core_tension or len(result.core_tension.strip()) < 10:
            warnings.append(GuardrailViolation(
                rule="WEAK_CORE_TENSION",
                severity=ViolationSeverity.WARNING,
                message="Core tension is empty or too short."
            ))

        passed = len(violations) == 0
        return GuardrailReport(passed=passed, violations=violations, warnings=warnings)

    def _extract_all_text(self, result: AnalysisResult) -> Dict[str, str]:
        blocks = {
            "decision_summary": result.decision_summary,
            "core_tension": result.core_tension,
        }

        for q_idx, q in enumerate(result.questions_to_explore):
            blocks[f"questions_to_explore[{q_idx}]"] = q

        categories = {
            "assumptions": result.assumptions,
            "overlooked_factors": result.overlooked_factors,
            "contradictions": result.contradictions,
            "evidence_gaps": result.evidence_gaps,
            "tradeoffs": result.tradeoffs
        }

        for cat_name, items in categories.items():
            for idx, item in enumerate(items):
                blocks[f"{cat_name}[{idx}].detected"] = item.detected
                blocks[f"{cat_name}[{idx}].why_it_matters"] = item.why_it_matters
                blocks[f"{cat_name}[{idx}].missing_evidence_or_assumption"] = item.missing_evidence_or_assumption
                blocks[f"{cat_name}[{idx}].investigative_question"] = item.investigative_question

        return blocks
