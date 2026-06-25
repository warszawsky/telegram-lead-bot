FROM python:3.12-slim

WORKDIR /app

# Папка для базы данных (можно примонтировать как том)
ENV DB_PATH=/data/requests.db
RUN mkdir -p /data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py db.py ./

CMD ["python", "bot.py"]
