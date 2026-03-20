"""
Gestionnaire de Templates - Application System Tray
====================================================
Usage:
  python clipboard_app.py          → Lance l'app en arrière-plan (icône tray)
  python clipboard_app.py --popup  → Affiche le popup de sélection (appelé par clic droit)

Raccourci clavier global : Ctrl+Shift+Q
"""

import sys
import os
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading

# --- Chemins ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_FILE = os.path.join(SCRIPT_DIR, "templates.json")

# --- Données par défaut ---
DEFAULT_TEMPLATES = [
    {"name": "Bonjour", "content": "Bonjour,\n\nJe me permets de vous contacter concernant "},
    {"name": "Cordialement", "content": "Cordialement,\n\nRodolphe FONTAINE"},
    {"name": "Accusé réception", "content": "Bonjour,\n\nJe vous confirme la bonne réception de votre message. Je reviendrai vers vous dans les meilleurs délais.\n\nCordialement"},
    {"name": "Disponibilité", "content": "Pouvez-vous me confirmer vos disponibilités pour cette semaine ?"},
]


# =============================================================================
# GESTION DES TEMPLATES (JSON)
# =============================================================================

def load_templates():
    if not os.path.exists(TEMPLATES_FILE):
        save_templates(DEFAULT_TEMPLATES)
        return DEFAULT_TEMPLATES
    try:
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return DEFAULT_TEMPLATES


def save_templates(templates):
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)


# =============================================================================
# REGISTRE WINDOWS - MENU CONTEXTUEL
# =============================================================================

REGISTRY_KEY = r"Software\Classes\Directory\Background\shell\TemplateManager"
REGISTRY_COMMAND_KEY = REGISTRY_KEY + r"\command"
MENU_LABEL = "Coller un template..."


def get_python_cmd():
    """Retourne le chemin vers pythonw.exe (sans console)."""
    python_exe = sys.executable
    pythonw = python_exe.replace("python.exe", "pythonw.exe")
    if os.path.exists(pythonw):
        return pythonw
    return python_exe


def install_context_menu():
    """Ajoute l'entrée dans le menu contextuel Windows (clic droit bureau)."""
    try:
        import winreg
        script_path = os.path.abspath(__file__)
        python_cmd = get_python_cmd()
        command = f'"{python_cmd}" "{script_path}" --popup'

        # Créer la clé principale avec le label du menu
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, MENU_LABEL)
        winreg.CloseKey(key)

        # Créer la sous-clé command
        cmd_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_COMMAND_KEY)
        winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
        winreg.CloseKey(cmd_key)

        return True
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'installer le menu contextuel :\n{e}")
        return False


def uninstall_context_menu():
    """Supprime l'entrée du menu contextuel Windows."""
    try:
        import winreg
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_COMMAND_KEY)
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY)
        return True
    except FileNotFoundError:
        return True  # Déjà désinstallé
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de désinstaller le menu contextuel :\n{e}")
        return False


def is_context_menu_installed():
    """Vérifie si le menu contextuel est installé."""
    try:
        import winreg
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY)
        return True
    except FileNotFoundError:
        return False


# =============================================================================
# POPUP DE SÉLECTION DES TEMPLATES
# =============================================================================

_active_popup = None  # Singleton : une seule instance à la fois


