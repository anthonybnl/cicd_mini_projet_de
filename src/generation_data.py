all_data = [
    {
        "datetime": "2026-09-11T08:54:00",
        "iban_source": "DE89370400440532013000",
        "pays_source": "France",
        "banque": "Crédit agricole",
        "iban_destination": "DE89370400440532013000",
        "pays_destination": "Germany",
        "montant": 32
    },
    {
        "datetime": "2026-06-17T23:13:00",
        "iban_source": "FR7630006000011234567890189",
        "pays_source": "Germany",
        "banque": "Société Générale",
        "iban_destination": "ES9121000418450200051332",
        "pays_destination": "Spain",
        "montant": 7459
    },
    {
        "datetime": "2026-06-17T23:13:00",
        "iban_source": "FR7630006000011234567890189",
        "pays_source": "Germany",
        "banque": "Société Générale",
        "iban_destination": "ES9121000418450200051332",
        "pays_destination": "United Kingdom",
        "montant": 7
    },
    {
        "datetime": "2026-06-17T23:13:00",
        "iban_source": "DE89370400440532013000",
        "pays_source": "United Kingdom",
        "banque": "Deutsche Bank",
        "iban_destination": "ES9121000418450200051332",
        "pays_destination": "Germany",
        "montant": 24.24
    },
    {
        "datetime": "2026-01-08T14:20:00",
        "iban_source": "FR7630006000011234567890189",
        "pays_source": "Germany",
        "banque": "Deutsche Bank",
        "iban_destination": "FR7630006000011234567890189",
        "pays_destination": "United Kingdom",
        "montant": 72
    },
    {
        "datetime": "2026-01-08T14:20:00",
        "iban_source": "FR7630006000011234567890189",
        "pays_source": "United Kingdom",
        "banque": "Crédit agricole",
        "iban_destination": "DE89370400440532013000",
        "pays_destination": "Spain",
        "montant": 5199
    },
    {
        "datetime": "2026-09-11T08:54:00",
        "iban_source": "ES9121000418450200051332",
        "pays_source": "United Kingdom",
        "banque": "Deutsche Bank",
        "iban_destination": "FR7630006000011234567890189",
        "pays_destination": "United Kingdom",
        "montant": 0.5
    },
    {
        "datetime": "2026-09-11T08:54:00",
        "iban_source": "DE89370400440532013000",
        "pays_source": "France",
        "banque": "Crédit agricole",
        "iban_destination": "ES9121000418450200051332",
        "pays_destination": "France",
        "montant": 56
    },
    {
        "datetime": "2026-09-11T08:54:00",
        "iban_source": "ES9121000418450200051332",
        "pays_source": "France",
        "banque": "Société Générale",
        "iban_destination": "DE89370400440532013000",
        "pays_destination": "Germany",
        "montant": 4
    },
    {
        "datetime": "2026-09-11T08:54:00",
        "iban_source": "FR7630006000011234567890189",
        "pays_source": "Spain",
        "banque": "Crédit agricole",
        "iban_destination": "FR7630006000011234567890189",
        "pays_destination": "Germany",
        "montant": 10.99
    },
]

# génération du CSV

import csv

with open("data.csv", "w", newline="") as csvfile:
    fieldnames = ["datetime", "iban_source", "pays_source", "banque", "iban_destination", "pays_destination", "montant"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator="\n")

    writer.writeheader()
    for row in all_data:
        writer.writerow(row)