import csv
import json


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
        total = sum(float(row["montant"]) for row in rows)
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

    # transactions >= 5000


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
        print(f"date: {row['datetime']}, montant: {row['montant']}, iban_source: {row['iban_source']}, iban_destination: {row['iban_destination']}, banque: {row['banque']}")



if __name__ == "__main__":
    main()
