FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY . /app

EXPOSE 8000 8501

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
