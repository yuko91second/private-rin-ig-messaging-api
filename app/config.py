from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    facebook_page_id: str = '128170000177681'
    facebook_page_access_token: str = 'EAAM4sCOqR98BPW7rD2uWU316HR4jX9YTj11CKBh7nH3ZAIFet8imJZATQAU2IKiM5s6qKTuZAbuLeSt6PXiO7jJjESCr8t3iDvKFn5kEtyKC9fld3fkZC9MrSKLTQDwVdDCSgPLjl2Em3JLtSUGE5hdMFwZAaE6g334SeCX8xCX3wAGzTneJSsxKJgguwkgGb7IC11Lh78NCwToFSACyWpkYZD'
    facebook_verify_token: str = 'rin080902'
    google_sheets_credentials_path: Optional[str] = 'rin-hp-crud-01-66c3505ccd9c.json'
    google_sheets_credentials_json: Optional[str] = None  # Render.comで使用
    google_sheets_spread_sheet_key: str = '1iaK0si5CniF3jaitvroSm0RAirM3jOLNZQDo7HU9aK0'

    class Config:
        env_file = '.env'

settings = Settings()
