import traceback
import gspread
from google.oauth2.service_account import Credentials
import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

# .envファイルから環境変数を読み込む
load_dotenv()

# --- 設定項目 ---
# 環境変数が設定されていなければservice_account.jsonをデフォルトで使う
KEY_FILE_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")
# ファイルの存在チェック
if not os.path.exists(KEY_FILE_PATH):
    raise FileNotFoundError(f"認証ファイルが見つかりません: {KEY_FILE_PATH}")

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1c7-0miNTxdx-XqDPR99unHbxzoxQmiyyrHMIKVoqoXk/"
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]
SOURCE_SHEET_NAME = "回答一覧"
PROMPT_SHEET_NAME = "AI指示"
# ----------------

# Gemini AIモデルを初期化
try:
    gemini_api_key = os.environ.get('GOOGLE_AI_API_KEY')
    if not gemini_api_key:
        raise ValueError("APIキーが環境変数に設定されていません。.envファイルを確認してください。")
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Geminiの初期化中にエラーが発生しました: {e}")
    gemini_model = None

def get_ai_judgement(prompt_template, comment):
    """AIに判定を依頼し、判定と理由を返す関数"""
    default_response = ("2", "AI判定エラー")

    if not gemini_model:
        print("Geminiモデルが利用できないため、判定をスキップします。")
        return default_response

    try:
        print(f"--- Preparing prompt (first 50 chars): '{prompt_template[:50]}...' comment '{comment[:30]}...' ---")
        prompt = prompt_template.format(comment=comment)
        print(f"--- Final Prompt ---\n{prompt}\n--- End Prompt ---")

        response = gemini_model.generate_content(prompt)
        print(f"--- Raw Response ---\n{response.text}\n--- End Raw ---")

        # JSON 部分だけ抽出
        json_text = response.text.strip()
        if json_text.startswith("```json") and json_text.endswith("```"):
            json_text = json_text[len("```json"): -len("```")].strip()
        elif json_text.startswith("```") and json_text.endswith("```"):
            json_text = json_text[len("```"): -len("```")].strip()

        print(f"--- Extracted JSON ---\n{json_text}\n--- End Extracted ---")
        data = json.loads(json_text)
        print(f"--- Parsed JSON ---\n{data}\n--- End Parsed ---")

        judgement = str(data.get("judgement", "2"))
        reason = data.get("reason", "理由解析エラー")
        if judgement not in ["0", "1"]:
            print(f"AI判定結果が0または1ではありません: {judgement}")
            return default_response
        return (judgement, reason)

    except json.JSONDecodeError as e:
        print(f"JSON 解析エラー: {e}\nResponse:\n{response.text}")
        return default_response
    except Exception as e:
        print(f"AI判定中にエラー: {e}")
        traceback.print_exc()
        return default_response

def main():
    print("Processing started.")
    try:
        creds = Credentials.from_service_account_file(KEY_FILE_PATH, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(SPREADSHEET_URL)
        print("Successfully authenticated and opened the sheets.")

        prompt_worksheet = spreadsheet.worksheet(PROMPT_SHEET_NAME)
        source_worksheet = spreadsheet.worksheet(SOURCE_SHEET_NAME)
        raw_prompt_template = prompt_worksheet.acell('A1').value
        if raw_prompt_template is None:
            print("「AI指示」シートのA1セルが空です。")
            return
        prompt_template = raw_prompt_template.strip()
        if "{comment}" not in prompt_template:
            print("プロンプトに '{comment}' が含まれていません。")
            return

        all_rows = source_worksheet.get_all_values()
        rows_processed = False
        for i, row in enumerate(all_rows, 1):
            if i == 1:
                continue
            if len(row) >= 3 and row[2] == '2':
                comment = row[1]
                print(f"Processing row {i}: '{comment[:50]}...'")
                ai_judgement, ai_reason = get_ai_judgement(prompt_template, comment)
                source_worksheet.update_cell(i, 3, ai_judgement)
                source_worksheet.update_cell(i, 4, ai_reason)
                print(f"Row {i} updated: {ai_judgement}, reason: {ai_reason}")
                rows_processed = True
        if not rows_processed:
            print("INFO: AI判定はスキップされました。")
        print("Processing finished successfully.")

    except Exception:
        print("An unexpected error occurred in main execution:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
    # 2025/07/09 テスト実行
