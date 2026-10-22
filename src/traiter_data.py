import csv
import json
import re
import sys
from pathlib import Path

import boto3
from sqlalchemy import text

from db import get_database_engine


def extraire_data(file_path) -> list[dict]:
    data = []

    with open(file_path) as csvfile:
        reader = csv.DictReader(csvfile)
        data = list(reader)
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


def traiter_lot_donnee(data: list[dict]):
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


def telecharger_fichiers_s3(s3, bucket: str) -> list[Path]:
    objects = s3.list_objects_v2(Bucket=bucket)
    liste_fichiers = [obj["Key"] for obj in objects.get("Contents", [])]

    liste_fichiers_locaux: list[Path] = []

    for fichier in liste_fichiers:
        # on extrait le nom du fichier si on a le pattern data/<fichier>.csv, en regex. Pas de sous dossier !
        match = re.match(r"data/([a-zA-Z0-9_]+\.csv)", fichier)
        if match:
            nom_fichier = match.group(1)
            s3.download_file(bucket, fichier, nom_fichier)
            liste_fichiers_locaux.append(Path(nom_fichier).resolve())
    return liste_fichiers_locaux


def main():

    # client boto3
    s3 = boto3.client(
        "s3",
        endpoint_url="http://localhost:9001",
        aws_access_key_id="rustfs",
        aws_secret_access_key="rustfs",
    )
    bucket = "bucketminiprojet"

    if not any(b["Name"] == bucket for b in s3.list_buckets()["Buckets"]):
        raise RuntimeError(f"Le bucket '{bucket}' n'existe pas.")

    liste_fichiers = telecharger_fichiers_s3(s3, bucket)
    print("Fichiers téléchargés :", liste_fichiers)

    liste_fichiers_csv = sorted(liste_fichiers)

    # gestion du retry : on mémorise les fichiers traités
    MEMORY_FILEPATH = Path("fichiers_traite.json").resolve()

    fichiers_traite = []
    has_error = False
    all_data = []

    if MEMORY_FILEPATH.exists():
        with open(MEMORY_FILEPATH, "r") as f:
            fichiers_traite = json.load(f)

    for fichier_csv in liste_fichiers_csv:
        if str(fichier_csv) in fichiers_traite:
            print(f"Le fichier {fichier_csv} a déjà été traité. Passage au suivant.")
            continue

        # on traite le fichier
        try:
            print(f"Traitement du fichier : {fichier_csv} ...")
            data = extraire_data(fichier_csv)
            all_data += data

            # on enregistre le fichier traité dans la liste et le fichier JSON
            fichiers_traite.append(str(fichier_csv))
            with open(MEMORY_FILEPATH, "w") as f:
                json.dump(fichiers_traite, f)
        except Exception as e:  # noqa: BLE001
            print(
                f"Erreur lors du traitement du fichier {fichier_csv} : {type(e).__name__} {e}"
            )
            has_error = True

        # suppression du fichier local après traitement
        Path(fichier_csv).unlink()

    if len(all_data) > 0:
        traiter_lot_donnee(all_data)

    if has_error:
        print(
            "Certains fichiers n'ont pas pu être traités.\nLe fichier mémoire est conservé pour le retry"
        )
        sys.exit(1)
    else:
        print("Tous les fichiers ont été traités avec succès.")
        if MEMORY_FILEPATH.exists():
            MEMORY_FILEPATH.unlink()  # on supprime le fichier mémoire car tous les fichiers ont été traités avec succès


if __name__ == "__main__":
    main()
