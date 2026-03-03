from typing import List

from rdkit import Chem


def substructure_search(molecules: List[str], substructure: str) -> List[str]:
    """
    Поиск молекул, содержащих заданную субструктуру.
    Args:
        molecules: список SMILES строк (например, ["CCO", "c1ccccc1"])
        substructure: SMILES субструктуры для поиска (например, "c1ccccc1")
    Returns:
        список SMILES, содержащих субструктуру
    """

    # 1. прасинг субструктуры 
    sub_mol = Chem.MolFromSmiles(substructure)
    if sub_mol is None:
        raise ValueError(f"Некорректный SMILES субструктуры: {substructure}")

    results = []

    # 2. проверка каждой молекулы
    for smiles in molecules:
        # создадим объект молекулы
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            print(f"Пропустим некорректный SMILES: {smiles}")
            continue

        # 3. проверка наличия субструктуры
        if mol.HasSubstructMatch(sub_mol):
            results.append(smiles)

    return results


def validate_smiles(smiles: str) -> bool:
    """Проверка корректности SMILES строки"""
    mol = Chem.MolFromSmiles(smiles)
    return mol is not None
