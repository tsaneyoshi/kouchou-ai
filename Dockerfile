FROM python:3.11-slim
WORKDIR /app

# --- デバッグステップ 1: コピー元のファイルが存在するか確認 ---
RUN echo "--- Checking existence of source files in 'sheet_updater' directory ---" && ls -l sheet_updater/

# --- ファイルコピー ---
COPY sheet_updater/requirements.txt .
COPY sheet_updater/main.py .

# --- デバッグステップ 2: コピー先のファイルが存在するか確認 ---
RUN echo "--- Checking contents of /app directory after COPY ---" && ls -l /app

# --- ライブラリインストールと実行 ---
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]