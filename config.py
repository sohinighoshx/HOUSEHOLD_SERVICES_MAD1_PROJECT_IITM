from dotenv import load_dotenv
from os import getenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = getenv(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///household_services.sqlite3"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = getenv(
        "SECRET_KEY",
        "dev-secret-key"
    )