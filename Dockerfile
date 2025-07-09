FROM python:3.11-slim
WORKDIR /app

# ルートからのパスを明記してファイルをコピー
COPY sheet_updater/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY sheet_updater/main.py .

# ビルド時の確認用。完成後は外してOKです
RUN ls -R /app

# ここを CMD ではなく ENTRYPOINT にして、常に /app/main.py を実行する
ENTRYPOINT ["python", "/app/main.py"]
