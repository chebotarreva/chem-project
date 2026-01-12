"""
Базовые тесты для проекта
"""

import sys
import os

# Добавляем src в путь для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_imports():
    """Тест импортов основных модулей"""
    # Проверяем, что основные модули импортируются без ошибок
    try:
        from src.api.main import app
        from src.main import substructure_search
        from src.config import settings
        assert app is not None
        print("УСПЕХ! Все модули импортируются успешно")
    except ImportError as e:
        print(f"ОШИБКА импорта: {e}")
        raise


def test_smiles_validation():
    """Тест валидации SMILES"""
    from src.main import validate_smiles

    # Корректные SMILES
    assert validate_smiles("CCO") == True  # Этанол
    assert validate_smiles("c1ccccc1") == True  # Бензол

    # Некорректные SMILES
    assert validate_smiles("XYZ") == False
    assert validate_smiles("") == False

    print("УСПЕХ! Валидация SMILES работает корректно")


def test_substructure_search_basic():
    """Базовый тест функции поиска"""
    from src.main import substructure_search

    molecules = ["CCO", "c1ccccc1", "CC(=O)O"]

    # Поиск бензольного кольца
    result = substructure_search(molecules, "c1ccccc1")
    assert "c1ccccc1" in result
    assert len(result) == 1

    print("УСПЕХ! Функция поиска работает корректно")


if __name__ == "__main__":
    test_imports()
    test_smiles_validation()
    test_substructure_search_basic()
    print("УРА! Все тесты пройдены успешно!")