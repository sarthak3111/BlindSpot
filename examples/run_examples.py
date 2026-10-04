"""Demonstration script running example scenarios through the BlindSpot engine."""

import json
from pathlib import Path
from blindspot.core.engine import BlindSpotEngine
from blindspot.cli.main import format_cli_output


def run():
    engine = BlindSpotEngine()
    example_dir = Path(__file__).parent
    files = list(example_dir.glob("*.json"))

    print(f"Running BlindSpot Engine across {len(files)} test dilemmas...\n")

    for file_path in files:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        print(f"\n{'#' * 75}")
        print(f"  SCENARIO: {file_path.name.upper()}")
        print(f"{'#' * 75}")

        result = engine.analyze(
            user_input=data["user_input"],
            options=data.get("options"),
            context=data.get("context")
        )

        # Print formatted output
        print(format_cli_output(result))
        
        # Verify JSON serialization matches requested schema
        as_dict = result.to_dict()
        assert "decision_summary" in as_dict
        assert "core_tension" in as_dict
        assert "assumptions" in as_dict
        assert "overlooked_factors" in as_dict
        assert "contradictions" in as_dict
        assert "evidence_gaps" in as_dict
        assert "tradeoffs" in as_dict
        assert "questions_to_explore" in as_dict
        print("  -> Schema verification passed successfully!")


if __name__ == "__main__":
    run()
