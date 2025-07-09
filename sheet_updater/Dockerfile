FROM python:3.11-slim
WORKDIR /app

# コピー元のパスを修正
COPY sheet_updater/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# コピー元のパスを修正
COPY sheet_updater/main.py .

CMD ["python", "main.py"]