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
KEY_FILE_PATH = 'service_account.json'
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
    default_response = ("2", "AI判定エラー") # エラー時のデフォルト値

    if not gemini_model:
        print("Geminiモデルが利用できないため、判定をスキップします。")
        return default_response

    try:
        cleaned_prompt_template = prompt_template 
        
        print(f"--- Preparing prompt from template (first 50 chars): '{cleaned_prompt_template[:50]}...' and comment '{comment[:30]}...' ---")

        prompt = cleaned_prompt_template.format(comment=comment) 
        
        print(f"--- Final Prompt to AI ---") 
        print(prompt)
        print(f"--- End Final Prompt ---")

        response = gemini_model.generate_content(prompt)
        
        print(f"--- Gemini AI Raw Response ---")
        print(response.text)
        print(f"--- End Raw Response ---")

        json_text = response.text.strip()
        if json_text.startswith("```json") and json_text.endswith("```"):
            json_text = json_text[len("```json"): -len("```")].strip()
        elif json_text.startswith("```") and json_text.endswith("```"):
            json_text = json_text[len("```"): -len("```")].strip()
        
        print(f"--- Extracted JSON Text ---")
        print(json_text)
        print(f"--- End Extracted JSON Text ---")

        data = json.loads(json_text)
        
        print(f"--- Parsed JSON Data ---")
        print(data)
        print(f"--- End Parsed JSON Data ---")
        
        judgement = str(data.get("judgement", "2"))
        reason = data.get("reason", "理由解析エラー")

        if judgement not in ["0", "1"]:
            print(f"AI判定結果が0または1ではありませんでした: {judgement} (元の値: {data.get('judgement')})")
            return default_response
            
        return (judgement, reason)

    except json.JSONDecodeError as e: 
        print(f"AIからの応答が有効なJSON形式ではありませんでした: {e}")
        print(f"問題の応答テキスト:\n{response.text}") 
        return default_response
    except Exception as e:
        print(f"AI判定中に予期せぬエラーが発生しました: {e}")
        traceback.print_exc() 
        return default_response

def main():
    print("Processing started.")
    try:
        creds = Credentials.from_service_account_file(KEY_FILE_PATH, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(SPREADSHEET_URL)
        
        prompt_worksheet = spreadsheet.worksheet(PROMPT_SHEET_NAME)
        source_worksheet = spreadsheet.worksheet(SOURCE_SHEET_NAME)
        print("Successfully authenticated and opened the sheets.")
        
        raw_prompt_template = prompt_worksheet.acell('A1').value
        
        if raw_prompt_template is None:
            print("「AI指示」シートのA1セルが空です。")
            return

        prompt_template = raw_prompt_template.strip() 

        if "{comment}" not in prompt_template:
            print("「AI指示」シートのA1に、'{comment}' を含む有効なプロンプトがありません。")
            return

        print(f"--- Processed Prompt Template (from A1 cell) ---")
        print(f"'{prompt_template}'") 
        print(f"--- End Processed Prompt Template ---")

        all_rows = source_worksheet.get_all_values()
        
        # --- ここから修正点 ---
        # 処理された行があるかを示すフラグ
        rows_processed = False 

        for i, row in enumerate(all_rows, 1):
            if i == 1: continue 

            if len(row) >= 3 and row[2] == '2':
                comment = row[1] 
                print(f"Found '2' at row {i}. Processing comment: '{comment[:50]}...'") 
                
                ai_judgement, ai_reason = get_ai_judgement(prompt_template, comment)
                
                source_worksheet.update_cell(i, 3, ai_judgement) 
                source_worksheet.update_cell(i, 4, ai_reason)    
                print(f"Row {i} updated to '{ai_judgement}' with reason: '{ai_reason}'")
                rows_processed = True # 行が処理されたことを記録
        
        # もし一つも行が処理されなかった場合、メッセージを表示
        if not rows_processed:
            print("INFO:AI判定はスキップされました。")
        # --- 修正ここまで ---

        print("Processing finished successfully.")

    except Exception as e:
        print(f"An unexpected error occurred in main execution:")
        print("--- Full Traceback ---")
        traceback.print_exc()

if __name__ == "__main__":
    main()