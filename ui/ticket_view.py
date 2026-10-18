"""Fenêtre d'affichage d'un ticket de caisse : enregistrer en .txt ou imprimer (Windows)."""
import os
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class TicketDialog(tk.Toplevel):
    def __init__(self, parent, id_vente: int, texte: str):
        super().__init__(parent)
        self.title(f"Ticket – vente n°{id_vente}")
        self.id_vente = id_vente
        self.texte = texte
        self.transient(parent.winfo_toplevel())

        cadre = ttk.Frame(self, padding=10)
        cadre.pack(fill="both", expand=True)
        zone = tk.Text(cadre, width=46, height=min(max(texte.count("\n") + 2, 12), 32),
                       font=("Courier New", 10), wrap="none", background="#fffef5")
        zone.insert("1.0", texte)
        zone.configure(state="disabled")
        zone.pack(fill="both", expand=True)

        boutons = ttk.Frame(cadre)
        boutons.pack(fill="x", pady=(10, 0))
        ttk.Button(boutons, text="Enregistrer…", command=self.enregistrer).pack(side="left")
        ttk.Button(boutons, text="Imprimer", command=self.imprimer).pack(side="left", padx=6)
        ttk.Button(boutons, text="Fermer", command=self.destroy).pack(side="right")
        self.bind("<Escape>", lambda _e: self.destroy())

    def enregistrer(self):
        chemin = filedialog.asksaveasfilename(
            parent=self, defaultextension=".txt", initialfile=f"ticket_{self.id_vente}.txt",
            filetypes=[("Texte", "*.txt")])
        if chemin:
            with open(chemin, "w", encoding="utf-8") as f:
                f.write(self.texte)

    def imprimer(self):
        if not sys.platform.startswith("win"):
            messagebox.showinfo("Impression", "L'impression directe est disponible sous Windows. "
                                "Utilisez « Enregistrer… » puis imprimez le fichier.", parent=self)
            return
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
                f.write(self.texte)
            os.startfile(f.name, "print")           # noqa: S606 (Windows uniquement)
        except OSError as erreur:
            messagebox.showerror("Impression", f"Impossible d'imprimer : {erreur}", parent=self)
