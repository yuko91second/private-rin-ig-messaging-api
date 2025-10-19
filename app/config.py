from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Facebook関連の設定
    facebook_page_id: str
    facebook_page_access_token: str
    facebook_verify_token: str
    facebook_api_latest_version: str = 'v24.0'

    # Google Sheets関連の設定
    google_sheets_credentials_path: str = 'rin-hp-crud-01-2a1820940bdb.json'  # ローカル開発用のデフォルト値
    google_sheets_spread_sheet_key: str

    class Config:
        env_file = '.env'


settings = Settings()
