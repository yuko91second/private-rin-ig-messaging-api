#!/usr/bin/env python3
"""
Google Sheetsアクセステストスクリプト
"""
import json
import sys
from pathlib import Path

# 必要なライブラリをインポート
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("必要なライブラリがインストールされていません。")
    print("pip install gspread google-auth")
    sys.exit(1)

def test_sheets_access():
    """Google Sheetsへのアクセスをテスト"""

    # 設定
    CREDENTIALS_PATH = "app/methods/rin-hp-crud-01-2a1820940bdb.json"
    SPREADSHEET_KEY = "1iaK0si5CniF3jaitvroSm0RAirM3jOLNZQDo7HU9aK0"

    print("=" * 50)
    print("Google Sheets アクセステスト開始")
    print("=" * 50)

    # 1. 認証ファイルの存在確認
    print("\n[1] 認証ファイルの確認...")
    cred_path = Path(CREDENTIALS_PATH)
    if not cred_path.exists():
        print(f"❌ 認証ファイルが見つかりません: {CREDENTIALS_PATH}")
        return False
    print(f"✅ 認証ファイルが存在します: {CREDENTIALS_PATH}")

    # 2. JSONファイルの内容確認
    print("\n[2] JSONファイルの内容確認...")
    try:
        with open(CREDENTIALS_PATH, 'r') as f:
            cred_data = json.load(f)
        print(f"✅ JSONファイルは有効です")
        print(f"   - project_id: {cred_data.get('project_id')}")
        print(f"   - client_email: {cred_data.get('client_email')}")
        print(f"   - private_key_id: {cred_data.get('private_key_id')[:20]}...")
    except json.JSONDecodeError as e:
        print(f"❌ JSONファイルが無効です: {e}")
        return False

    # 3. 認証処理
    print("\n[3] Google認証処理...")
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH,
            scopes=scopes
        )
        print("✅ 認証情報の作成に成功")
    except Exception as e:
        print(f"❌ 認証情報の作成に失敗: {e}")
        return False

    # 4. gspread認証
    print("\n[4] gspread認証...")
    try:
        client = gspread.authorize(credentials)
        print("✅ gspread認証に成功")
    except Exception as e:
        print(f"❌ gspread認証に失敗: {e}")
        return False

    # 5. スプレッドシートを開く
    print("\n[5] スプレッドシートへのアクセス...")
    print(f"   スプレッドシートID: {SPREADSHEET_KEY}")
    try:
        workbook = client.open_by_key(SPREADSHEET_KEY)
        print(f"✅ スプレッドシートを開きました")
        print(f"   - タイトル: {workbook.title}")
        print(f"   - URL: {workbook.url}")
    except Exception as e:
        print(f"❌ スプレッドシートを開けません: {e}")
        print("\n考えられる原因:")
        print("1. スプレッドシートIDが間違っている")
        print("2. サービスアカウントに共有されていない")
        print(f"3. 共有設定を確認: {cred_data.get('client_email')}")
        return False

    # 6. ワークシートの一覧を取得
    print("\n[6] ワークシート一覧の取得...")
    try:
        worksheets = workbook.worksheets()
        print(f"✅ ワークシート一覧を取得しました（{len(worksheets)}個）")
        for ws in worksheets[:5]:  # 最初の5個だけ表示
            print(f"   - {ws.title}")
        if len(worksheets) > 5:
            print(f"   ... 他{len(worksheets) - 5}個")
    except Exception as e:
        print(f"❌ ワークシート一覧の取得に失敗: {e}")
        return False

    # 7. テスト読み込み
    print("\n[7] データ読み込みテスト...")
    try:
        # (当日)DMリストシートの存在確認
        test_sheet = workbook.worksheet("(当日)DMリスト")
        print(f"✅ '(当日)DMリスト' シートにアクセス成功")

        # A2セルの値を取得
        test_value = test_sheet.acell('A2').value
        print(f"   - A2セルの値: {test_value}")

    except Exception as e:
        print(f"⚠️  '(当日)DMリスト' シートが見つからないか、読み込みエラー: {e}")
        # 最初のシートで代替テスト
        try:
            first_sheet = worksheets[0]
            print(f"   代替: '{first_sheet.title}' シートでテスト")
            test_value = first_sheet.acell('A1').value
            print(f"   - A1セルの値: {test_value}")
        except Exception as e2:
            print(f"❌ データ読み込みに失敗: {e2}")
            return False

    print("\n" + "=" * 50)
    print("🎉 すべてのテストが成功しました！")
    print("Google Sheets APIは正常に動作しています。")
    print("=" * 50)
    return True

if __name__ == "__main__":
    try:
        success = test_sheets_access()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nテストを中断しました。")
        sys.exit(1)
    except Exception as e:
        print(f"\n予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
