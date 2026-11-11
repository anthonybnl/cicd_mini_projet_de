import csv
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import boto3

# On fixe la seed (du random) afin que le process soit reproductible (les tests passeront donc puisque les données seront toujours les mêmes)
SEED = 2026
NB_FICHIERS = 3

# permet de simuler un bug pour faire échouer la pipeline (voir README)
SIMULER_BUG = os.environ.get("SIMULER_BUG", "")

# WITH_OCR=1 : bonus OCR
WITH_OCR = os.environ.get("WITH_OCR", "0") == "1"

DOSSIER_IMAGES = Path(__file__).resolve().parents[1] / "images"

# endpoint du S3 : localhost par défaut, "http://s3:9001" depuis le conteneur Docker
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localhost:9001")

COMPTES = {
    "FR7630006000011234567890189": ("France", "Société Générale"),
    "FR7630003000409876543210925": ("France", "Société Générale"),
    "FR7613306000015678901234567": ("France", "Crédit agricole"),
    "DE89370400440532013000": ("Germany", "Deutsche Bank"),
    "GB29NWBK60161331926819": ("United Kingdom", "NatWest"),
    "ES9121000418450200051332": ("Spain", "CaixaBank"),
}

COLONNES = [
    "datetime",
    "iban_source",
    "pays_source",
    "banque",
    "iban_destination",
    "pays_destination",
    "montant",
]


def generer_montant() -> float:
    if random.random() < 0.2:
        return round(random.uniform(5000, 10000), 2)
    return round(random.uniform(1, 1000), 2)


def generer_transaction() -> dict:
    referentiel_iban = list(COMPTES.keys())

    iban_source = random.choice(referentiel_iban)
    iban_destination = random.choice(
        [iban for iban in referentiel_iban if iban != iban_source]
    )

    pays_source, banque = COMPTES[iban_source]
    pays_destination, _ = COMPTES[iban_destination]

    date = datetime(2026, 1, 1) + timedelta(minutes=random.randint(0, 365 * 24 * 60))

    return {
        "datetime": date.isoformat(),
        "iban_source": iban_source,
        "pays_source": pays_source,
        "banque": banque,
        "iban_destination": iban_destination,
        "pays_destination": pays_destination,
        "montant": generer_montant(),
    }


def generer_fichier() -> list[dict]:
    nb_transactions = random.randint(5, 10)
    return [generer_transaction() for _ in range(nb_transactions)]


def envoyer_fichier_dans_bucket(s3, bucket, filepath: Path, data):
    with open(str(filepath), "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=COLONNES, lineterminator="\n")

        writer.writeheader()
        for row in data:
            writer.writerow(row)

    s3.upload_file(str(filepath), bucket, f"data/{filepath.name}")

    # suppression du fichier CSV local
    # filepath.unlink()


def envoyer_images_dans_bucket(s3, bucket):
    # le nombre d'images n'est pas fixé : on envoie toutes les images du dossier
    images = sorted(DOSSIER_IMAGES.glob("*.png"))
    for image in images:
        s3.upload_file(str(image), bucket, f"data/{image.name}")
        print(f"{image.name} : image envoyée")
    print(f"{len(images)} image(s) envoyée(s) pour l'OCR.")


def main():
    random.seed(SEED)

    # client boto3
    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id="rustfs",
        aws_secret_access_key="rustfs",
    )
    bucket = "bucketminiprojet"

    # on test si le bucket existe
    if not any(b["Name"] == bucket for b in s3.list_buckets()["Buckets"]):
        print(f"Le bucket '{bucket}' n'existe pas. Création en cours...")
        s3.create_bucket(Bucket=bucket)

    for i in range(1, NB_FICHIERS + 1):
        data = generer_fichier()

        if SIMULER_BUG == "generation" and i == 2:
            # bug simulé sur le deuxième fichier
            print("==== SIMULER_BUG=generation : le fichier 2 sera en erreur ====")
            data[0]["montant"] = round(
                data[0]["montant"] * 100, 2
            )  # montant en centimes pour simuler le bug

        filepath = Path(f"transactions_{i:02d}.csv").resolve()
        envoyer_fichier_dans_bucket(s3, bucket, filepath, data)
        print(f"{filepath.name} : {len(data)} transactions envoyées")

    if WITH_OCR:
        envoyer_images_dans_bucket(s3, bucket)

    print("Fichiers envoyés dans le bucket avec succès.")


if __name__ == "__main__":
    main()
