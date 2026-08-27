FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/service/sign_service/requirements.txt /app/requirements.txt
COPY Models /app/models
COPY Preprocessing /app/preprocessing
COPY Data /app/data
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/service/sign_service /app/sign_service

WORKDIR /app/sign_service

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]