import gspread
import os
import json
import base64
from google.oauth2.service_account import Credentials
from ..config import settings
from pathlib import Path


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
        # 環境変数からBase64エンコードされた認証情報を取得
        if os.getenv('GOOGLE_SHEETS_CREDENTIALS_BASE64'):
            credentials_base64 = os.getenv('GOOGLE_SHEETS_CREDENTIALS_BASE64')
            credentials_json = base64.b64decode(
                credentials_base64).decode('utf-8')
            credentials_info = json.loads(credentials_json)
            credentials = Credentials.from_service_account_info(
                credentials_info, scopes=scopes)
        # ローカル開発用：ファイルから読み込む
        else:
            credentials_path = Path(__file__).resolve(
            ).parent / settings.google_sheets_credentials_path
            credentials = Credentials.from_service_account_file(
                str(credentials_path), scopes=scopes)
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
        from datetime import datetime, timezone, timedelta

        recipient_sheet = self.workbook.worksheet("(当日)DMリスト")

        # JST（日本時間）で今日の日付を取得
        jst = timezone(timedelta(hours=9))
        today_jst = datetime.now(jst).date()

        # シートの日付をチェック（A2セル）
        sheet_date_str = recipient_sheet.acell('A2').value
        sheet_date = None

        if sheet_date_str:
            try:
                # 日付のパース（複数フォーマットに対応）
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d']:
                    try:
                        sheet_date = datetime.strptime(
                            str(sheet_date_str), fmt).date()
                        break
                    except ValueError:
                        continue
            except Exception as e:
                print(
                    f"Failed to parse date from sheet: {sheet_date_str}, error: {e}")

        # 日付が異なる（または無効）場合、シートをリセット
        if sheet_date != today_jst:
            print(
                f"Date mismatch detected. Sheet date: {sheet_date}, Today: {today_jst}")
            print("Resetting recipient sheet for new day...")

            # 日付を更新
            recipient_sheet.update_acell('A2', today_jst.strftime('%Y-%m-%d'))

            # B列（ユーザーリスト）をクリア（B2以降）
            range_values = recipient_sheet.col_values(2)
            if len(range_values) > 1:  # ヘッダー以外にデータがある場合
                recipient_sheet.batch_clear([f'B2:B{len(range_values)}'])

            print("Recipient sheet reset completed.")
            # 新しい日なので、このユーザーはまだコメントしていない
            return False

        # 同じ日付の場合、B列をチェック
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
