FROM python:3.11-slim
WORKDIR /app

# ルートからのパスを明記してファイルをコピー
COPY sheet_updater/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY sheet_updater/main.py .

# この行を追加して、/appフォルダの中身をすべて表示させる
RUN ls -R /app

CMD ["python", "main.py"]