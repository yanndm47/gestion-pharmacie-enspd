"""Accès à MySQL / MariaDB (WampServer).

Deux gestionnaires de contexte, à utiliser dans TOUS les services :

    with lecture() as cur:          # consultation : aucune modification gardée
        cur.execute("SELECT ...", (param,))
        lignes = cur.fetchall()     # liste de dictionnaires

    with transaction() as cur:      # écriture : tout est validé, ou rien (RG-52)
        cur.execute("INSERT ...", (...))

Toujours passer les valeurs en paramètres (%s), jamais par concaténation de
texte : c'est ce qui protège contre l'injection SQL.

Les erreurs MySQL sont traduites en messages lisibles (voir traduire_erreur).
Notamment, les erreurs levées par les triggers du script 02 (SIGNAL, code 1644)
deviennent des BusinessError avec le message des règles de gestion (RG-xx).
"""
from contextlib import contextmanager

import mysql.connector
from mysql.connector import Error

import config
from core.errors import BusinessError, DatabaseUnavailable, PharmacieError

# Noms des contraintes d'unicité du script 01 -> message pour l'utilisateur
_DOUBLONS = {
    "uq_client_identite": "ce client existe déjà (même nom, prénom et date de naissance)",
    "uq_personnel_login": "cet identifiant est déjà utilisé",
    "uq_medicament": "ce médicament existe déjà (même nom, forme et dosage)",
    "uq_fournisseur_raison": "ce fournisseur existe déjà",
    "uq_stock_lot": "ce numéro de lot existe déjà pour ce médicament",
}


def traduire_erreur(err: Error) -> PharmacieError:
    """Transforme une erreur MySQL en erreur de l'application."""
    errno = getattr(err, "errno", None)
    msg = getattr(err, "msg", None) or str(err)

    if errno == 1644:  # SIGNAL SQLSTATE '45000' : règle de gestion d'un trigger
        return BusinessError(msg)
    if errno == 1062:  # doublon
        for cle, texte in _DOUBLONS.items():
            if cle in msg:
                return BusinessError(f"Doublon : {texte}.")
        return BusinessError("Doublon : cette valeur existe déjà.")
    if errno == 3819:  # contrainte CHECK
        return BusinessError(f"Valeur refusée par une contrainte de la base. Détail : {msg}")
    if errno == 1452:
        return BusinessError("Référence introuvable : l'élément lié n'existe pas.")
    if errno == 1451:
        return BusinessError("Suppression impossible : cet élément est encore utilisé ailleurs.")
    if errno in (2002, 2003, 2006, 2013):
        return DatabaseUnavailable(
            "Impossible de joindre MySQL. Vérifiez que WampServer est démarré "
            f"(icône verte) et que le port est correct (actuellement {config.DB_PORT})."
        )
    if errno == 1045:
        return DatabaseUnavailable(
            f"Accès refusé pour l'utilisateur « {config.DB_USER} ». "
            "Vérifiez PHARMA_DB_USER et PHARMA_DB_PASSWORD."
        )
    if errno == 1049:
        return DatabaseUnavailable(
            f"La base « {config.DB_NAME} » n'existe pas : exécutez d'abord les scripts SQL 01 à 03."
        )
    return PharmacieError(f"Erreur base de données ({errno}) : {msg}")


def _connecter():
    try:
        return mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            connection_timeout=5,
        )
    except Error as err:
        raise traduire_erreur(err) from err


@contextmanager
def lecture():
    """Curseur de consultation (résultats sous forme de dictionnaires)."""
    cnx = _connecter()
    try:
        cur = cnx.cursor(dictionary=True)
        try:
            yield cur
        except Error as err:
            raise traduire_erreur(err) from err
        finally:
            cur.close()
    finally:
        cnx.close()


@contextmanager
def transaction():
    """Curseur d'écriture dans une transaction : validée à la sortie, annulée sur erreur."""
    cnx = _connecter()
    try:
        cnx.start_transaction()
        cur = cnx.cursor(dictionary=True)
        try:
            yield cur
            cnx.commit()
        except Error as err:
            cnx.rollback()
            raise traduire_erreur(err) from err
        except Exception:
            cnx.rollback()
            raise
        finally:
            cur.close()
    finally:
        cnx.close()
