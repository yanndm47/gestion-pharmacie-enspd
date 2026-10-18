"""Configuration de l'application.

Les valeurs par défaut correspondent à une installation WampServer classique.
Pour les changer SANS modifier le code (par exemple port 3307 pour MariaDB),
définissez des variables d'environnement avant de lancer l'application :

    set PHARMA_DB_PORT=3307          (Windows, invite de commandes)
    $env:PHARMA_DB_PORT = "3307"     (Windows, PowerShell)
"""
import os

APP_TITLE = "Pharmacie – Gestion"

DB_HOST = os.getenv("PHARMA_DB_HOST", "localhost")
DB_PORT = int(os.getenv("PHARMA_DB_PORT", "3306"))
DB_USER = os.getenv("PHARMA_DB_USER", "root")
DB_PASSWORD = os.getenv("PHARMA_DB_PASSWORD", "")
DB_NAME = os.getenv("PHARMA_DB_NAME", "pharmacie")

# Alerte de péremption : nombre de jours (doit rester cohérent avec la vue
# v_alertes_peremption du script SQL 02, qui utilise 90 jours).
SEUIL_PEREMPTION_JOURS = 90

# Validité d une ordonnance, en jours à partir de la date de prescription (RG-25)
VALIDITE_ORDONNANCE_JOURS = 14

# Nom affiché sur les tickets de caisse
NOM_PHARMACIE = os.getenv("PHARMA_NOM", "Pharmacie")
