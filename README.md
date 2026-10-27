# STARZ Order Manager

## Installation sous Windows

1. Récupérez le dépôt Git sur votre ordinateur (par exemple avec **Code > Télécharger ZIP** ou `git clone`).
2. Ouvrez le dossier téléchargé et double-cliquez sur **install.bat**.
3. Une fois l'installation terminée, lancez **STARZ Order Manager** depuis le raccourci créé sur le Bureau.

Python 3.10 ou plus récent doit être installé sur le poste. L'installateur crée l'application dans `%LOCALAPPDATA%\Programs\STARZ Order Manager` et installe les dépendances dans un environnement isolé. Une connexion Internet est nécessaire pendant l'installation.

Pour mettre à jour l'application, récupérez les dernières modifications Git puis relancez `install.bat`.

## Données locales

La base de commandes, les pièces jointes Outlook et le fichier Excel BLOG ne sont pas inclus dans le dépôt afin de ne pas publier de données métier. Chaque utilisateur conserve ainsi ses propres commandes et pièces jointes.

Pour afficher le stock et utiliser la recherche de produits, demandez une copie autorisée du fichier `BLOG_2026_RJ45.xlsx` à votre équipe, puis placez-le ici après l'installation :

`%LOCALAPPDATA%\Programs\STARZ Order Manager\data\imports\BLOG_2026_RJ45.xlsx`

Créez le dossier `data\imports` s'il n'existe pas. Sans ce fichier, les fonctionnalités de stock et de recherche de produits ne sont pas disponibles.

L'import Outlook nécessite Outlook classique configuré sur le poste. La lecture des PDF numérisés nécessite également Tesseract OCR ; les autres fonctions de lecture PDF ne dépendent pas de Tesseract.
