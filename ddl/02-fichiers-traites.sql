/********** Mémoire des fichiers déjà traités **********/
/* un fichier est inscrit ici dans la même transaction que l'insertion de ses données :
   soit le fichier est entièrement pris en compte, soit pas du tout */
CREATE TABLE fichiers_traites (
    nom_fichier VARCHAR(255) PRIMARY KEY,
    date_traitement TIMESTAMP NOT NULL DEFAULT now()
);
