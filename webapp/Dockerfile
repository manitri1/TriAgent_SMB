FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webapp_bff ./webapp_bff

EXPOSE 8090

CMD ["uvicorn", "webapp_bff.main:app", "--host", "0.0.0.0", "--port", "8090"]
