"""Command-line interface for the BlindSpot AI analysis engine."""

from __future__ import annotations
import sys
import argparse
import json
from pathlib import Path
from typing import Optional

# Ensure UTF-8 output on Windows terminals
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from blindspot.core.engine import BlindSpotEngine, GuardrailViolationError
from blindspot.core.models import AnalysisRequest, AnalysisResult


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blindspot",
        description="BlindSpot: AI Critical-Thinking Assistant for Decision Analysis"
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="User reasoning text or dilemma to analyze. If omitted, reads from stdin or prompts interactively."
    )
    parser.add_argument(
        "--file", "-f",
        type=Path,
        help="Path to a text file containing the user's reasoning."
    )
    parser.add_argument(
        "--context", "-c",
        type=str,
        default=None,
        help="Additional context or stated priorities."
    )
    parser.add_argument(
        "--option", "-o",
        action="append",
        dest="options",
        help="Explicit option being weighed (can be specified multiple times, e.g. -o 'Stay' -o 'Leave')."
    )
    parser.add_argument(
        "--provider", "-p",
        choices=["gemini", "openai", "anthropic", "heuristic"],
        default=None,
        help="LLM provider backend (defaults to heuristic or environment setting)."
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="Model identifier."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw structured JSON strictly adhering to schema."
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Output formatted markdown report."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write output to a designated file."
    )
    parser.add_argument(
        "--non-strict",
        action="store_true",
        help="Do not abort on guardrail violations."
    )
    return parser


def format_cli_output(result: AnalysisResult) -> str:
    """Format the analysis result nicely for terminal display."""
    lines = []
    separator = "=" * 70
    sub_sep = "-" * 70

    lines.append(separator)
    lines.append("  BLINDSPOT — CRITICAL THINKING ANALYSIS ENGINE")
    lines.append(separator)
    lines.append("")
    lines.append(f"DECISION SUMMARY:\n  {result.decision_summary}")
    lines.append("")
    lines.append(f"CORE TENSION:\n  {result.core_tension}")
    lines.append("")

    def _render_section(title: str, items):
        lines.append(sub_sep)
        lines.append(f"{title} ({len(items)}):")
        lines.append(sub_sep)
        if not items:
            lines.append("  (No high-impact blind spots detected in this category)\n")
            return
        for i, it in enumerate(items, 1):
            badge = f"[{it.classification.value}]"
            lines.append(f"  {i}. {badge} {it.detected}")
            lines.append(f"     - Why It Matters: {it.why_it_matters}")
            lines.append(f"     - Evidence/Assumption: {it.missing_evidence_or_assumption}")
            lines.append(f"     - Investigative Question: {it.investigative_question}")
            lines.append("")

    _render_section("ASSUMPTIONS", result.assumptions)
    _render_section("OVERLOOKED FACTORS", result.overlooked_factors)
    _render_section("CONTRADICTIONS & TENSIONS", result.contradictions)
    _render_section("EVIDENCE GAPS", result.evidence_gaps)
    _render_section("TRADE-OFFS", result.tradeoffs)

    lines.append(sub_sep)
    lines.append("KEY QUESTIONS TO EXPLORE:")
    lines.append(sub_sep)
    for i, q in enumerate(result.questions_to_explore, 1):
        lines.append(f"  {i}. {q}")
    lines.append("")
    lines.append(separator)
    meta = result.metadata
    if meta:
        lines.append(f"Metadata: Provider={meta.get('provider')} | Model={meta.get('model')} | Latency={meta.get('latency_ms')}ms | Guardrails Passed={meta.get('guardrails_passed')}")
        lines.append(separator)

    return "\n".join(lines)


def main(args=None):
    parser = create_parser()
    parsed = parser.parse_args(args)

    # Determine input text
    input_text = None
    if parsed.file:
        if not parsed.file.exists():
            sys.stderr.write(f"Error: File not found: {parsed.file}\n")
            sys.exit(1)
        input_text = parsed.file.read_text(encoding="utf-8")
    elif parsed.input:
        input_text = parsed.input
    elif not sys.stdin.isatty():
        input_text = sys.stdin.read()
    else:
        # Interactive prompt
        print("BlindSpot: Enter your decision dilemma and reasoning (Type 'END' on a new line when done):")
        lines = []
        try:
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
        except EOFError:
            pass
        input_text = "\n".join(lines)

    if not input_text or not input_text.strip():
        sys.stderr.write("Error: No reasoning input provided for analysis.\n")
        parser.print_help()
        sys.exit(1)

    engine = BlindSpotEngine(
        provider_name=parsed.provider,
        model=parsed.model,
        strict_guardrails=not parsed.non_strict
    )

    try:
        result = engine.analyze(
            user_input=input_text,
            options=parsed.options,
            context=parsed.context
        )
    except GuardrailViolationError as gve:
        sys.stderr.write(f"\n[Guardrail Violation Error] {gve}\n")
        sys.exit(2)
    except Exception as e:
        sys.stderr.write(f"\n[Engine Error] {e}\n")
        sys.exit(1)

    # Output generation
    if parsed.json:
        output_str = result.to_json(indent=2)
    elif parsed.markdown:
        output_str = result.to_markdown()
    else:
        output_str = format_cli_output(result)

    if parsed.output:
        parsed.output.write_text(output_str, encoding="utf-8")
        print(f"Analysis saved to {parsed.output}")
    else:
        print(output_str)


if __name__ == "__main__":
    main()
