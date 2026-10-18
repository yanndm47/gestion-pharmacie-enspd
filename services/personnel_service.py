"""Comptes du personnel (RG-46 à RG-50) : réservé à l'administrateur."""
from datetime import date
from typing import Optional

from core.errors import BusinessError
from core.permissions import ROLES, require
from core.security import hash_password, valider_mot_de_passe
from db.connection import lecture, transaction


def lister_personnel(user) -> list:
    require(user, "gerer_comptes")
    with lecture() as cur:
        cur.execute(
            "SELECT id_personnel, nom, prenom, login, role, telephone, date_embauche, actif "
            "FROM personnel ORDER BY actif DESC, nom, prenom"
        )
        return cur.fetchall()


def _controler_identite(nom: str, prenom: str, role: str) -> None:
    if not (nom or "").strip() or not (prenom or "").strip():
        raise BusinessError("Le nom et le prénom sont obligatoires.")
    if role not in ROLES:
        raise BusinessError("Rôle invalide : pharmacien, caissier ou administrateur.")


def _controler_mot_de_passe(mot_de_passe: str) -> None:
    try:
        valider_mot_de_passe(mot_de_passe)
    except ValueError as erreur:
        raise BusinessError(str(erreur)) from erreur


def _exiger_autre_administrateur(cur, id_personnel: int) -> None:
    """Évite de se retrouver sans administrateur actif."""
    cur.execute(
        "SELECT COUNT(*) AS n FROM personnel "
        "WHERE role = 'administrateur' AND actif = 1 AND id_personnel <> %s",
        (id_personnel,),
    )
    if cur.fetchone()["n"] == 0:
        raise BusinessError("Il doit rester au moins un administrateur actif.")


def creer_compte(user, nom: str, prenom: str, login: str, mot_de_passe: str, role: str,
                 telephone: str = "", date_embauche: Optional[date] = None) -> int:
    """Crée un compte ; le mot de passe est haché avant d'être stocké (RG-48)."""
    require(user, "gerer_comptes")
    _controler_identite(nom, prenom, role)
    login = (login or "").strip()
    if not login:
        raise BusinessError("L'identifiant de connexion est obligatoire.")
    _controler_mot_de_passe(mot_de_passe)
    with transaction() as cur:
        cur.execute(
            "INSERT INTO personnel (nom, prenom, login, mot_de_passe_hash, role, telephone, date_embauche) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (nom.strip(), prenom.strip(), login, hash_password(mot_de_passe), role,
             (telephone or "").strip() or None, date_embauche),
        )
        return cur.lastrowid


def modifier_compte(user, id_personnel: int, nom: str, prenom: str, role: str,
                    telephone: str = "") -> None:
    """Modifie l'identité et le rôle (pas l'identifiant de connexion)."""
    require(user, "gerer_comptes")
    _controler_identite(nom, prenom, role)
    with transaction() as cur:
        cur.execute("SELECT role, actif FROM personnel WHERE id_personnel = %s FOR UPDATE", (id_personnel,))
        ancien = cur.fetchone()
        if ancien is None:
            raise BusinessError("Ce compte n'existe pas.")
        if role != ancien["role"]:
            if id_personnel == user.id_personnel:
                raise BusinessError("Vous ne pouvez pas modifier votre propre rôle.")
            if ancien["role"] == "administrateur" and ancien["actif"]:
                _exiger_autre_administrateur(cur, id_personnel)
        cur.execute(
            "UPDATE personnel SET nom = %s, prenom = %s, role = %s, telephone = %s WHERE id_personnel = %s",
            (nom.strip(), prenom.strip(), role, (telephone or "").strip() or None, id_personnel),
        )


def changer_statut_compte(user, id_personnel: int, actif: bool) -> None:
    """Désactive ou réactive un compte ; un compte n'est jamais supprimé (RG-49)."""
    require(user, "gerer_comptes")
    if not actif and id_personnel == user.id_personnel:
        raise BusinessError("Vous ne pouvez pas désactiver votre propre compte.")
    with transaction() as cur:
        cur.execute("SELECT role, actif FROM personnel WHERE id_personnel = %s FOR UPDATE", (id_personnel,))
        ancien = cur.fetchone()
        if ancien is None:
            raise BusinessError("Ce compte n'existe pas.")
        if not actif and ancien["role"] == "administrateur" and ancien["actif"]:
            _exiger_autre_administrateur(cur, id_personnel)
        cur.execute("UPDATE personnel SET actif = %s WHERE id_personnel = %s",
                    (1 if actif else 0, id_personnel))


def reinitialiser_mot_de_passe(user, id_personnel: int, nouveau_mot_de_passe: str) -> None:
    require(user, "gerer_comptes")
    _controler_mot_de_passe(nouveau_mot_de_passe)
    with transaction() as cur:
        cur.execute("UPDATE personnel SET mot_de_passe_hash = %s WHERE id_personnel = %s",
                    (hash_password(nouveau_mot_de_passe), id_personnel))
