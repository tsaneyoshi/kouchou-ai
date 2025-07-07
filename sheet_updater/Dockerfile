# Pythonの公式イメージをベースにする
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なライブラリをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# プログラム本体をコピー
COPY main.py .

# コンテナが起動したときに実行するコマンド
CMD ["python", "main.py"]
