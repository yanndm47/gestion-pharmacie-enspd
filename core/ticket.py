"""Mise en forme d'un ticket de caisse (texte à largeur fixe, sans dépendance)."""
from core.formatting import fmt_date, fmt_montant


def _gauche_droite(gauche: str, droite: str, largeur: int) -> str:
    """'gauche ........ droite' sur `largeur` caractères (la gauche est tronquée si besoin)."""
    place = largeur - len(droite) - 1
    if len(gauche) > place:
        gauche = gauche[: max(place - 1, 0)] + "…"
    return gauche + " " * (largeur - len(gauche) - len(droite)) + droite


def formater_ticket(nom_pharmacie, id_vente, date_vente, vendeur, client, lignes, total,
                    paiement, statut="validee", largeur=42) -> str:
    """Construit le texte du ticket.

    lignes : liste de dicts avec nom_commercial, quantite, prix_unitaire, sous_total.
    """
    trait = "-" * largeur
    sortie = [nom_pharmacie.upper().center(largeur).rstrip(), trait]
    horodatage = f"{fmt_date(date_vente)} {date_vente.strftime('%H:%M')}"
    sortie.append(_gauche_droite(f"Ticket n° {id_vente}", horodatage, largeur))
    sortie.append(f"Vendeur : {vendeur}")
    if client:
        sortie.append(f"Client  : {client}")
    sortie.append(trait)
    for l in lignes:
        sortie.append(l["nom_commercial"] if len(l["nom_commercial"]) <= largeur
                      else l["nom_commercial"][: largeur - 1] + "…")
        detail = f"   {l['quantite']} x {fmt_montant(l['prix_unitaire'])}"
        sortie.append(_gauche_droite(detail, fmt_montant(l["sous_total"]), largeur))
    sortie.append(trait)
    sortie.append(_gauche_droite("TOTAL", fmt_montant(total), largeur))
    sortie.append(f"Paiement : {paiement}")
    if statut == "annulee":
        sortie += ["", "*** VENTE ANNULÉE ***".center(largeur).rstrip()]
    sortie += ["", "Merci de votre visite".center(largeur).rstrip()]
    return "\n".join(sortie)