class TemplatePopup:
    """Fenêtre popup sans bordure qui s'affiche à la position du curseur."""

    BG = "#2b2b2b"
    BG_HOVER = "#3d3d3d"
    FG = "#ffffff"
    FG_PREVIEW = "#aaaaaa"
    BORDER = "#555555"
    TITLE_BG = "#1e1e1e"

    def __init__(self):
        self.templates = load_templates()
        self.root = None
        self.blocker = None

    def show(self):
        global _active_popup

        # Fermer le popup existant si déjà ouvert
        if _active_popup is not None:
            _active_popup._close()
            return

        _active_popup = self

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg=self.BG)
        self.root.attributes("-topmost", True)

        # Fenêtre transparente plein écran pour détecter les clics en dehors
        self.blocker = tk.Toplevel(self.root)
        self.blocker.overrideredirect(True)
        self.blocker.attributes("-alpha", 0.01)
        self.blocker.attributes("-topmost", True)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.blocker.geometry(f"{screen_w}x{screen_h}+0+0")
        self.blocker.bind("<Button-1>", lambda e: self._close())
        self.blocker.bind("<Button-3>", lambda e: self._close())

        # Position : à la position du curseur
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()

        self._build_ui()

        # Ajuster la position pour ne pas sortir de l'écran
        self.root.update_idletasks()
        w = self.root.winfo_reqwidth()
        h = self.root.winfo_reqheight()

        if x + w > screen_w:
            x = screen_w - w - 10
        if y + h > screen_h:
            y = screen_h - h - 10

        self.root.geometry(f"+{x}+{y}")
        self.root.lift()  # S'assurer que le popup est au-dessus du blocker
        self.root.bind("<Escape>", lambda e: self._close())
        self.root.focus_force()
        self.root.mainloop()

    def _build_ui(self):
        # Titre
        title = tk.Label(
            self.root,
            text="  Choisir un template",
            bg=self.TITLE_BG, fg=self.FG_PREVIEW,
            font=("Segoe UI", 9),
            anchor="w", pady=5, padx=5
        )
        title.pack(fill="x")

        # Séparateur
        tk.Frame(self.root, bg=self.BORDER, height=1).pack(fill="x")

        if not self.templates:
            tk.Label(
                self.root,
                text="Aucun template disponible",
                bg=self.BG, fg=self.FG_PREVIEW,
                font=("Segoe UI", 9),
                padx=15, pady=8
            ).pack()
            return

        # Boutons pour chaque template
        for template in self.templates:
            self._add_template_button(template)

    def _add_template_button(self, template):
        name = template.get("name", "Sans titre")
        content = template.get("content", "")
        preview = content[:60].replace("\n", " ")
        if len(content) > 60:
            preview += "..."

        frame = tk.Frame(self.root, bg=self.BG, cursor="hand2")
        frame.pack(fill="x", padx=2, pady=1)

        name_lbl = tk.Label(
            frame, text=name,
            bg=self.BG, fg=self.FG,
            font=("Segoe UI", 10, "bold"),
            anchor="w", padx=12, pady=3
        )
        name_lbl.pack(fill="x")

        if preview:
            preview_lbl = tk.Label(
                frame, text=preview,
                bg=self.BG, fg=self.FG_PREVIEW,
                font=("Segoe UI", 8),
                anchor="w", padx=12, pady=0
            )
            preview_lbl.pack(fill="x")

        # Hover effect
        def on_enter(e, f=frame):
            f.configure(bg=self.BG_HOVER)
            for child in f.winfo_children():
                child.configure(bg=self.BG_HOVER)

        def on_leave(e, f=frame):
            f.configure(bg=self.BG)
            for child in f.winfo_children():
                child.configure(bg=self.BG)

        def on_click(e, t=template):
            self._select_template(t["content"])

        for widget in [frame, name_lbl] + ([preview_lbl] if preview else []):
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

        # Séparateur léger
        tk.Frame(self.root, bg=self.BORDER, height=1).pack(fill="x", padx=8)

    def _select_template(self, content):
        """Ferme le popup et colle le template."""
        self._close()

        def paste():
            time.sleep(0.15)  # Laisser le temps au focus de revenir
            try:
                import pyperclip
                pyperclip.copy(content)
            except ImportError:
                # Fallback si pyperclip n'est pas installé
                import subprocess
                subprocess.run(
                    ["clip"],
                    input=content.encode("utf-16"),
                    check=True
                )
            try:
                import pyautogui
                pyautogui.hotkey("ctrl", "v")
            except ImportError:
                pass  # Si pyautogui absent, au moins le clipboard est rempli

        threading.Thread(target=paste, daemon=True).start()

    def _close(self):
        global _active_popup
        _active_popup = None
        if self.blocker:
            try:
                self.blocker.destroy()
            except Exception:
                pass
            self.blocker = None
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None


# =============================================================================
# FENÊTRE DE GESTION DES TEMPLATES
# =============================================================================

