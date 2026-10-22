import csv

from sqlalchemy import text

from db import get_database_engine


def extraire_data() -> list[dict]:
    csv_file = "data.csv"
    data = []

    with open(csv_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)  # noqa: PERF402
    return data


def _mon_group_by(data: list[dict], key: str) -> dict:
    grouped = {}
    for row in data:
        k = row[key]
        if k not in grouped:
            grouped[k] = []
        grouped[k].append(row)
    return grouped


def traiter_data(data: list[dict]):

    # somme des montants par iban d'origine
    grouped = _mon_group_by(data, "iban_source")

    results_montants_par_iban = []
    for iban, rows in grouped.items():
        total = sum(float(row["montant"]) for row in rows)
        results_montants_par_iban.append((iban, total))

    # somme des montants par banque source
    grouped = _mon_group_by(data, "banque")

    results_montants_par_banque = []
    for banque, rows in grouped.items():

        # test pour que la CI échoue en changeant la méthode de calcul
        total = sum(float(row["montant"]) for row in rows) / len(rows) # on ne calcule plus la somme mais la moyenne
        # les tests pytest ne vont pas passer car on ne calcule plus la somme mais la moyenne

        results_montants_par_banque.append((banque, total))

    # somme des montant reçus par iban de destination
    grouped = _mon_group_by(data, "iban_destination")

    results_montants_par_iban_destination = []
    for iban, rows in grouped.items():
        total = sum(float(row["montant"]) for row in rows)
        results_montants_par_iban_destination.append((iban, total))

    transactions_cinq_mille = [row for row in data if float(row["montant"]) >= 5000]
    return (
        results_montants_par_iban,
        results_montants_par_banque,
        results_montants_par_iban_destination,
        transactions_cinq_mille,
    )


def inserer_montants_par_iban(engine, results_montants_par_iban):
    with engine.begin() as conn:
        for iban, total in results_montants_par_iban:
            conn.execute(
                text(
                    "INSERT INTO montants_par_iban (iban, montant) VALUES (:iban, :total) "
                    "ON CONFLICT (iban) DO UPDATE SET montant = EXCLUDED.montant"
                ),
                {"iban": iban, "total": total},
            )
        conn.commit()


def inserer_montants_par_banque(engine, results_montants_par_banque):
    with engine.begin() as conn:
        for banque, total in results_montants_par_banque:
            conn.execute(
                text(
                    "INSERT INTO montants_par_banque (banque, montant) VALUES (:banque, :total) "
                    "ON CONFLICT (banque) DO UPDATE SET montant = EXCLUDED.montant"
                ),
                {"banque": banque, "total": total},
            )
        conn.commit()


def inserer_montants_par_iban_destination(
    engine, results_montants_par_iban_destination
):
    with engine.begin() as conn:
        for iban, total in results_montants_par_iban_destination:
            conn.execute(
                text(
                    "INSERT INTO montants_par_iban_destination (iban, montant) VALUES (:iban, :total) "
                    "ON CONFLICT (iban) DO UPDATE SET montant = EXCLUDED.montant"
                ),
                {"iban": iban, "total": total},
            )
        conn.commit()


def inserer_transactions_cinq_mille(engine, transactions_cinq_mille):
    with engine.begin() as conn:
        for row in transactions_cinq_mille:
            conn.execute(
                text(
                    "INSERT INTO transactions_montant_eleve (datetime_tx, montant, iban_source, pays_source, iban_destination, pays_destination, banque) "
                    "VALUES (:datetime, :montant, :iban_source, :pays_source, :iban_destination, :pays_destination, :banque) "
                    "ON CONFLICT (datetime_tx, iban_source, iban_destination) DO NOTHING"
                ),
                {
                    "datetime": row["datetime"],
                    "montant": row["montant"],
                    "iban_source": row["iban_source"],
                    "pays_source": row["pays_source"],
                    "iban_destination": row["iban_destination"],
                    "pays_destination": row["pays_destination"],
                    "banque": row["banque"],
                },
            )
        conn.commit()


def inserer_data(
    engine,
    results_montants_par_iban,
    results_montants_par_banque,
    results_montants_par_iban_destination,
    transactions_cinq_mille,
):
    inserer_montants_par_iban(engine, results_montants_par_iban)
    inserer_montants_par_banque(engine, results_montants_par_banque)
    inserer_montants_par_iban_destination(engine, results_montants_par_iban_destination)
    inserer_transactions_cinq_mille(engine, transactions_cinq_mille)


def main():
    data = extraire_data()
    (
        results_montants_par_iban,
        results_montants_par_banque,
        results_montants_par_iban_destination,
        transactions_cinq_mille,
    ) = traiter_data(data)

    print("Montants par IBAN:")
    for iban, total in results_montants_par_iban:
        print(f"IBAN: {iban}, Total: {total}")
    print("\nMontants par banque:")

    for banque, total in results_montants_par_banque:
        print(f"Banque: {banque}, Total: {total}")
    print("\nMontants par IBAN de destination:")

    for iban, total in results_montants_par_iban_destination:
        print(f"IBAN: {iban}, Total: {total}")

    print("\nTransactions >= 5000:")
    for row in transactions_cinq_mille:
        print(
            f"date: {row['datetime']}, montant: {row['montant']}, iban_source: {row['iban_source']}, iban_destination: {row['iban_destination']}, banque: {row['banque']}"
        )

    engine = get_database_engine()
    inserer_data(
        engine,
        results_montants_par_iban,
        results_montants_par_banque,
        results_montants_par_iban_destination,
        transactions_cinq_mille,
    )


if __name__ == "__main__":
    main()
