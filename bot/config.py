from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    database_url: str
    timezone: str = "Europe/Warsaw"
    admin_user_id: int

    # Google Sheets (необов'язково: без цих значень синхронізація просто вимкнена)
    google_credentials_path: str = ""
    google_sheet_id: str = ""
    google_sheet_tab: str = "v_tableau_daily_journal"
    # Передавати в таблицю лише дні до цієї дати включно (РРРР-ММ-ДД). Порожньо = усі дні
    google_sync_until: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()