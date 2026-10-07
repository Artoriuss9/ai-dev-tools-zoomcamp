FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --system --create-home app \
    && mkdir -p /data \
    && chown app:app /data

COPY --chown=app:app backend ./backend
COPY --chown=app:app frontend ./frontend

ENV DATABASE_URL=sqlite:////data/pubg.db
USER app

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=3s --start-period=20s --retries=12 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3)"]

CMD ["python", "-m", "backend.run"]
