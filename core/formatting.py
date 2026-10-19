"""Fonctions d'affichage (montants, dates)."""
from datetime import date, datetime
from decimal import Decimal


def fmt_montant(valeur) -> str:
    """12000 -> '12 000' ; 1234.5 -> '1 234,50'. Aucune devise n'est ajoutée."""
    if valeur is None:
        return ""
    d = Decimal(str(valeur))
    if d == d.to_integral_value():
        return f"{int(d):,}".replace(",", " ")
    # Séparateur de milliers : espace ; séparateur décimal : virgule
    return f"{d:,.2f}".replace(",", " ").replace(".", ",")


def fmt_date(valeur) -> str:
    """Date ou datetime -> 'JJ/MM/AAAA'."""
    if valeur is None:
        return ""
    if isinstance(valeur, (date, datetime)):
        return valeur.strftime("%d/%m/%Y")
    return str(valeur)


def parse_date(texte: str) -> date:
    """Accepte 'JJ/MM/AAAA' ou 'AAAA-MM-JJ'. Lève ValueError sinon."""
    texte = (texte or "").strip()
    for modele in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texte, modele).date()
        except ValueError:
            continue
    raise ValueError("Date invalide : utilisez le format JJ/MM/AAAA.")


def parse_decimal(texte: str):
    """'1 500', '1500,50' ou '1500.5' -> Decimal. Lève ValueError si invalide."""
    from decimal import Decimal, InvalidOperation

    brut = (texte or "").replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        valeur = Decimal(brut)
    except InvalidOperation:
        raise ValueError("Nombre invalide.") from None
    if not valeur.is_finite():
        raise ValueError("Nombre invalide.")
    return valeur


def fmt_valeur(valeur, genre: str = "texte") -> str:
    """Affichage selon le genre : texte, int, montant, date, datetime, pct, decimal.

    Ne lève jamais d'exception : une valeur inattendue est simplement affichée telle quelle.
    """
    if valeur is None:
        return ""
    try:
        if genre == "montant":
            return fmt_montant(valeur)
        if genre == "int":
            return str(int(valeur))
        if genre == "date":
            return fmt_date(valeur)
        if genre == "datetime":
            return valeur.strftime("%d/%m/%Y %H:%M") if hasattr(valeur, "strftime") else str(valeur)
        if genre == "pct":
            return f"{Decimal(str(valeur)):.1f} %".replace(".", ",")
        if genre == "decimal":
            return f"{Decimal(str(valeur)):.1f}".replace(".", ",")
    except (ValueError, TypeError, ArithmeticError):
        return str(valeur)
    return str(valeur)
