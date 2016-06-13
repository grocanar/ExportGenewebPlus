
# GenewebPlus

## Introduction
Cette addon permet d'exporter au format gwplus. C'est le format utilisé en internet par le site web geneanet.
le format gwplus est décrit à l'url suivante: 

## Problématique.
Il y a plusieurs problèmes principaux pour écrire le module d'exportation vers le format gwplus.
+ Il n'y a pas une stricte équivalence entre le format xml de gramps et le format gwplus
+ le format gwplus est gourverné par la famille. Ce qui pose souci évidement pour les individus "isolés".
* l'information des invidus est affichés en deux modes.
1. un mode étendue ou toutes les informations de l'individus apparaissent comme ici
 
**fam de_"Dupont _"Ale"x_IV.0  14/7/1967 #bp Le_Havre,76600,Seine-Maritime,Normandie,France +21/12/2014 #mp Le_Havre,76600,Seine-Maritime,Normandie,France #ms ac
te_de_mariage_de_Dupont_et_Durand Durand Alexia.1 12/4/1967**

2.un mode réduit 
**de_"Dupont _"Ale"x_IV.0**

Le mode étendue ne doit apparaitre qu'une fois dans le fichier et suivant un ordre bien précis.
Si l'individu est un enfant d'une famille existante le mode étendu doit apparaitre dans la déclaration en tant qu'enfant.

Sinon cela doit apparaitre soit dans la déclaration de la famille soit en tant que témoin.

si lindividu n'apparait dans aucun de ces cas on doit ajouter cet individu dans une famille ou les parents sont inconnu.
## Fonctionnement


## Réglage.

Les correspondances entre les paramètres GRAMPS et les tages geneanet sont définies en naut du fichier
* dans le tableau FAMILYCONSTANTEVENTS
* dans le tableau PERSONCONSTANTEVENTS
* dans le tableau RELATIONCONSTANTEVENTS
* dans le tableau RELATIONEVENTS
* dans la liste WITNESSROLETYPE

### FAMILYCONSTANTEVENTS
ce tableau contient la correspondance des événements familaux. 
il y a une correponsance presque parfaite sauf pour l'evenement CENSUS qui n'a pas de tag cortrespondant dans geneweb. C'est en modifiant ce tableau si on veut modifier les valeurs.
Pour un evenement personnalisé c'est le nom de l'evenement qui est pris pour le tag geneweb. Geneanet l'affichera alors tel quel.


### PERSONCONSTANTEVENTS
ce tableau contient la correspondance des événements personnels.
Plusieurs évenements ne sont pas reconnus dans geneweb et certains tags geneweb n'ont pas de correspondances dans GRAMPS.

### RELATIONCONSTANTEVENTS
Ce tableau contient les relations qu'il faut écrire si on veut utiliser les tages geneweb correspondant.

### RELATIONEVENTS
Ce tableau traite le cas particulier du baptème. On définit le role "CUSTOM3 que doit avoir une personne dans un évenement pour endosser le rôle de Parrain ou de Marraine.

### WITNESSROLETYPE
Contient la liste des roles dans les évenements qui permettent de devenir un témoins sur geneweb.


##Limitations

+ Si on fait référence a des personnes qui ne sont pas dans le filtre d'export le résultat est incertain.
* On ne gère pas les attributs.
