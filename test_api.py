import sys

sys.path.insert(0, '.')

# Тест 1: Импорты
try:
    from src.api.main import app

    print("FastAPI приложение импортировано")

    from src.api.models import MoleculeCreate

    print("Pydantic модели импортированы")

    from src.db.session import SessionLocal

    print("База данных импортирована")

    print("\nВсе импорты работают!")

except ImportError as e:
    print(f"ОШИБКА импорта: {e}")
    import traceback

    traceback.print_exc()

# Тест 2: Создание модели
print("\n--- Тест Pydantic модели ---")
try:
    mol = MoleculeCreate(id=1, smiles="c1ccccc1", name="Бензол")
    print(f"Модель создана: {mol}")
    print(f"   id: {mol.id}, smiles: {mol.smiles}")
except Exception as e:
    print(f"ОШИБКА создания модели: {e}")