class TemplateManager(tk.Toplevel):
    """Fenêtre de gestion : ajouter, modifier, supprimer les templates."""

    def __init__(self, parent=None):
        if parent:
            super().__init__(parent)
        else:
            self._root = tk.Tk()
            self._root.withdraw()
            super().__init__(self._root)

        self.title("Gestionnaire de Templates")
        self.geometry("600x450")
        self.resizable(True, True)
        self.templates = load_templates()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # --- Frame principale ---
        main = tk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Liste des templates ---
        list_frame = tk.LabelFrame(main, text="Templates", padx=5, pady=5)
        list_frame.pack(fill="both", expand=True, side="left", padx=(0, 5))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode="single",
            font=("Segoe UI", 10),
            width=25
        )
        self.listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        # Boutons CRUD
        btn_frame = tk.Frame(main)
        btn_frame.pack(fill="y", side="left")

        tk.Button(btn_frame, text="➕ Nouveau", width=14, command=self._new_template).pack(pady=3)
        tk.Button(btn_frame, text="✏️ Modifier", width=14, command=self._edit_template).pack(pady=3)
        tk.Button(btn_frame, text="🗑️ Supprimer", width=14, command=self._delete_template).pack(pady=3)
        tk.Button(btn_frame, text="⬆️ Monter", width=14, command=self._move_up).pack(pady=3)
        tk.Button(btn_frame, text="⬇️ Descendre", width=14, command=self._move_down).pack(pady=3)

        # --- Séparateur ---
        tk.Frame(self, height=1, bg="#cccccc").pack(fill="x", padx=10)

        # --- Menu contextuel Windows ---
        ctx_frame = tk.LabelFrame(self, text="Menu contextuel Windows (clic droit bureau)", padx=10, pady=8)
        ctx_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.ctx_status_var = tk.StringVar()
        self.ctx_status_lbl = tk.Label(ctx_frame, textvariable=self.ctx_status_var, font=("Segoe UI", 9))
        self.ctx_status_lbl.pack(side="left", padx=(0, 10))

        self.ctx_btn = tk.Button(ctx_frame, text="", width=20, command=self._toggle_context_menu)
        self.ctx_btn.pack(side="left")

        self._refresh_ctx_status()

        # Remplir la liste
        self._refresh_list()

    def _refresh_list(self, select_index=None):
        self.listbox.delete(0, "end")
        for t in self.templates:
            self.listbox.insert("end", t["name"])
        if select_index is not None:
            self.listbox.selection_set(select_index)
            self.listbox.see(select_index)

    def _on_select(self, event):
        pass  # Pas d'aperçu en temps réel pour simplifier

    def _get_selected_index(self):
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def _new_template(self):
        dialog = TemplateDialog(self, title="Nouveau template")
        if dialog.result:
            self.templates.append(dialog.result)
            save_templates(self.templates)
            self._refresh_list(len(self.templates) - 1)

    def _edit_template(self):
        idx = self._get_selected_index()
        if idx is None:
            messagebox.showinfo("Info", "Sélectionnez un template à modifier.")
            return
        dialog = TemplateDialog(self, title="Modifier le template", template=self.templates[idx])
        if dialog.result:
            self.templates[idx] = dialog.result
            save_templates(self.templates)
            self._refresh_list(idx)

    def _delete_template(self):
        idx = self._get_selected_index()
        if idx is None:
            messagebox.showinfo("Info", "Sélectionnez un template à supprimer.")
            return
        name = self.templates[idx]["name"]
        if messagebox.askyesno("Confirmer", f"Supprimer le template \"{name}\" ?"):
            del self.templates[idx]
            save_templates(self.templates)
            self._refresh_list(max(0, idx - 1) if self.templates else None)

    def _move_up(self):
        idx = self._get_selected_index()
        if idx is None or idx == 0:
            return
        self.templates[idx - 1], self.templates[idx] = self.templates[idx], self.templates[idx - 1]
        save_templates(self.templates)
        self._refresh_list(idx - 1)

    def _move_down(self):
        idx = self._get_selected_index()
        if idx is None or idx >= len(self.templates) - 1:
            return
        self.templates[idx + 1], self.templates[idx] = self.templates[idx], self.templates[idx + 1]
        save_templates(self.templates)
        self._refresh_list(idx + 1)

    def _refresh_ctx_status(self):
        if is_context_menu_installed():
            self.ctx_status_var.set("✅ Installé")
            self.ctx_status_lbl.configure(fg="green")
            self.ctx_btn.configure(text="Désinstaller le menu clic droit")
        else:
            self.ctx_status_var.set("❌ Non installé")
            self.ctx_status_lbl.configure(fg="red")
            self.ctx_btn.configure(text="Installer le menu clic droit")

    def _toggle_context_menu(self):
        if is_context_menu_installed():
            if uninstall_context_menu():
                messagebox.showinfo("Succès", "Menu contextuel désinstallé.")
        else:
            if install_context_menu():
                messagebox.showinfo(
                    "Succès",
                    "Menu contextuel installé !\n\n"
                    "Faites un clic droit sur le bureau pour voir l'entrée\n"
                    '"Coller un template..."'
                )
        self._refresh_ctx_status()

    def _on_close(self):
        self.destroy()
        try:
            self._root.destroy()
        except Exception:
            pass

    def run(self):
        """Lance la boucle principale (mode standalone)."""
        try:
            self._root.mainloop()
        except Exception:
            pass


