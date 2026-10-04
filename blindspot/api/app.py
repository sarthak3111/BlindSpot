"""Flask REST API and web server for BlindSpot analysis engine."""

from __future__ import annotations
import os
from pathlib import Path
from flask import Flask, request, jsonify, render_template

from blindspot.core.engine import BlindSpotEngine, GuardrailViolationError
from blindspot.core.models import AnalysisRequest, AnalysisResult
from blindspot.providers.factory import get_provider


def create_app(test_config=None) -> Flask:
    template_dir = Path(__file__).parent.parent / "web" / "templates"
    static_dir = Path(__file__).parent.parent / "web" / "static"

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir) if static_dir.exists() else None
    )

    if test_config:
        app.config.update(test_config)

    engine = BlindSpotEngine()

    @app.route("/api/health", methods=["GET"])
    def health():
        active_provider = engine.provider.provider_name
        return jsonify({
            "status": "healthy",
            "service": "blindspot-analysis-engine",
            "active_provider": active_provider,
            "version": "0.1.0"
        })

    @app.route("/api/schema", methods=["GET"])
    def get_schema():
        return jsonify(AnalysisResult.model_json_schema())

    @app.route("/api/analyze", methods=["POST"])
    def analyze():
        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Invalid JSON body provided."}), 400

        # 1. Validate user_input
        user_input = data.get("user_input")
        if user_input is None:
            return jsonify({"error": "'user_input' field is required."}), 400
        if not isinstance(user_input, str):
            return jsonify({"error": "'user_input' must be a string."}), 400
        user_input = user_input.strip()
        if not user_input:
            return jsonify({"error": "'user_input' cannot be empty."}), 400
        if len(user_input) > 50000:
            return jsonify({"error": "Input exceeds maximum allowed size of 50,000 characters."}), 400

        # 2. Validate options
        options = data.get("options")
        if options is not None:
            if not isinstance(options, list):
                return jsonify({"error": "'options' must be a list of strings."}), 400
            if len(options) > 20:
                return jsonify({"error": "A maximum of 20 options is supported."}), 400
            options = [str(opt).strip()[:500] for opt in options if opt and str(opt).strip()]

        # 3. Validate context
        context = data.get("context")
        if context is not None:
            if not isinstance(context, str):
                return jsonify({"error": "'context' must be a string."}), 400
            context = context.strip()[:10000]

        # 4. Validate temperature
        raw_temp = data.get("temperature", 0.2)
        try:
            temperature = float(raw_temp)
            temperature = max(0.0, min(1.0, temperature))
        except (ValueError, TypeError):
            temperature = 0.2

        strict = bool(data.get("strict_guardrails", True))
        provider_name = data.get("provider")
        model = data.get("model")

        # 5. Check provider resolution
        call_provider = None
        if provider_name:
            if not isinstance(provider_name, str):
                return jsonify({"error": "'provider' must be a string."}), 400
            try:
                call_provider = get_provider(provider_name=provider_name.strip(), model=model)
            except Exception as e:
                return jsonify({"error": f"Failed to instantiate provider '{provider_name}': {str(e)}"}), 400

        try:
            result = engine.analyze(
                user_input=user_input,
                options=options,
                context=context,
                provider=call_provider,
                temperature=temperature,
                strict=strict
            )
            response_dict = result.to_dict()
            response_dict["metadata"] = result.metadata
            return jsonify(response_dict), 200

        except GuardrailViolationError as gve:
            return jsonify({
                "error": "Guardrail violation: output violates BlindSpot constraints",
                "details": str(gve),
                "violations": [v.model_dump() for v in gve.report.violations]
            }), 422
        except Exception as e:
            app.logger.error("Analysis engine execution error: %s", e, exc_info=True)
            return jsonify({"error": "Analysis failed due to an internal engine error. Please check reasoning input and try again."}), 500

    @app.route("/favicon.ico", methods=["GET"])
    def favicon():
        return ("", 204)

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1")
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
