/********** Table des montants par IBAN **********/
CREATE TABLE montants_par_iban (
    iban VARCHAR(50) PRIMARY KEY,
    montant NUMERIC(15, 2) NOT NULL
);

/********** Table des montants par banque **********/
CREATE TABLE montants_par_banque (
    banque VARCHAR(50) PRIMARY KEY,
    montant NUMERIC(15, 2) NOT NULL
);

/********** Table des montants par IBAN de destination **********/
CREATE TABLE montants_par_iban_destination (
    iban VARCHAR(50) PRIMARY KEY,
    montant NUMERIC(15, 2) NOT NULL
);

/********** Table des transactions dont le montant est >= 5000 **********/
CREATE TABLE transactions_montant_eleve (
    id SERIAL PRIMARY KEY,
    datetime_tx TIMESTAMP NOT NULL,
    iban_source VARCHAR(50) NOT NULL,
    pays_source VARCHAR(50) NOT NULL,
    banque VARCHAR(50) NOT NULL,
    iban_destination VARCHAR(50) NOT NULL,
    pays_destination VARCHAR(50) NOT NULL,
    montant NUMERIC(15, 2) NOT NULL,
    UNIQUE (datetime_tx, iban_source, iban_destination)
);