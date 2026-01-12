from typing import List, Optional
from sqlalchemy.orm import Session
from src.api.models import MoleculeCreate, MoleculeResponse
from src.db.models import Molecule


class DatabaseManager:
    """Менеджер для работы с базой данных"""

    def __init__(self, db: Session):
        self.db = db

    def create_molecule(self, molecule: MoleculeCreate) -> Molecule:
        """Создать молекулу в БД"""
        db_molecule = Molecule(
            smiles=molecule.smiles,  # molecule.smiles уже строка
            name=molecule.name if molecule.name else None  # передаем None если пусто
        )
        self.db.add(db_molecule)
        self.db.commit()
        self.db.refresh(db_molecule)
        return db_molecule

    def get_molecule_by_id(self, molecule_id: int) -> Optional[MoleculeResponse]:
        """Получить молекулу по ID"""
        db_molecule = self.db.query(Molecule).filter(Molecule.id == molecule_id).first()
        if db_molecule:
            return MoleculeResponse.model_validate(db_molecule)
        return None

    def get_all_molecules(
        self, skip: int = 0, limit: int = 10, search: Optional[str] = None
    ) -> List[MoleculeResponse]:
        """Получить все молекулы с пагинацией"""
        query = self.db.query(Molecule)

        # Если есть поисковый запрос
        if search:
            query = query.filter(
                Molecule.name.ilike(f"%{search}%")
                | Molecule.smiles.ilike(f"%{search}%")
            )

        # Пагинация
        db_molecules = query.offset(skip).limit(limit).all()

        return [MoleculeResponse.model_validate(mol) for mol in db_molecules]

    def update_molecule(
        self, molecule_id: int, molecule_update: MoleculeCreate
    ) -> Optional[MoleculeResponse]:
        """Обновить молекулу"""
        db_molecule = self.db.query(Molecule).filter(Molecule.id == molecule_id).first()

        if not db_molecule:
            return None

        # Обновляем только переданные поля
        db_molecule.smiles = molecule_update.smiles
        if molecule_update.name is not None:  # разрешаем установить пустое имя
            db_molecule.name = molecule_update.name

        self.db.commit()
        self.db.refresh(db_molecule)
        return MoleculeResponse.model_validate(db_molecule)

    def delete_molecule(self, molecule_id: int) -> bool:
        """Удалить молекулу"""
        db_molecule = self.db.query(Molecule).filter(Molecule.id == molecule_id).first()

        if not db_molecule:
            return False

        self.db.delete(db_molecule)
        self.db.commit()
        return True

    def count_molecules(self) -> int:
        """Получить общее количество молекул"""
        return self.db.query(Molecule).count()  # type: ignore

    def search_by_substructure(
        self, substructure_smiles: str
    ) -> List[MoleculeResponse]:
        """Поиск молекул по субструктуре (будем использовать позже)"""
        # Пока просто получаем все молекулы
        # В следующем шаге интегрируем RDKit
        all_molecules = self.db.query(Molecule).all()
        return [MoleculeResponse.model_validate(mol) for mol in all_molecules]
