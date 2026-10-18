"""Hachage et vérification des mots de passe (bibliothèque standard uniquement).

Format stocké dans personnel.mot_de_passe_hash :
    pbkdf2_sha256$<itérations>$<sel>$<empreinte>

Les comptes du jeu de test (script SQL 03) ont un hachage SHA-256 simple
(64 caractères hexadécimaux, produit par SHA2() de MySQL). Ils sont acceptés
à la connexion puis automatiquement convertis au format ci-dessus.
"""
import hashlib
import hmac
import secrets

PREFIX = "pbkdf2_sha256"
ITERATIONS = 200_000


def _pbkdf2(password: str, salt: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("ascii"), iterations
    ).hex()


def hash_password(password: str, iterations: int = ITERATIONS) -> str:
    """Retourne le hachage à stocker pour ce mot de passe."""
    salt = secrets.token_hex(16)
    return f"{PREFIX}${iterations}${salt}${_pbkdf2(password, salt, iterations)}"


def _est_sha256_simple(stocke: str) -> bool:
    return len(stocke) == 64 and all(c in "0123456789abcdefABCDEF" for c in stocke)


def verify_password(password: str, stocke: str) -> bool:
    """Vrai si le mot de passe correspond au hachage stocké."""
    if not stocke:
        return False
    if stocke.startswith(PREFIX + "$"):
        try:
            _, iterations, salt, empreinte = stocke.split("$")
            calcule = _pbkdf2(password, salt, int(iterations))
        except (ValueError, UnicodeEncodeError):
            return False
        return hmac.compare_digest(calcule, empreinte)
    if _est_sha256_simple(stocke):
        calcule = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(calcule, stocke.lower())
    return False


def needs_rehash(stocke: str) -> bool:
    """Vrai si le hachage stocké est à convertir (ancien format ou trop faible)."""
    if not stocke.startswith(PREFIX + "$"):
        return True
    try:
        return int(stocke.split("$")[1]) < ITERATIONS
    except (IndexError, ValueError):
        return True


MIN_LONGUEUR = 8


def valider_mot_de_passe(mot_de_passe: str) -> None:
    """Lève ValueError si le mot de passe ne respecte pas la politique (8 caractères minimum)."""
    if not mot_de_passe or len(mot_de_passe) < MIN_LONGUEUR:
        raise ValueError(f"Le mot de passe doit contenir au moins {MIN_LONGUEUR} caractères.")
    if mot_de_passe.strip() != mot_de_passe:
        raise ValueError("Le mot de passe ne doit pas commencer ni finir par un espace.")
