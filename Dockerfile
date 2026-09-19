FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
COPY pyproject.toml README.md ./
COPY src ./src
COPY web ./web
RUN pip install --no-cache-dir .
EXPOSE 8080
CMD ["sh", "-c", "uvicorn lekh_signal.api:app --host 0.0.0.0 --port ${PORT}"]
