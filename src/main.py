from typing import List

from rdkit import Chem


def substructure_search(molecules: List[str], substructure: str) -> List[str]:
    """
    поиск молекул, содержащих заданную субструктуру.
    args:
        molecules: список SMILES строк (например, ["CCO", "c1ccccc1"])
        substructure: SMILES субструктуры для поиска (например, "c1ccccc1")
    returns:
        список SMILES с субструктурой
    """

    sub_mol = Chem.MolFromSmiles(substructure)
    if sub_mol is None:
        raise ValueError(f"ОШИБКА! некорректный SMILES субструктуры: {substructure}")

    results = []

    for smiles in molecules:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            print(f"пропустим некорректный SMILES: {smiles}")
            continue

        if mol.HasSubstructMatch(sub_mol):
            results.append(smiles)

    return results


def validate_smiles(smiles: str) -> bool:
    """проверка корректности SMILES строки"""
    mol = Chem.MolFromSmiles(smiles)
    return mol is not None
