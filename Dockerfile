FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для RDKit
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    build-essential \
    cmake \
    libboost-all-dev \
    libeigen3-dev \
    libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка RDKit
RUN pip install rdkit-pypi

# Копирование кода
COPY . .

# Создание директории для alembic
RUN mkdir -p alembic/versions

CMD ["sh", "-c", "sleep 2 && alembic upgrade head && uvicorn src.api.main:app --host 0.0.0.0 --port 8000"]