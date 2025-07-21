# 創建電商網站 - Docker 部署
FROM python:3.9-slim

WORKDIR /app

# 複製依賴檔案
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY src/ ./src/
COPY config/ ./config/

# 設置環境變數
ENV PYTHONPATH=/app
ENV FLASK_APP=src/main.py

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["python", "src/main.py"]