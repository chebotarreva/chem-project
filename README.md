# Chemical Molecules API

![CI/CD Status](https://github.com/chebotarreva/chem-project/actions/workflows/ci-cd.yml/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

Это API для хранения и поиска химических соединений с использованием RDKit, FastAPI, PostgreSQL, Redis, Docker и Celery.

Как запустить проект?

```bash
# клонировать репозиторий:
git clone https://github.com/chebotarreva/chem-project.git
cd chem-project

# запустить всё с Docker:
docker-compose up -d

# веб-приложение будет доступно по адресу:
# http://localhost

# может пригодиться:
# - Документация: http://localhost/docs
# - Мониторинг задач: http://localhost:5555
