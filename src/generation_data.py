import csv
from pathlib import Path
import boto3

fichier1 = [
    {
        "datetime": "2026-09-11T08:54:00",
        "iban_source": "DE89370400440532013000",
        "pays_source": "France",
        "banque": "Crédit agricole",
        "iban_destination": "DE89370400440532013000",
        "pays_destination": "Germany",
        "montant": 32,
    },
    {
        "datetime": "2026-06-17T23:13:00",
        "iban_source": "FR7630006000011234567890189",
        "pays_source": "Germany",
        "banque": "Société Générale",
        "iban_destination": "ES9121000418450200051332",
        "pays_destination": "Spain",
        "montant": 7459,
    },
    {
        "datetime": "2026-06-17T23:13:00",
        "iban_source": "FR7630006000011234567890189",
        "pays_source": "Germany",
        "banque": "Société Générale",
        "iban_destination": "ES9121000418450200051332",
        "pays_destination": "United Kingdom",
        "montant": 7,
    },
    {
        "datetime": "2026-06-17T23:13:00",
        "iban_source": "DE89370400440532013000",
        "pays_source": "United Kingdom",
        "banque": "Deutsche Bank",
        "iban_destination": "ES9121000418450200051332",
        "pays_destination": "Germany",
        "montant": 24.24,
    },
    {
        "datetime": "2026-01-08T14:20:00",
        "iban_source": "FR7630006000011234567890189",
        "pays_source": "Germany",
        "banque": "Deutsche Bank",
        "iban_destination": "FR7630006000011234567890189",
        "pays_destination": "United Kingdom",
        "montant": 72,
    },
    {
        "datetime": "2026-01-08T14:20:00",
        "iban_source": "FR7630006000011234567890189",
        "pays_source": "United Kingdom",
        "banque": "Crédit agricole",
        "iban_destination": "DE89370400440532013000",
        "pays_destination": "Spain",
        "montant": 5199,
    },
    {
        "datetime": "2026-09-11T08:54:00",
        "iban_source": "ES9121000418450200051332",
        "pays_source": "United Kingdom",
        "banque": "Deutsche Bank",
        "iban_destination": "FR7630006000011234567890189",
        "pays_destination": "United Kingdom",
        "montant": 0.5,
    },
    {
        "datetime": "2026-09-11T08:54:00",
        "iban_source": "DE89370400440532013000",
        "pays_source": "France",
        "banque": "Crédit agricole",
        "iban_destination": "ES9121000418450200051332",
        "pays_destination": "France",
        "montant": 56,
    },
    {
        "datetime": "2026-09-11T08:54:00",
        "iban_source": "ES9121000418450200051332",
        "pays_source": "France",
        "banque": "Société Générale",
        "iban_destination": "DE89370400440532013000",
        "pays_destination": "Germany",
        "montant": 4,
    },
    {
        "datetime": "2026-09-11T08:54:00",
        "iban_source": "FR7630006000011234567890189",
        "pays_source": "Spain",
        "banque": "Crédit agricole",
        "iban_destination": "FR7630006000011234567890189",
        "pays_destination": "Germany",
        "montant": 10.99,
    },
]

fichier2 = [
    {
        "datetime": "2026-09-11T08:54:00",
        "iban_source": "DE89370400440532013000",
        "pays_source": "France",
        "banque": "Crédit agricole",
        "iban_destination": "DE89370400440532013000",
        "pays_destination": "Germany",
        "montant": 82.56,
    }
]


def envoyer_fichier_dans_bucket(s3, bucket, filepath: Path, data):
    with open(str(filepath), "w", newline="") as csvfile:
        fieldnames = [
            "datetime",
            "iban_source",
            "pays_source",
            "banque",
            "iban_destination",
            "pays_destination",
            "montant",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator="\n")

        writer.writeheader()
        for row in data:
            writer.writerow(row)

    s3.upload_file(str(filepath), bucket, f"data/{filepath.name}")

    # suppression du ficheir CSV
    filepath.unlink()


def main():

    # client boto3
    s3 = boto3.client(
        "s3",
        endpoint_url="http://localhost:9001",
        aws_access_key_id="rustfs",
        aws_secret_access_key="rustfs",
    )
    bucket = "bucketminiprojet"

    # on test si le bucket existe
    if not any(b["Name"] == bucket for b in s3.list_buckets()["Buckets"]):
        print(f"Le bucket '{bucket}' n'existe pas. Création en cours...")
        s3.create_bucket(Bucket=bucket)

    envoyer_fichier_dans_bucket(s3, bucket, Path("data1.csv").resolve(), fichier1)
    envoyer_fichier_dans_bucket(s3, bucket, Path("data2.csv").resolve(), fichier2)


if __name__ == "__main__":
    main()
