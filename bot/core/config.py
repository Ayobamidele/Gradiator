from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent


class Settings:
    """Class to hold application's config values."""
    APP_NAME: str = config("APP_NAME", default="The Bouncer Bot")
    APP_VERSION: str = config("APP_VERSION", default="0.1.0")
    APP_DESCRIPTION: str = config(
        "APP_DESCRIPTION", default="Remove/Add users from channels")

    SLACK_BOT_TOKEN = config("SLACK_BOT_TOKEN", "")
    SLACK_SIGNING_SECRET = config("SLACK_SIGNING_SECRET", "")
    SLACK_USER_TOKEN = config("SLACK_USER_TOKEN", "")

    DB_USER: str = config("DB_USER", default="postgres")
    DB_PASSWORD: str = config("DB_PASSWORD", default="password")
    DB_HOST: str = config("DB_HOST", default="localhost")
    DB_PORT: str = config("DB_PORT", default="5432")
    DB_NAME: str = config("DB_NAME", default="bouncer")

    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
