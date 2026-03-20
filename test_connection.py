import os
import subprocess

print("Тестируем подключение разными способами.")

# Способ 1: Через docker compose exec из Python
print("\n1. Проверка из контейнера PostgreSQL:")
cmd1 = "docker compose exec postgres psql -U chem_user -d chem_database -c \"SELECT 'PG_OK'\""
result1 = subprocess.run(cmd1, shell=True, capture_output=True, text=True)
print(f"   Статус: {result1.returncode}, Вывод: {result1.stdout.strip()}")

# Способ 2: Через docker compose exec из бэкенда
print("\n2. Проверка из контейнера Backend:")
cmd2 = "docker compose exec backend python -c \"import psycopg2; conn=psycopg2.connect(host='postgres',user='chem_user',password='chem_password',database='chem_database'); print('BACKEND_OK')\""
result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
print(f"   Статус: {result2.returncode}, Вывод: {result2.stdout.strip()}")

# Способ 3: Проверяем переменные окружения в бэкенде
print("\n3. Переменные в Backend:")
cmd3 = "docker compose exec backend env | grep DATABASE"
result3 = subprocess.run(cmd3, shell=True, capture_output=True, text=True)
print(f"   {result3.stdout.strip()}")