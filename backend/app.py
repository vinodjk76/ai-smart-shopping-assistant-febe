"""Flask application factory and entry point."""
import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from api_utils import ApiError, error_response
from config import Config
from extensions import cors, db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    logging.basicConfig(
        level=getattr(logging, str(app.config.get("LOG_LEVEL", "INFO")).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # Keep SDK/HTTP libraries from logging request details (may include keys)
    for noisy in ("httpx", "httpcore", "google_genai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from routes import cart, chat, comparisons, products, recommendations, reviews, wishlist

    for module in (products, recommendations, comparisons, reviews, cart, wishlist, chat):
        app.register_blueprint(module.bp)

    @app.get("/api/health")
    def health():
        from models import Product

        try:
            count = Product.query.count()
            db_status = "ok"
        except Exception:  # noqa: BLE001
            count, db_status = 0, "error"
        from services.gemini_service import is_configured

        return jsonify({
            "status": "ok" if db_status == "ok" else "degraded",
            "database": db_status,
            "products": count,
            "gemini_configured": is_configured(),  # boolean only; key never exposed
            "data_notice": "Seeded data is demo/sample data.",
        })

    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return error_response(err.message, err.status, err.code, err.details)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        codes = {404: "not_found", 405: "method_not_allowed",
                 413: "payload_too_large", 415: "unsupported_media_type"}
        return error_response(err.description or err.name, err.code or 500,
                              codes.get(err.code, "http_error"))

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("Unhandled error: %s", type(err).__name__)
        db.session.rollback()
        return error_response("Internal server error", 500, "internal_error")

    with app.app_context():
        import models  # noqa: F401  (register models)

        db.create_all()

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="127.0.0.1", port=5000, debug=False)
