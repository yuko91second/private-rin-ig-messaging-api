import time
import datetime
import gspread
from google.oauth2.service_account import Credentials
from ..config import settings
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

class SheetsMethods:
    def __init__(self):
        # * 環境設定から取得した相対パスを絶対パスに変換
        credentials_path = Path(__file__).resolve(
        ).parent / settings.google_sheets_credentials_path
        # * 読み込みエラーを避けるために絶対パスを使用
        self.credentials_file = str(credentials_path)

        self.spread_sheet_key = settings.google_sheets_spread_sheet_key
        self.client = self._authorize()
        self.workbook = self._get_workbook()

    def _authorize(self):
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = Credentials.from_service_account_file(
            self.credentials_file, scopes=scopes)
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
