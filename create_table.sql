-- create_table.sql
DROP TABLE IF EXISTS molecules;
CREATE TABLE molecules (
    id INTEGER PRIMARY KEY,
    smiles VARCHAR(1000) NOT NULL,
    name VARCHAR(255)
);
CREATE INDEX idx_smiles ON molecules(smiles);