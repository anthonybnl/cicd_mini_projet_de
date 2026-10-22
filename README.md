# Mini projet Data Engineering - CI/CD

Dans le cadre du cours EFREI M2 CI/CD : Mini projet Data Engineering

[![pipeline](https://github.com/anthonybnl/cicd_mini_projet_de/actions/workflows/pipeline.yml/badge.svg)](https://github.com/anthonybnl/cicd_mini_projet_de/actions/workflows/pipeline.yml)

## Simulation d'une erreur de calcul

Afin de tester la robustesse de notre pipeline CI/CD, notamment des tests, nous avons volontairement changer une règle de calcul (moyenne au lieu de somme)

Résultat :

![](doc/01.png)

Comme on peut le voir, les tests ont échoué car la règle de calcul a été modifiée.
