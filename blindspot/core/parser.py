"""JSON response parser and sanitizer for BlindSpot engine."""

from __future__ import annotations
import json
import re
from typing import Dict, Any
from blindspot.core.models import AnalysisResult


class ResponseParsingError(ValueError):
    """Raised when the engine fails to extract or parse valid JSON."""
    pass


def extract_json_str(raw_text: str) -> str:
    """Extract a JSON object substring from raw LLM output text."""
    text = raw_text.strip()

    # 1. Check for markdown code fences ```json ... ```
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    fence_matches = re.findall(fence_pattern, text, re.IGNORECASE)
    if fence_matches:
        # Choose the largest match or first non-empty
        for match in fence_matches:
            match = match.strip()
            if match.startswith("{") and match.endswith("}"):
                return match

    # 2. Look for outermost balanced { and }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace:last_brace + 1]

    return text


def clean_json_text(json_str: str) -> str:
    """Attempt basic repairs for common LLM JSON syntax quirks (trailing commas, comments, smart quotes, etc.)."""
    s = json_str.strip()
    
    # Replace smart quotes with standard ASCII quotes
    s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

    # Normalize any echoed pseudo-code in classification
    s = re.sub(r'"classification"\s*:\s*"OBSERVATION"\s*or\s*"HYPOTHESIS"', '"classification": "OBSERVATION"', s, flags=re.IGNORECASE)

    # Remove single line comments // ... (not inside URLs)
    s = re.sub(r'(?<!:)\/\/[^\n]*', '', s)

    # Remove multi-line comments /* ... */
    s = re.sub(r'\/\*[\s\S]*?\*\/', '', s)

    # Remove trailing commas before closing braces/brackets
    s = re.sub(r",\s*([\]}])", r"\1", s)
    return s.strip()


def parse_analysis_response(raw_text: str) -> AnalysisResult:
    """Parse raw LLM response into an AnalysisResult.
    
    Raises:
        ResponseParsingError: If valid JSON cannot be extracted or parsed.
    """
    candidate = extract_json_str(raw_text)
    candidate_cleaned = clean_json_text(candidate)

    try:
        data = json.loads(candidate_cleaned)
    except json.JSONDecodeError as primary_err:
        # Try raw candidate as fallback
        try:
            data = json.loads(candidate)
        except Exception:
            snippet = candidate_cleaned[:200] + ("..." if len(candidate_cleaned) > 200 else "")
            raise ResponseParsingError(
                f"Failed to parse LLM response into valid JSON: {primary_err}. Content snippet: {snippet}"
            ) from primary_err

    if not isinstance(data, dict):
        raise ResponseParsingError(f"Expected JSON object (dict), but got {type(data).__name__}")

    # Ensure required top-level keys exist or have fallbacks
    normalized_data: Dict[str, Any] = {
        "decision_summary": data.get("decision_summary") or data.get("summary") or "Dilemma under analysis.",
        "core_tension": data.get("core_tension") or data.get("tension") or "Core trade-off requires clarification.",
        "assumptions": data.get("assumptions") or [],
        "overlooked_factors": data.get("overlooked_factors") or data.get("overlooked") or [],
        "contradictions": data.get("contradictions") or [],
        "evidence_gaps": data.get("evidence_gaps") or data.get("missing_evidence") or [],
        "tradeoffs": data.get("tradeoffs") or data.get("trade_offs") or [],
        "questions_to_explore": data.get("questions_to_explore") or data.get("questions") or []
    }

    try:
        return AnalysisResult(**normalized_data)
    except Exception as validation_err:
        raise ResponseParsingError(f"Schema validation error on parsed data: {validation_err}") from validation_err
