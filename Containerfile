FROM python:3.14-slim
WORKDIR /app
COPY run.py ./
COPY src/ ./src/
COPY static/ ./static/
COPY data/ ./data/
ENV HOST=0.0.0.0 PORT=8000 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 65534:65534
EXPOSE 8000
CMD ["python", "run.py"]
