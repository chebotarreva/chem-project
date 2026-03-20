#!/bin/bash
echo "=== 1. Создаём таблицу molecules ==="
docker compose exec postgres psql -U chem_user -d chem_database -c \
  "CREATE TABLE IF NOT EXISTS molecules (id INTEGER PRIMARY KEY, smiles VARCHAR(1000) NOT NULL, name VARCHAR(255));"

echo "=== 2. Создаём индекс ==="
docker compose exec postgres psql -U chem_user -d chem_database -c \
  "CREATE INDEX IF NOT EXISTS idx_smiles ON molecules(smiles);"

echo "=== 3. Проверяем таблицу ==="
docker compose exec postgres psql -U chem_user -d chem_database -c "\dt"

echo "=== 4. Тестируем API ==="
curl -X POST "http://localhost:8000/molecules/" \
  -H "Content-Type: application/json" \
  -d '{"id": 1, "smiles": "c1ccccc1", "name": "Бензол"}' 2>/dev/null | python -m json.tool