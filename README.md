# Chemical Molecules API

![CI/CD Status](https://github.com/chebotarreva/chem-project/actions/workflows/ci-cd.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

API для хранения и поиска химических молекул с использованием RDKit, FastAPI, PostgreSQL, Redis, Docker, и Celery.

Запуск проекта:

```bash
# Клонирование репозитория
git clone https://github.com/chebotarreva/chem-project.git
cd chem-project

# Запуск с Docker Compose
docker-compose up -d

# Приложение будет доступно по адресу:
# - API: http://localhost
# - Документация: http://localhost/docs
# - Мониторинг задач: http://localhost:5555
