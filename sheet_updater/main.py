import traceback
import gspread
from google.oauth2.service_account import Credentials
import os

# --- 設定項目 ---
# サービスアカウントの秘密鍵ファイルへのパス
# ローカルでテストする際はファイル名を直接指定
# Cloud Runで動かす際は、環境変数からパスを取得（後述）
KEY_FILE_PATH = os.environ.get('GCP_SECRET_PATH', 'service_account.json')

# あなたのスプレッドシートのURL
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1c7-0miNTxdx-XqDPR99unHbxzoxQmiyyrHMIKVoqoXk/" 

# アクセス許可の範囲（スコープ）
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]
# ----------------

def main():
    print("Processing started.")
    try:
        # 秘密の鍵を使って認証
        creds = Credentials.from_service_account_file(KEY_FILE_PATH, scopes=SCOPES)
        client = gspread.authorize(creds)

        # スプレッドシートをURLで開く
        spreadsheet = client.open_by_url(SPREADSHEET_URL)
        worksheet = spreadsheet.worksheet("回答一覧") # 操作したいシート名
        print("Successfully authenticated and opened the sheet.")

        # C列（判定列）の全データを取得
        judgement_column = worksheet.col_values(3) # C列は3番目

        # C列が「2」の行を処理
        for i, value in enumerate(judgement_column, 1):
            if value == '2':
                print(f"Found '2' at row {i}. Processing...")
                # --- ここに本来のAI判定ロジックを入れる ---
                # 今回はテストとして、単純に「1」に書き換える
                ai_judgement = 1
                worksheet.update_cell(i, 3, ai_judgement)
                print(f"Row {i} updated to '{ai_judgement}'.")

        print("Processing finished successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("--- Full Traceback ---")
        traceback.print_exc() # これがエラーの詳細を出力します

if __name__ == "__main__":
    main()
