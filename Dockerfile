FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m playwright install chromium

COPY . .

ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]