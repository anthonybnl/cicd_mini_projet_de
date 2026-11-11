# Mini projet Data Engineering - CI/CD

Dans le cadre du cours EFREI M2 CI/CD : Mini projet Data Engineering

[![pipeline](https://github.com/anthonybnl/cicd_mini_projet_de/actions/workflows/pipeline.yml/badge.svg)](https://github.com/anthonybnl/cicd_mini_projet_de/actions/workflows/pipeline.yml)

## Génération des données

Le script `src/generation_data.py` génère 3 fichiers CSV de 5 à 10 transactions chacun, puis les envoie dans le bucket S3.

Les données générées aléatoirement mais avec une **seed fixe** (`SEED = 2026`) : elles sont donc identiques à chaque exécution ce qui rend le pipeline testable (`pytest`)

## Simulation d'un bug dans la génération des données

Afin de pouvoir vérifier le bon fonctionnement des tests, nous pouvons simuler un bug via la variable d'environnement `SIMULER_BUG=generation`  
Lorsque cette variable est définie avec cette valeur, des changements interviennent dans les données générées.

Ainsi les tests ne passent plus.

Sur un `push` classique, la variable est vide et aucun bug n'est simulé.

Afin de déclencher ce comportement il faut lancer la pipeline manuellement et choisir l'option `generation` pour le choix `Bug à simuler`

Résultat :

[Lien vers la pipeline](https://github.com/anthonybnl/cicd_mini_projet_de/actions/runs/42994084459)

![](img/01.png)

## Ajout du retry sur le traitement des données

TODO

### Mémoire des fichiers traités

La liste des fichiers déjà traités est stockée en base, dans la table `fichiers_traites` (voir `ddl/02-fichiers-traites.sql`).

Pour chaque fichier, l'insertion des résultats **et** l'inscription du fichier dans `fichiers_traites` se font dans **une seule transaction**.  
S'il n'y a pas d'erreur, le fichier est traité et marqué comme traité. Sinon tout est annulé : **rollback**.

Les montants s'additionnent à ceux déjà en base, c'est l'agrégation incrémentale.

### Deux niveaux de retry

1. **Dans le script** : le téléchargement depuis le S3 et l'insertion en base sont retentés 3 fois (5 secondes d'attente), pour les erreurs passagères (S3 ou BDD indisponible un court instant)
2. **Dans la pipeline** : si un fichier est toujours en erreur, le script se termine avec un code d'erreur et la pipeline le relance. Grâce à la table `fichiers_traites`, seuls les fichiers en erreur sont rejoués.

### Simulation d'un bug d'insertion

Pour tester ce mécanisme, nous pouvons simuler un bug d'insertion via la variable d'environnement `SIMULER_BUG=insertion`.  
L'insertion du fichier 2 échoue alors au milieu de la transaction (après l'insertion des montants, avant le marquage du fichier) : tout est annulé par le rollback.

Le bug n'est simulé qu'au **premier lancement** du script : un fichier `bug_insertion` est créé à la racine du projet. Au lancement suivant, le fichier existe déjà et le bug n'est plus simulé. Le fichier est supprimé quand tous les fichiers sont traités avec succès.

Déroulement attendu :

1. **Premier lancement** : le fichier 1 est traité, le fichier 2 échoue 3 fois (retry dans le script), le fichier 3 est traité. Le script se termine en erreur.
2. **Retry de la pipeline** : les fichiers 1 et 3 sont ignorés (déjà traités), le fichier 2 est traité avec succès.
3. **Tests** : ils passent, aucun montant n'a été compté deux fois.

Afin de déclencher ce comportement il faut lancer la pipeline manuellement et choisir l'option `insertion` pour le choix `Bug à simuler`

Résultat :

[Lien vers la pipeline](TODO)

![](img/02.png)

## Installation de Tesseract (OCR)

Afin de faire fonctionner `pytesseract` pour l'OCR, il est nécessaire d'installer Tesseract :

```bash
sudo apt install tesseract-ocr
sudo apt install libtesseract-dev
```
