import requests
import time

API_URL = "http://localhost/api/molecules/"

MOLECULES = [
    {"name": "Метанол", "smiles": "CO"},
    {"name": "Формальдегид", "smiles": "C=O"},
    {"name": "Ацетон", "smiles": "CC(=O)C"},
    {"name": "Анилин", "smiles": "c1ccc(cc1)N"},
    {"name": "Фенол", "smiles": "c1ccccc1O"},
    {"name": "Толуол", "smiles": "Cc1ccccc1"},
    {"name": "Нитробензол", "smiles": "c1ccc(cc1)[N+](=O)[O-]"},
    {"name": "Бензойная кислота", "smiles": "c1ccc(cc1)C(=O)O"},
    {"name": "Салициловая кислота", "smiles": "c1ccc(c(c1)C(=O)O)O"},
    {"name": "Кофеин", "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"},
    {"name": "Никотин", "smiles": "CN1CCC[C@H]1c2cccnc2"},
    {"name": "Глюкоза", "smiles": "C(C1C(C(C(C(O1)O)O)O)O)O"},
    {"name": "Сахароза", "smiles": "C(C1C(C(C(C(O1)OC2(C(C(C(O2)CO)O)O)CO)O)O)O)O"},
    {"name": "Аскорбиновая кислота", "smiles": "C(C(C1C(=C(C(=O)O1)O)O)O)O"},
    {"name": "Лимонная кислота", "smiles": "C(C(=O)O)C(CC(=O)O)(C(=O)O)O"},
    {"name": "Морфин", "smiles": "CN1CCC23C4C1CC5=C2C(=C(C=C5)O)OC3C(C=C4)O"},
    {"name": "Пенициллин G", "smiles": "CC1(C(N2C(S1)C(C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C"},
    {"name": "Тетрациклин", "smiles": "CN(C)C1C(=O)C(C(C(C(C1(C(=O)C(=C(C2=C(C=CC=C2O)O)O)O)O)O)(C)O)O)N(C)C"},
    {"name": "DDT", "smiles": "ClC(Cl)(Cl)C(C1=CC=C(C=C1)Cl)C2=CC=C(C=C2)Cl"},
    {"name": "Бензодиазепин", "smiles": "c1ccc2c(c1)C(=NCCN2)c3ccccc3"},
]


def add_molecules():
    added = 0
    errors = 0

    for mol in MOLECULES:
        try:
            response = requests.post(API_URL, json=mol, timeout=10)
            if response.status_code == 201:
                data = response.json()
                print(f"✓ {mol['name']} (ID: {data['id']})")
                added += 1
            else:
                print(f"✗ {mol['name']}: Ошибка {response.status_code} - {response.text[:100]}")
                errors += 1

            time.sleep(0.1)  # Небольшая задержка

        except Exception as e:
            print(f"✗ {mol['name']}: {str(e)[:100]}")
            errors += 1

    print(f"\nИтог: добавлено {added}, ошибок {errors}")


if __name__ == "__main__":
    print("Добавляем молекулы в базу данных...\n")
    add_molecules()