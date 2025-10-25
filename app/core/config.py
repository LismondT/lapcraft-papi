from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Lapcraft API"
    database_url: str = "sqlite:///./app.db"
    secret_key: str = "reverse 1999 peak gacha"
    refresh_secret_key = "blue archive +wibe gacha"

    class Config:
        env_file = ".env"


settings = Settings()
