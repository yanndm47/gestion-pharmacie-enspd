"""Connexion des utilisateurs (table personnel)."""
from dataclasses import dataclass

from core.errors import BusinessError
from core.permissions import ROLE_LABELS
from core.security import hash_password, needs_rehash, verify_password
from db.connection import lecture, transaction


@dataclass(frozen=True)
class Utilisateur:
    id_personnel: int
    nom: str
    prenom: str
    role: str

    @property
    def nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}"

    @property
    def role_libelle(self) -> str:
        return ROLE_LABELS.get(self.role, self.role)


def connecter(login: str, mot_de_passe: str) -> Utilisateur:
    """Vérifie l'identifiant et le mot de passe, retourne l'utilisateur connecté.

    Le message d'échec est volontairement identique que l'identifiant ou le mot
    de passe soit faux, pour ne pas révéler quels identifiants existent.
    """
    login = (login or "").strip()
    if not login or not mot_de_passe:
        raise BusinessError("Saisissez votre identifiant et votre mot de passe.")

    with lecture() as cur:
        cur.execute(
            "SELECT id_personnel, nom, prenom, mot_de_passe_hash, role, actif "
            "FROM personnel WHERE login = %s",
            (login,),
        )
        ligne = cur.fetchone()

    if ligne is None or not verify_password(mot_de_passe, ligne["mot_de_passe_hash"]):
        raise BusinessError("Identifiant ou mot de passe incorrect.")
    if not ligne["actif"]:
        raise BusinessError("Ce compte est désactivé. Contactez l'administrateur.")

    # Les comptes du jeu de test sont convertis au hachage PBKDF2 à la 1re connexion
    if needs_rehash(ligne["mot_de_passe_hash"]):
        with transaction() as cur:
            cur.execute(
                "UPDATE personnel SET mot_de_passe_hash = %s WHERE id_personnel = %s",
                (hash_password(mot_de_passe), ligne["id_personnel"]),
            )

    return Utilisateur(
        id_personnel=ligne["id_personnel"],
        nom=ligne["nom"],
        prenom=ligne["prenom"],
        role=ligne["role"],
    )


def changer_mot_de_passe(user: Utilisateur, ancien: str, nouveau: str) -> None:
    """Permet à chaque utilisateur de changer son propre mot de passe."""
    from core.security import valider_mot_de_passe

    try:
        valider_mot_de_passe(nouveau)
    except ValueError as erreur:
        raise BusinessError(str(erreur)) from erreur
    with transaction() as cur:
        cur.execute(
            "SELECT mot_de_passe_hash FROM personnel WHERE id_personnel = %s FOR UPDATE",
            (user.id_personnel,),
        )
        ligne = cur.fetchone()
        if ligne is None or not verify_password(ancien or "", ligne["mot_de_passe_hash"]):
            raise BusinessError("L'ancien mot de passe est incorrect.")
        cur.execute("UPDATE personnel SET mot_de_passe_hash = %s WHERE id_personnel = %s",
                    (hash_password(nouveau), user.id_personnel))
