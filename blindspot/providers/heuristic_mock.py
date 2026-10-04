"""Heuristic mock provider for offline testing, deterministic evaluation, and demonstration."""

from __future__ import annotations
import json
import re
from typing import Dict, Any, List, Optional
from blindspot.providers.base import BaseLLMProvider


class HeuristicMockProvider(BaseLLMProvider):
    """A deterministic heuristic analysis engine that executes the BlindSpot framework
    without requiring external API keys. Ideal for testing, continuous integration,
    and offline scenarios.
    """

    def __init__(self, model: Optional[str] = "heuristic-v1", **kwargs):
        super().__init__(model=model, **kwargs)

    @property
    def provider_name(self) -> str:
        return "heuristic"

    def generate(
        self,
        user_prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
        **kwargs
    ) -> str:
        parsed_data = self._extract_prompt_data(user_prompt)
        result = self._analyze_heuristically(parsed_data)
        return json.dumps(result, indent=2, ensure_ascii=False)

    def _extract_prompt_data(self, prompt: str) -> Dict[str, Any]:
        data = {"user_input": "", "options": [], "context": ""}

        if "=== USER REASONING INPUT ===" in prompt:
            parts = prompt.split("=== USER REASONING INPUT ===")
            sub = parts[1]
            if "=== " in sub:
                data["user_input"] = sub.split("=== ")[0].strip()
            else:
                data["user_input"] = sub.strip()
        else:
            data["user_input"] = prompt.strip()

        if "=== EXPLICIT OPTIONS CONSIDERED ===" in prompt:
            parts = prompt.split("=== EXPLICIT OPTIONS CONSIDERED ===")
            sub = parts[1]
            if "=== " in sub:
                opts_block = sub.split("=== ")[0].strip()
            else:
                opts_block = sub.strip()
            data["options"] = [
                line.lstrip("- *0123456789.").strip()
                for line in opts_block.split("\n")
                if line.strip()
            ]

        if "=== ADDITIONAL CONTEXT / STATED PRIORITIES ===" in prompt:
            parts = prompt.split("=== ADDITIONAL CONTEXT / STATED PRIORITIES ===")
            sub = parts[1]
            if "=== " in sub:
                data["context"] = sub.split("=== ")[0].strip()
            else:
                data["context"] = sub.strip()

        return data

    def _analyze_heuristically(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        text = parsed["user_input"]
        context = parsed.get("context", "")
        options = parsed.get("options", [])
        combined = f"{text} {context} {' '.join(options)}".strip()
        lower = combined.lower()

        # 1. Decision Summary
        if "internship" in lower:
            summary = "Evaluating whether to accept a 6-month internship while managing college coursework and academic exam schedules."
            tension = "Immediate industry exposure and financial stipend versus academic performance, attendance requirements, and exam preparation."
        elif "stay" in lower and any(w in lower for w in ["leave", "quit", "move"]):
            summary = "Evaluating whether to remain in current position or transition to an alternative path."
            tension = "Balancing known stability and organizational familiarity against prospective growth and unverified upside."
        elif "startup" in lower and any(w in lower for w in ["corporate", "big tech", "faang", "microsoft", "google"]):
            summary = "Weighing an opportunity at an early-stage startup against a position in an established corporate environment."
            tension = "High-risk / high-equity upside versus stable compensation, predictable scope, and established infrastructure."
        elif "build" in lower and any(w in lower for w in ["buy", "adopt", "saas"]):
            summary = "Deliberating between building a custom in-house solution versus adopting an existing commercial or third-party service."
            tension = "High upfront engineering investment and maintenance overhead versus long-term flexibility and domain alignment."
        elif options:
            summary = f"Evaluating decision dilemma between: {options[0]} and {options[1] if len(options) > 1 else 'alternative'}."
            tension = "Tension between baseline certainty and the trade-offs of proposed alternative paths."
        else:
            first_sentence = [line.strip() for line in text.split("\n") if line.strip()][0] if text else "Decision dilemma under evaluation."
            summary = f"Evaluating options regarding: {first_sentence[:120]}"
            tension = "Tension between current baseline certainty and the uncertain trade-offs of proposed alternative paths."

        assumptions = []
        overlooked_factors = []
        contradictions = []
        evidence_gaps = []
        tradeoffs = []
        questions_to_explore = []

        sentences = [s.strip() for s in re.split(r"[.!?]", text) if len(s.strip()) > 8]

        # Specific: Internship & Academics
        if "internship" in lower:
            assumptions.append({
                "classification": "HYPOTHESIS",
                "detected": "Assumption that physical proximity to home and the internship title will translate into meaningful engineering mentorship and career acceleration.",
                "why_it_matters": "Convenience and nominal industry experience do not guarantee substantive project ownership; intern work can often be routine or peripheral.",
                "missing_evidence_or_assumption": "Assumes the host team has designated engineering mentors and structured, hands-on intern project milestones.",
                "investigative_question": "What concrete projects, tech stack, and dedicated senior mentorship will you be assigned during the 6 months?"
            })

            overlooked_factors.append({
                "classification": "OBSERVATION",
                "detected": "College mandatory attendance regulations, exam leave policies, and lab session scheduling are unaddressed.",
                "why_it_matters": "Strict university attendance thresholds and sudden exam dates can trigger academic debarment if uncoordinated with corporate work hours.",
                "missing_evidence_or_assumption": "Absence of written college department approvals (NOC) and documented employer policy on exam leaves.",
                "investigative_question": "Has your department head granted formal approval for this 6-month schedule, and will the employer contractually allow exam study leaves?"
            })

            contradictions.append({
                "classification": "OBSERVATION",
                "detected": "Simultaneous priority on top academic standing alongside a demanding 6-month corporate schedule.",
                "why_it_matters": "Full working day commitments directly compress study hours and exam preparation bandwidth, risking GPA degradation.",
                "missing_evidence_or_assumption": "Assumes energy and time management can absorb 40+ weekly hours of professional commitment without grade penalties.",
                "investigative_question": "How many weekly study hours do your upcoming exams require, and when will those hours occur if working regular business shifts?"
            })

            evidence_gaps.append({
                "classification": "OBSERVATION",
                "detected": "The substantive quality and scope of 'industry experience' are stated without a written role syllabus.",
                "why_it_matters": "Without an agreed scope of work, interns often end up assigned to QA, documentation, or operational support rather than core development.",
                "missing_evidence_or_assumption": "Absence of an official offer letter specifying technical deliverables, deliverables cadence, and team placement.",
                "investigative_question": "What specific codebases, features, or architecture components will you independently deliver during the tenure?"
            })

            tradeoffs.append({
                "classification": "OBSERVATION",
                "detected": "Near-term financial independence (₹30,000 stipend) and proximity versus potential academic GPA risk and exam performance.",
                "why_it_matters": "While ₹30,000 provides immediate financial relief, cumulative GPA carries long-term gating implications for graduate studies and campus placements.",
                "missing_evidence_or_assumption": "Assumes the immediate earnings and initial resume line outweigh any potential dip in cumulative academic standing.",
                "investigative_question": "If your exam GPA drops by one full grade point, does the brand reputation of this internship compensate for that permanent academic record?"
            })

            questions_to_explore.extend([
                "How will you handle non-negotiable semester exam days if they coincide with critical corporate project deliverables?",
                "Has the company verified in writing whether daily work hours can be adjusted around mandatory campus labs or lectures?",
                "What specific skill or credential will you have at the end of 6 months that you could not acquire through focused campus projects?",
                "If forced to choose midway between meeting a project deadline and securing top exam marks, which outcome takes precedence?"
            ])

        else:
            # General / Tech / Career reasoning
            certainty_matches = [
                s for s in sentences
                if any(w in s.lower() for w in ["definitely", "obviously", "guaranteed", "surely", "bound to", "will certainly"])
            ]
            if certainty_matches:
                target_s = certainty_matches[0]
                assumptions.append({
                    "classification": "OBSERVATION",
                    "detected": f"Definitive projection stated without empirical proof: '{target_s}'",
                    "why_it_matters": "Treating an uncertain future projection as a guaranteed outcome biases risk estimation.",
                    "missing_evidence_or_assumption": "Assumes outcome probability is near 100% despite inherent market or situational volatility.",
                    "investigative_question": f"What specific evidence or historical precedent supports the certainty of '{target_s}'?"
                })
            else:
                assumptions.append({
                    "classification": "HYPOTHESIS",
                    "detected": "Implicit assumption that non-quantified variables will remain constant during the transition.",
                    "why_it_matters": "Unstated baseline stability assumptions fail if external dependencies shift.",
                    "missing_evidence_or_assumption": "Lacks longitudinal data on workload, team dynamics, or resource runway.",
                    "investigative_question": "Which currently stable conditions are most vulnerable to disruption once this decision is executed?"
                })

            if any(w in lower for w in ["salary", "equity", "money", "pay", "cost", "budget", "compensation", "stipend", "₹", "inr"]):
                tradeoffs.append({
                    "classification": "OBSERVATION",
                    "detected": "Financial trade-off between guaranteed liquid compensation and deferred or variable valuation.",
                    "why_it_matters": "Changes in cash flow liquidity impact personal or operational runway during adverse scenarios.",
                    "missing_evidence_or_assumption": "Assumes expected monetary value compensates for higher liquidity risk.",
                    "investigative_question": "What is the minimum viable financial runway needed if projected upsides take twice as long to materialize?"
                })
            else:
                tradeoffs.append({
                    "classification": "HYPOTHESIS",
                    "detected": "Trade-off between immediate execution speed and long-term technical or strategic debt.",
                    "why_it_matters": "Prioritizing immediate relief often compounds structural complexity later.",
                    "missing_evidence_or_assumption": "Quantitative assessment of downstream maintenance obligations.",
                    "investigative_question": "What recurring operational debt will be incurred by choosing the faster alternative?"
                })

            if any(w in lower for w in ["stability", "security", "stress", "burnout", "work-life", "wlb"]):
                contradictions.append({
                    "classification": "OBSERVATION",
                    "detected": "Stated desire for stability or well-being while contemplating high-friction or volatile operational conditions.",
                    "why_it_matters": "Pursuing demanding or uncertain environments can directly undermine the stated priority of peace of mind.",
                    "missing_evidence_or_assumption": "Assumes personal resilience can absorb increased friction without impacting performance.",
                    "investigative_question": "Under what specific conditions would this choice jeopardize your stated need for stability?"
                })
            else:
                contradictions.append({
                    "classification": "HYPOTHESIS",
                    "detected": "Potential friction between expressed long-term career ambition and short-term convenience constraints.",
                    "why_it_matters": "Short-term optimization can inadvertently restrict future optionality.",
                    "missing_evidence_or_assumption": "Unclear whether the immediate move creates or forecloses downstream opportunities.",
                    "investigative_question": "Does this choice expand or narrow the set of viable options available in two years?"
                })

            overlooked_factors.append({
                "classification": "HYPOTHESIS",
                "detected": "Two-way door versus one-way door reversibility analysis is missing from the evaluation.",
                "why_it_matters": "Irreversible decisions require substantially higher evidentiary thresholds than easily undone experiments.",
                "missing_evidence_or_assumption": "Assumes the decision can be unwound with minimal switching cost if initial hypotheses fail.",
                "investigative_question": "What would be the total cost, time, and reputational toll to reverse this choice after 6 months?"
            })

            evidence_gaps.append({
                "classification": "OBSERVATION",
                "detected": "Key claims regarding counterpart promises or market expectations are unverified by contractual or audited data.",
                "why_it_matters": "Decisions based on informal commitments leave the decision-maker exposed if leadership or priorities shift.",
                "missing_evidence_or_assumption": "Absence of formal documentation, written commitments, or independent benchmarks.",
                "investigative_question": "Which crucial assertions in your reasoning currently rest solely on informal verbal assurances?"
            })

            questions_to_explore.extend([
                "What disconfirming evidence, if discovered tomorrow, would lead you to abandon your favored direction?",
                "What is the worst-case scenario over a 12-month horizon, and is your downside risk capped?",
                "Are you solving for the outcome with the highest upside or the path with the lowest catastrophic risk?",
                "If an objective third party reviewed your stated options, what unspoken premise would they challenge first?"
            ])

        return {
            "decision_summary": summary,
            "core_tension": tension,
            "assumptions": assumptions,
            "overlooked_factors": overlooked_factors,
            "contradictions": contradictions,
            "evidence_gaps": evidence_gaps,
            "tradeoffs": tradeoffs,
            "questions_to_explore": questions_to_explore
        }
