FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mock_pos ./mock_pos

EXPOSE 8080

CMD ["uvicorn", "mock_pos.main:app", "--host", "0.0.0.0", "--port", "8080"]
