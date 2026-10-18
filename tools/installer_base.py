#!/usr/bin/env python3
"""Installe la base de données pharmacie en exécutant les scripts SQL sans passer par DBeaver.

Pourquoi : DBeaver coupe parfois une instruction à chaque point-virgule, y compris à l'intérieur
d'un trigger ou d'une procédure, ce qui donne l'erreur 1064 « near '' ». Ce programme lit les
scripts lui-même et envoie chaque trigger ou procédure en UNE seule instruction.

Usage (depuis le dossier pharmacie_app, environnement virtuel activé) :
    python tools/installer_base.py            installe les scripts 01, 02 et 03
    python tools/installer_base.py --demo     installe aussi le jeu enrichi (script 06)
    python tools/installer_base.py --dossier C:/chemin/des/scripts

ATTENTION : le script 01 supprime et recrée la base « pharmacie ».
La connexion utilise les mêmes variables d'environnement que l'application
(PHARMA_DB_HOST, PHARMA_DB_PORT, PHARMA_DB_USER, PHARMA_DB_PASSWORD).
"""
import argparse
import os
import re
import sys

ROUTINE = re.compile(r"^CREATE\s+(DEFINER\s*=\s*\S+\s+)?(PROCEDURE|FUNCTION|TRIGGER)\b", re.IGNORECASE)


def sans_commentaire(ligne: str) -> str:
    """Retire un commentaire « -- ... » en fin de ligne, sans toucher aux textes entre apostrophes."""
    entre_quotes = False
    i = 0
    while i < len(ligne):
        c = ligne[i]
        if c == "'":
            entre_quotes = not entre_quotes
        elif not entre_quotes and ligne.startswith("--", i) and (i + 2 >= len(ligne) or ligne[i + 2] in " \t"):
            return ligne[:i].rstrip()
        i += 1
    return ligne.rstrip()


def decouper(texte: str):
    """Découpe un script en instructions. Gère DELIMITER et les routines CREATE ... BEGIN ... END."""
    delimiteur = ";"
    tampon, en_routine = [], False
    for ligne in texte.splitlines():
        brut = ligne.strip()
        if not tampon:
            if not brut or brut.startswith("--"):
                continue
            if brut.upper().startswith("DELIMITER "):
                delimiteur = brut.split(None, 1)[1].strip()
                continue
            en_routine = bool(ROUTINE.match(brut)) and delimiteur == ";"
        elif brut.startswith("--"):
            tampon.append(ligne)               # commentaire à l'intérieur d'une instruction
            continue
        code = sans_commentaire(brut)
        if en_routine:
            fin = code.upper() == "END;"            # un simple « END » (fin de CASE) ne termine pas la routine
        else:
            fin = code.endswith(delimiteur)
        if fin:
            tampon.append(ligne.replace(brut, code))
            instruction = "\n".join(tampon).rstrip()
            if instruction.endswith(delimiteur):
                instruction = instruction[: -len(delimiteur)].rstrip()
            elif en_routine and instruction.endswith(";"):
                instruction = instruction[:-1].rstrip()
            yield instruction
            tampon, en_routine = [], False
        else:
            tampon.append(ligne)
    if tampon and "".join(tampon).strip():
        raise ValueError("Le script se termine au milieu d'une instruction : " + tampon[0].strip()[:80])


def parametres():
    return dict(host=os.getenv("PHARMA_DB_HOST", "localhost"), port=int(os.getenv("PHARMA_DB_PORT", "3306")),
                user=os.getenv("PHARMA_DB_USER", "root"), password=os.getenv("PHARMA_DB_PASSWORD", ""),
                charset="utf8mb4", collation="utf8mb4_unicode_ci", autocommit=True)


def executer_script(cnx, chemin: str) -> int:
    with open(chemin, encoding="utf-8") as f:
        instructions = list(decouper(f.read()))
    curseur = cnx.cursor()
    for numero, instruction in enumerate(instructions, start=1):
        try:
            curseur.execute(instruction)
            if curseur.with_rows:
                lignes = curseur.fetchall()
                if lignes and len(lignes) <= 12:
                    titres = [c[0] for c in curseur.description]
                    print("   ", " | ".join(titres))
                    for l in lignes:
                        print("   ", " | ".join(str(v) for v in l))
        except Exception as erreur:
            print(f"\nERREUR dans {os.path.basename(chemin)}, instruction n°{numero} :")
            print("   ", instruction[:300].replace("\n", "\n    "))
            print(f"   -> {erreur}")
            try:
                cnx.rollback()
            except Exception:
                pass
            raise SystemExit(1)
    curseur.close()
    return len(instructions)


def main():
    arg = argparse.ArgumentParser(description="Installe la base pharmacie sans DBeaver.")
    arg.add_argument("--demo", action="store_true", help="installe aussi le script 06 (jeu enrichi)")
    arg.add_argument("--dossier", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sql"),
                     help="dossier contenant les scripts SQL (défaut : dossier sql de l'application)")
    options = arg.parse_args()
    scripts = ["01_schema_pharmacie.sql", "02_regles_triggers_pharmacie.sql", "03_donnees_test_pharmacie.sql"]
    if options.demo:
        scripts.append("06_donnees_enrichies_pharmacie.sql")
    chemins = [os.path.join(options.dossier, s) for s in scripts]
    manquants = [c for c in chemins if not os.path.isfile(c)]
    if manquants:
        sys.exit("Scripts introuvables : " + ", ".join(manquants) + "\nUtilisez --dossier pour indiquer leur emplacement.")
    try:
        import mysql.connector
    except ImportError:
        sys.exit("Module manquant : exécutez d'abord  pip install -r requirements.txt")
    try:
        cnx = mysql.connector.connect(**parametres())
    except Exception as erreur:
        sys.exit(f"Connexion impossible : {erreur}\nVérifiez que WampServer est vert et le port (PHARMA_DB_PORT).")
    for chemin in chemins:
        print(f"-> {os.path.basename(chemin)}")
        n = executer_script(cnx, chemin)
        print(f"   {n} instructions exécutées")
    cnx.close()
    print("\nBase installée. Vérifiez dans DBeaver : SHOW TRIGGERS; doit donner 13 lignes.")


if __name__ == "__main__":
    main()
