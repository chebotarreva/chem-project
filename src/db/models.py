from sqlalchemy import Column, Index, Integer, String

from src.db.base import Base


class Molecule(Base):
    __tablename__ = "molecules"

    id = Column(Integer, primary_key=True, index=True)
    smiles = Column(String(1000), nullable=False)
    name = Column(String(255), nullable=True)

    # для оптимизации поиска
    __table_args__ = (Index("idx_smiles", "smiles"),)

    def __repr__(self):
        return f"<Molecule(id={self.id}, name='{self.name}', smiles='{self.smiles[:20]}...')>"
