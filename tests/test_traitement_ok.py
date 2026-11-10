import datetime
import os
from collections import namedtuple

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


MontantParIban = namedtuple("MontantParIban", ["iban", "montant"])
MontantParBanque = namedtuple("MontantParBanque", ["banque", "montant"])
MontantParIbanDestination = namedtuple("MontantParIbanDestination", ["iban", "montant"])
TransactionMontantEleve = namedtuple(
    "TransactionMontantEleve",
    [
        "datetime_tx",
        "iban_source",
        "pays_source",
        "banque",
        "iban_destination",
        "pays_destination",
        "montant",
    ],
)

@pytest.fixture
def get_data_from_bdd():
    print("Connecting to the database...")
    engine = create_engine(os.environ["DATABASE_URL"])

    with engine.connect() as connection:
        # partie montant par IBAN
        result = connection.execute(text("SELECT iban, montant FROM montants_par_iban ORDER BY iban"))
        montants_par_iban = [
            MontantParIban(iban=iban, montant=float(montant))
            for iban, montant in result.fetchall()
        ]

        # partie montant par banque
        result = connection.execute(
            text("SELECT banque, montant FROM montants_par_banque ORDER BY banque")
        )
        montants_par_banque = [
            MontantParBanque(banque=banque, montant=float(montant))
            for banque, montant in result.fetchall()
        ]

        # partie montant par IBAN de destination
        result = connection.execute(
            text("SELECT iban, montant FROM montants_par_iban_destination ORDER BY iban")
        )
        montants_par_iban_destination = [
            MontantParIbanDestination(iban=iban, montant=float(montant))
            for iban, montant in result.fetchall()
        ]

        # partie transactions >= 5000
        result = connection.execute(
            text(
                "SELECT datetime_tx, iban_source, pays_source, banque, "
                "iban_destination, pays_destination, montant "
                "FROM transactions_montant_eleve ORDER BY datetime_tx"
            )
        )
        transactions_montant_eleve = []
        for row in result.fetchall():
            data = [*row]
            data[-1] = float(data[-1]) # avant dernier : montant, on met en float
            transactions_montant_eleve.append(TransactionMontantEleve(*data))

    return (
        montants_par_iban,
        montants_par_banque,
        montants_par_iban_destination,
        transactions_montant_eleve,
    )


@pytest.fixture
def data_expected():
    # valeurs attendues pour les données générées avec SEED = 2026 (voir generation_data.py)
    # ces données sont triées par IBAN, banque et datetime_tx pour que cela corresponde aux données de la BDD
    montants_par_iban = [
        MontantParIban(iban="DE89370400440532013000", montant=1213.29),
        MontantParIban(iban="ES9121000418450200051332", montant=11132.69),
        MontantParIban(iban="FR7613306000015678901234567", montant=10349.75),
        MontantParIban(iban="FR7630003000409876543210925", montant=6987.72),
        MontantParIban(iban="FR7630006000011234567890189", montant=814.95),
        MontantParIban(iban="GB29NWBK60161331926819", montant=2995.95),
    ]

    montants_par_banque = [
        MontantParBanque(banque="CaixaBank", montant=11132.69),
        MontantParBanque(banque="Crédit agricole", montant=10349.75),
        MontantParBanque(banque="Deutsche Bank", montant=1213.29),
        MontantParBanque(banque="NatWest", montant=2995.95),
        MontantParBanque(banque="Société Générale", montant=7802.67),
    ]

    montants_par_iban_destination = [
        MontantParIbanDestination(iban="DE89370400440532013000", montant=9520.14),
        MontantParIbanDestination(iban="ES9121000418450200051332", montant=2656.46),
        MontantParIbanDestination(iban="FR7613306000015678901234567", montant=1708.61),
        MontantParIbanDestination(iban="FR7630006000011234567890189", montant=1197.44),
        MontantParIbanDestination(iban="GB29NWBK60161331926819", montant=18411.7),
    ]

    transactions_montant_eleve = [
        TransactionMontantEleve(
            datetime_tx=datetime.datetime(2026, 7, 15, 21, 44),
            iban_source="FR7630003000409876543210925",
            pays_source="France",
            banque="Société Générale",
            iban_destination="DE89370400440532013000",
            pays_destination="Germany",
            montant=5749.22,
        ),
        TransactionMontantEleve(
            datetime_tx=datetime.datetime(2026, 8, 14, 0, 8),
            iban_source="ES9121000418450200051332",
            pays_source="Spain",
            banque="CaixaBank",
            iban_destination="GB29NWBK60161331926819",
            pays_destination="United Kingdom",
            montant=8554.31,
        ),
        TransactionMontantEleve(
            datetime_tx=datetime.datetime(2026, 11, 4, 10, 47),
            iban_source="FR7613306000015678901234567",
            pays_source="France",
            banque="Crédit agricole",
            iban_destination="GB29NWBK60161331926819",
            pays_destination="United Kingdom",
            montant=9454.84,
        ),
    ]

    return (
        montants_par_iban,
        montants_par_banque,
        montants_par_iban_destination,
        transactions_montant_eleve,
    )


def test_montants_par_iban_equals(get_data_from_bdd, data_expected):
    montants_par_iban = get_data_from_bdd[0]
    expected_montants_par_iban = data_expected[0]
    assert montants_par_iban == expected_montants_par_iban

def test_montants_par_banque_equals(get_data_from_bdd, data_expected):
    montants_par_banque = get_data_from_bdd[1]
    expected_montants_par_banque = data_expected[1]
    assert montants_par_banque == expected_montants_par_banque

def test_montants_par_iban_destination_equals(get_data_from_bdd, data_expected):
    montants_par_iban_destination = get_data_from_bdd[2]
    expected_montants_par_iban_destination = data_expected[2]
    assert montants_par_iban_destination == expected_montants_par_iban_destination

def test_transactions_montant_eleve_equals(get_data_from_bdd, data_expected):
    transactions_montant_eleve = get_data_from_bdd[3]
    expected_transactions_montant_eleve = data_expected[3]
    assert transactions_montant_eleve == expected_transactions_montant_eleve