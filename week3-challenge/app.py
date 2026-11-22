from flask import Flask

from settings import load_settings


def create_app(test_config=None):
    app = Flask(__name__)

    settings = load_settings(test_config)

    app.config.update(settings)

    from routes.home import home_bp
    from routes.crops import crops_bp
    from routes.receipts import receipts_bp
    from routes.withdrawals import withdrawals_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(crops_bp)
    app.register_blueprint(receipts_bp)
    app.register_blueprint(withdrawals_bp)

    return app


app = create_app()