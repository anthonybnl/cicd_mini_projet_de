import json
import random
from datetime import datetime

list_datetimes = [
    datetime(2026, 9, 11, 8, 54, 00),
    datetime(2026, 6, 17, 23, 13, 00),
    datetime(2026, 1, 8, 14, 20, 00),
]

list_ibans = [
    "DE89370400440532013000",
    "FR7630006000011234567890189",
    "GB29NWBK60161331926819",
    "ES9121000418450200051332",
]

list_pays = ["France", "Germany", "United Kingdom", "Spain"]

list_banques = ["Société Générale", "Deutsche Bank", "Crédit agricole"]

longueur_donnee = 10


data = []


for _ in range(longueur_donnee):
    dt = random.choice(list_datetimes)
    iban_source = random.choice(list_ibans)
    pays_source = random.choice(list_pays)
    banque = random.choice(list_banques)
    iban_destination = random.choice(list_ibans)
    pays_destination = random.choice(list_pays)

    item = {
        "datetime": dt.isoformat(),
        "iban_source": iban_source,
        "pays_source": pays_source,
        "banque": banque,
        "iban_destination": iban_destination,
        "pays_destination": pays_destination,
        "montant": round(random.uniform(0.5, 100), 2),
    }

    data.append(item)

json_data = json.dumps(data, indent=4)
with open("data.json", "w") as f:
    f.write(json_data)

print(data)