# =============================================================================
# DIALOG NOUVEAU / MODIFIER
# =============================================================================

class TemplateDialog(tk.Toplevel):
    """Boîte de dialogue pour créer ou modifier un template."""

    def __init__(self, parent, title="Template", template=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(True, True)
        self.result = None
        self._template = template or {"name": "", "content": ""}
        self._build_ui()
        self.geometry("500x350")
        self.transient(parent)
        self.grab_set()
        self.wait_window()

    def _build_ui(self):
        frame = tk.Frame(self, padx=15, pady=10)
        frame.pack(fill="both", expand=True)

        # Nom
        tk.Label(frame, text="Nom du template :", anchor="w").pack(fill="x")
        self.name_var = tk.StringVar(value=self._template["name"])
        tk.Entry(frame, textvariable=self.name_var, font=("Segoe UI", 10)).pack(fill="x", pady=(0, 10))

        # Contenu
        tk.Label(frame, text="Contenu :", anchor="w").pack(fill="x")
        self.content_text = tk.Text(frame, font=("Segoe UI", 10), wrap="word", height=10)
        self.content_text.pack(fill="both", expand=True)
        self.content_text.insert("1.0", self._template["content"])

        # Boutons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        tk.Button(btn_frame, text="Annuler", command=self.destroy, width=10).pack(side="right", padx=(5, 0))
        tk.Button(btn_frame, text="Enregistrer", command=self._save, width=12).pack(side="right")

    def _save(self):
        name = self.name_var.get().strip()
        content = self.content_text.get("1.0", "end-1c")
        if not name:
            messagebox.showwarning("Attention", "Le nom ne peut pas être vide.", parent=self)
            return
        self.result = {"name": name, "content": content}
        self.destroy()


# =============================================================================
# APPLICATION SYSTEM TRAY
# =============================================================================

def create_tray_icon():
    """Crée une image d'icône 64x64 avec Pillow."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([4, 4, 60, 60], radius=12, fill="#4a90d9")
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except Exception:
        font = ImageFont.load_default()
    draw.text((18, 10), "T", fill="white", font=font)
    return img


def run_tray():
    """Lance l'application en mode system tray."""
    import pystray
    import keyboard

    icon_image = create_tray_icon()

    def hotkey_handler():
        popup = TemplatePopup()
        popup.show()

    keyboard.add_hotkey("ctrl+shift+q", lambda: threading.Thread(target=hotkey_handler, daemon=True).start())

    def open_manager(icon, item):
        def _open():
            manager = TemplateManager()
            manager.run()
        threading.Thread(target=_open, daemon=True).start()

    def open_popup(icon, item):
        def _open():
            popup = TemplatePopup()
            popup.show()
        threading.Thread(target=_open, daemon=True).start()

    def toggle_ctx(icon, item):
        if is_context_menu_installed():
            uninstall_context_menu()
        else:
            install_context_menu()
        # Forcer le rafraîchissement du menu
        icon.update_menu()

    def ctx_menu_label(item):
        if is_context_menu_installed():
            return "Désinstaller menu clic droit"
        return "Installer menu clic droit"

    def quit_app(icon, item):
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Coller un template...", open_popup),
        pystray.MenuItem("Gérer les templates", open_manager),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(ctx_menu_label, toggle_ctx),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quitter", quit_app),
    )

    icon = pystray.Icon("TemplateManager", icon_image, "Template Manager", menu)
    icon.run()


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def main():
    if "--popup" in sys.argv:
        # Mode popup : affiché par le clic droit Windows
        popup = TemplatePopup()
        popup.show()
    elif "--manage" in sys.argv:
        # Mode gestion standalone
        manager = TemplateManager()
        manager.run()
    else:
        # Mode normal : icône system tray
        run_tray()


if __name__ == "__main__":
    main()
