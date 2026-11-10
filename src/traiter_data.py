import csv
import re
import sys
import time
from pathlib import Path

import boto3
from sqlalchemy import text

from db import get_database_engine


def extraire_data(file_path) -> list[dict]:
    data = []

    with open(file_path, encoding="utf-8") as csvfile:
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


def avec_retry(fonction, *args, nb_essais=3, attente=5):
    # relance la fonction en cas d'erreur (S3 ou BDD indisponible un court instant)
    for essai in range(1, nb_essais + 1):
        try:
            return fonction(*args)
        except Exception as e:
            print(f"Erreur (tentative {essai}/{nb_essais}) : {type(e).__name__} {e}")
            if essai == nb_essais:
                raise
            print(f"Nouvelle tentative dans {attente} secondes...")
            time.sleep(attente)


# les montants s'additionnent à ceux déjà en base :
# chaque fichier vient compléter les totaux des fichiers précédents


def inserer_montants_par_iban(conn, results_montants_par_iban):
    for iban, total in results_montants_par_iban:
        conn.execute(
            text(
                "INSERT INTO montants_par_iban (iban, montant) VALUES (:iban, :total) "
                "ON CONFLICT (iban) DO UPDATE SET montant = montants_par_iban.montant + EXCLUDED.montant"
            ),
            {"iban": iban, "total": total},
        )


def inserer_montants_par_banque(conn, results_montants_par_banque):
    for banque, total in results_montants_par_banque:
        conn.execute(
            text(
                "INSERT INTO montants_par_banque (banque, montant) VALUES (:banque, :total) "
                "ON CONFLICT (banque) DO UPDATE SET montant = montants_par_banque.montant + EXCLUDED.montant"
            ),
            {"banque": banque, "total": total},
        )


def inserer_montants_par_iban_destination(conn, results_montants_par_iban_destination):
    for iban, total in results_montants_par_iban_destination:
        conn.execute(
            text(
                "INSERT INTO montants_par_iban_destination (iban, montant) VALUES (:iban, :total) "
                "ON CONFLICT (iban) DO UPDATE SET montant = montants_par_iban_destination.montant + EXCLUDED.montant"
            ),
            {"iban": iban, "total": total},
        )


def inserer_transactions_cinq_mille(conn, transactions_cinq_mille):
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


def marquer_fichier_traite(conn, nom_fichier: str):
    # pas de ON CONFLICT ici : si le fichier est déjà en base, la clé primaire
    # fait échouer la transaction et rien n'est compté deux fois
    conn.execute(
        text("INSERT INTO fichiers_traites (nom_fichier) VALUES (:nom_fichier)"),
        {"nom_fichier": nom_fichier},
    )


def inserer_data(engine, nom_fichier: str, resultats):
    (
        results_montants_par_iban,
        results_montants_par_banque,
        results_montants_par_iban_destination,
        transactions_cinq_mille,
    ) = resultats

    # une seule transaction pour tout le fichier : si une insertion plante,
    # tout est annulé (rollback) et le fichier n'est pas marqué comme traité
    with engine.begin() as conn:
        inserer_montants_par_iban(conn, results_montants_par_iban)
        inserer_montants_par_banque(conn, results_montants_par_banque)
        inserer_montants_par_iban_destination(conn, results_montants_par_iban_destination)
        inserer_transactions_cinq_mille(conn, transactions_cinq_mille)
        marquer_fichier_traite(conn, nom_fichier)


def lire_fichiers_traites(engine) -> set[str]:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT nom_fichier FROM fichiers_traites"))
        return {nom_fichier for (nom_fichier,) in result.fetchall()}


def lister_fichiers_s3(s3, bucket: str) -> list[str]:
    # pour tester le retry
    # return ["data/data1.csv", "data/data3.csv"]

    objects = s3.list_objects_v2(Bucket=bucket)
    liste_fichiers = [obj["Key"] for obj in objects.get("Contents", [])]
    return liste_fichiers


def telecharger_un_fichier_s3(s3, bucket: str, key: str) -> Path:
    match = re.match(r"data/([a-zA-Z0-9_]+\.csv)", key)
    if not match:
        raise ValueError(f"Le key '{key}' ne correspond pas au pattern attendu 'data/<fichier>.csv'")

    local_file = Path(match.group(1))
    print(f"Téléchargement du fichier {key} vers {local_file} ...")
    avec_retry(s3.download_file, bucket, key, str(local_file))
    return local_file


def traiter_un_fichier(s3, bucket: str, engine, key_s3: str):
    fichier_csv = telecharger_un_fichier_s3(s3, bucket, key_s3)
    try:
        data = extraire_data(fichier_csv)
        resultats = traiter_data(data)
    finally:
        # suppression du fichier local, même en cas d'erreur
        fichier_csv.unlink()

    print(f"{len(data)} transactions, dont {len(resultats[3])} >= 5000. Insertion en base ...")
    avec_retry(inserer_data, engine, key_s3, resultats)


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

    liste_fichiers_s3 = sorted(lister_fichiers_s3(s3, bucket))
    print("Liste des fichiers S3 :", liste_fichiers_s3)

    # gestion du retry : la liste des fichiers déjà traités est stockée en base
    engine = get_database_engine()
    fichiers_traites = avec_retry(lire_fichiers_traites, engine)

    fichiers_en_erreur = []

    for key_s3 in liste_fichiers_s3:

        if key_s3 in fichiers_traites:
            print(f"Le fichier {key_s3} a déjà été traité. Passage au suivant.")
            continue

        print(f"\nTraitement du fichier : {key_s3} ...")
        try:
            traiter_un_fichier(s3, bucket, engine, key_s3)
            print(f"Fichier {key_s3} traité avec succès.")
        except Exception as e:  # noqa: BLE001
            # on passe au fichier suivant : un fichier en erreur ne bloque pas les autres
            print(f"Erreur lors du traitement du fichier {key_s3} : {type(e).__name__} {e}")
            fichiers_en_erreur.append(key_s3)

    if fichiers_en_erreur:
        print(f"\nFichiers en erreur : {fichiers_en_erreur}")
        print("Ils seront retraités au prochain lancement (les autres ne seront pas rejoués).")
        sys.exit(1)

    print("\nTous les fichiers ont été traités avec succès.")


if __name__ == "__main__":
    main()
