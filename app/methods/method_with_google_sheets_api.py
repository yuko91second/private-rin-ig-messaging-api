import gspread
import json
import os
from google.oauth2.service_account import Credentials
from ..config import settings
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

class SheetsMethods:
    def __init__(self):
        self.spread_sheet_key = settings.google_sheets_spread_sheet_key
        self.client = self._authorize()
        self.workbook = self._get_workbook()

    def _authorize(self):
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # デバッグ情報を出力
        print(f"[DEBUG] GOOGLE_SHEETS_CREDENTIALS_JSON exists: {os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON') is not None}")
        print(f"[DEBUG] GOOGLE_SHEETS_CREDENTIALS_PATH from settings: {settings.google_sheets_credentials_path}")
        
        # 環境変数から直接JSON文字列を取得する方法
        if os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON'):
            try:
                print("[DEBUG] Trying to load credentials from GOOGLE_SHEETS_CREDENTIALS_JSON environment variable")
                credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS_JSON')
                print(f"[DEBUG] JSON length: {len(credentials_json) if credentials_json else 0}")
                credentials_info = json.loads(credentials_json)
                print(f"[DEBUG] Parsed JSON keys: {list(credentials_info.keys()) if credentials_info else 'None'}")
                
                # private_keyの改行文字を確認
                if 'private_key' in credentials_info:
                    pk = credentials_info['private_key']
                    print(f"[DEBUG] Private key starts with: {pk[:50] if pk else 'None'}")
                    print(f"[DEBUG] Private key ends with: {pk[-50:] if pk else 'None'}")
                    # バックスラッシュを含む文字列はf-string外で処理
                    newline_check = '\n' in pk
                    escaped_newline_check = '\\n' in pk
                    print(f"[DEBUG] Private key contains newline: {newline_check}")
                    print(f"[DEBUG] Private key contains escaped newline: {escaped_newline_check}")
                    print(f"[DEBUG] Private key length: {len(pk) if pk else 0}")
                    # 改行文字を修正する試み
                    if escaped_newline_check:
                        print("[DEBUG] Found escaped newlines, replacing...")
                        credentials_info['private_key'] = pk.replace('\\n', '\n')
                credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)
                print("[DEBUG] Successfully created credentials from environment variable")
            except json.JSONDecodeError as e:
                print(f"[DEBUG] JSON decode error: {e}")
                raise ValueError(f"Invalid JSON in GOOGLE_SHEETS_CREDENTIALS_JSON environment variable: {e}")
            except Exception as e:
                print(f"[DEBUG] Unexpected error: {e}")
                raise
        # ローカル開発用：ファイルパスから読み込む
        elif settings.google_sheets_credentials_path and settings.google_sheets_credentials_path != 'default_value':
            print("[DEBUG] Trying to load credentials from file path")
            credentials_path = Path(__file__).resolve().parent / settings.google_sheets_credentials_path
            if not credentials_path.exists():
                credentials_path = Path(settings.google_sheets_credentials_path).resolve()
            print(f"[DEBUG] Credentials path: {credentials_path}")
            print(f"[DEBUG] File exists: {credentials_path.exists()}")
            credentials = Credentials.from_service_account_file(str(credentials_path), scopes=scopes)
            print("[DEBUG] Successfully created credentials from file")
        else:
            print("[DEBUG] No credentials provided!")
            print(f"[DEBUG] Environment variables: {list(os.environ.keys())}")
            raise ValueError("No Google Sheets credentials provided")

        return gspread.authorize(credentials)

    def _get_workbook(self):
        workbook = self.client.open_by_key(self.spread_sheet_key)
        return workbook

    def get_today_str(self):
        recipient_sheet = self.workbook.worksheet("(当日)DMリスト")
        # A2セルの値を取得
        recipient_today_str = recipient_sheet.acell('A2').value
        response_sheet = self.workbook.worksheet("(当日)レスポンス")
        response_today_str = response_sheet.acell('A2').value
        return recipient_today_str, response_today_str

    def whether_already_made_a_comment(self, username: str) -> bool:
        recipient_sheet = self.workbook.worksheet("(当日)DMリスト")
        # B列の値を取得
        range_values = recipient_sheet.col_values(2)
        if username in range_values:
            return True
        return False

    def get_response_rows_list_per_zodiac_sign(self) -> list:
        recipient_sheet = self.workbook.worksheet("(当日)レスポンス")
        range_values = recipient_sheet.get('B2:O13')
        row_arrays = [row for row in range_values]
        return row_arrays

    def get_fixed_form_sentences(self):
        fixed_form_sheet = self.workbook.worksheet("定型文")
        range_values = fixed_form_sheet.get('A2:C5')
        fixed_form_sentences_list = [row for row in range_values]
        return fixed_form_sentences_list

    def insert_username_on_recipient_sheet(self, username: str):
        recipient_sheet = self.workbook.worksheet("(当日)DMリスト")
        # B列の最終行にusernameを追加
        b_col_values = recipient_sheet.col_values(2)  # B列は2番目の列
        last_row_index = len(b_col_values) + 1
        recipient_sheet.update_cell(last_row_index, 2, username)
