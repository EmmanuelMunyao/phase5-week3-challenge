import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def load_settings(test_config=None) -> dict:
    """Load application settings with optional test overrides."""

    app_env = os.getenv("APP_ENV", "development").lower()

    if app_env not in {"development", "test", "production"}:
        raise RuntimeError(
            "APP_ENV must be development, test or production."
        )

    timezone = os.getenv("TIMEZONE", "Africa/Nairobi")
    app_name = os.getenv(
        "APP_NAME",
        "Ghala Moi's Bridge Warehouse",
    )

    data_file = Path(
        os.getenv("DATA_FILE", "data/ghala.json")
    )

    fee_text = os.getenv("STORAGE_FEE_KSH", "25")

    try:
        fee = int(fee_text)
    except ValueError as exc:
        raise RuntimeError(
            f"STORAGE_FEE_KSH must be whole shillings: {fee_text}."
        ) from exc

    if str(fee) != fee_text.strip():
        raise RuntimeError(
            f"STORAGE_FEE_KSH must be whole shillings: {fee_text}."
        )

    if fee < 0:
        raise RuntimeError(
            f"STORAGE_FEE_KSH must be whole shillings: {fee_text}."
        )

    secret_key = os.getenv("SECRET_KEY")

    if app_env == "production" and not secret_key:
        raise RuntimeError(
            "SECRET_KEY is required in production."
        )

    cors_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173",
    )

    origins = [
        origin.strip()
        for origin in cors_origins.split(",")
        if origin.strip()
    ]

    if "*" in origins:
        raise RuntimeError(
            "CORS_ORIGINS cannot contain *."
        )

    settings = {
        "APP_ENV": app_env,
        "APP_NAME": app_name,
        "TIMEZONE": timezone,
        "DATA_FILE": data_file,
        "STORAGE_FEE_KSH": fee,
        "SECRET_KEY": secret_key,
        "CORS_ORIGINS": origins,
    }

    # Test configuration overrides environment settings.
    if test_config:
        settings.update(test_config)

    return settings


_SETTINGS = load_settings()

APP_ENV = _SETTINGS["APP_ENV"]
APP_NAME = _SETTINGS["APP_NAME"]
TIMEZONE = _SETTINGS["TIMEZONE"]
DATA_FILE = _SETTINGS["DATA_FILE"]
STORAGE_FEE_KSH = _SETTINGS["STORAGE_FEE_KSH"]
SECRET_KEY = _SETTINGS["SECRET_KEY"]
CORS_ORIGINS = _SETTINGS["CORS_ORIGINS"]