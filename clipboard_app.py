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
from tkinter import ttk, messagebox
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
        return list(DEFAULT_TEMPLATES)
    try:
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return list(DEFAULT_TEMPLATES)


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
    python_exe = sys.executable
    pythonw = python_exe.replace("python.exe", "pythonw.exe")
    if os.path.exists(pythonw):
        return pythonw
    return python_exe


def install_context_menu():
    try:
        import winreg
        script_path = os.path.abspath(__file__)
        python_cmd = get_python_cmd()
        command = f'"{python_cmd}" "{script_path}" --popup'
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, MENU_LABEL)
        winreg.CloseKey(key)
        cmd_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_COMMAND_KEY)
        winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
        winreg.CloseKey(cmd_key)
        return True
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d'installer le menu contextuel :\n{e}")
        return False


def uninstall_context_menu():
    try:
        import winreg
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_COMMAND_KEY)
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REGISTRY_KEY)
        return True
    except FileNotFoundError:
        return True
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de désinstaller le menu contextuel :\n{e}")
        return False


def is_context_menu_installed():
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

POPUP_BG       = "#2b2b2b"
POPUP_BG_HOVER = "#3c5a8a"
POPUP_FG       = "#ffffff"
POPUP_FG_DIM   = "#aaaaaa"
POPUP_BORDER   = "#444444"
POPUP_HEAD_BG  = "#1e1e1e"
POPUP_SEARCH_BG = "#3a3a3a"
POPUP_BTN_BG   = "#1e3a5f"


class TemplatePopup:
    """Fenêtre popup sans bordure avec recherche et navigation clavier."""

    MAX_VISIBLE = 8  # Nombre max d'entrées visibles avant scroll

    def __init__(self):
        self.all_templates = load_templates()
        self.filtered = list(self.all_templates)
        self.focused_idx = 0
        self.item_frames = []
        self.root = None
        self.blocker = None
        self._list_frame = None
        self._canvas = None
        self._inner = None

    def show(self):
        global _active_popup

        if _active_popup is not None:
            _active_popup._close()
            return

        _active_popup = self

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg=POPUP_BORDER)
        self.root.attributes("-topmost", True)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        # Fenêtre transparente plein écran pour détecter les clics en dehors
        self.blocker = tk.Toplevel(self.root)
        self.blocker.overrideredirect(True)
        self.blocker.attributes("-alpha", 0.01)
        self.blocker.attributes("-topmost", True)
        self.blocker.geometry(f"{screen_w}x{screen_h}+0+0")
        self.blocker.bind("<Button-1>", lambda e: self._close())
        self.blocker.bind("<Button-3>", lambda e: self._close())

        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()

        self._build_ui()

        self.root.update_idletasks()
        w = max(self.root.winfo_reqwidth(), 320)
        h = self.root.winfo_reqheight()

        if x + w > screen_w:
            x = screen_w - w - 10
        if y + h > screen_h:
            y = screen_h - h - 10

        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.lift()

        # Bindings clavier
        self.root.bind("<Escape>", lambda e: self._close())
        self.root.bind("<Up>",     lambda e: self._move_focus(-1))
        self.root.bind("<Down>",   lambda e: self._move_focus(1))
        self.root.bind("<Return>", lambda e: self._select_focused())

        self.root.focus_force()
        self.root.mainloop()

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=POPUP_BG, padx=1, pady=1)
        outer.pack(fill="both", expand=True)

        # --- En-tête ---
        header = tk.Frame(outer, bg=POPUP_HEAD_BG)
        header.pack(fill="x")
        tk.Label(
            header, text="📋  Templates",
            bg=POPUP_HEAD_BG, fg=POPUP_FG,
            font=("Segoe UI", 10, "bold"),
            anchor="w", padx=10, pady=6
        ).pack(side="left")
        tk.Label(
            header, text="Ctrl+Shift+Q",
            bg=POPUP_HEAD_BG, fg=POPUP_FG_DIM,
            font=("Segoe UI", 8),
            anchor="e", padx=10
        ).pack(side="right")

        # --- Barre de recherche ---
        search_frame = tk.Frame(outer, bg=POPUP_SEARCH_BG, pady=4)
        search_frame.pack(fill="x", padx=6, pady=(6, 2))
        tk.Label(search_frame, text="🔍", bg=POPUP_SEARCH_BG, fg=POPUP_FG_DIM,
                 font=("Segoe UI", 9)).pack(side="left", padx=(6, 2))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search)
        search_entry = tk.Entry(
            search_frame,
            textvariable=self._search_var,
            bg=POPUP_SEARCH_BG, fg=POPUP_FG,
            insertbackground=POPUP_FG,
            relief="flat",
            font=("Segoe UI", 9),
            bd=0
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Frame(outer, bg=POPUP_BORDER, height=1).pack(fill="x", padx=6)

        # --- Liste scrollable ---
        self._list_container = tk.Frame(outer, bg=POPUP_BG)
        self._list_container.pack(fill="both", expand=True)
        self._build_list()

        tk.Frame(outer, bg=POPUP_BORDER, height=1).pack(fill="x", padx=6, pady=(4, 0))

        # --- Bouton Gérer ---
        manage_btn = tk.Label(
            outer,
            text="⚙  Gérer les templates",
            bg=POPUP_BTN_BG, fg=POPUP_FG,
            font=("Segoe UI", 9),
            anchor="center", pady=7, cursor="hand2"
        )
        manage_btn.pack(fill="x", padx=6, pady=6)
        manage_btn.bind("<Button-1>", lambda e: self._open_manager())
        manage_btn.bind("<Enter>", lambda e: manage_btn.configure(bg="#254a7a"))
        manage_btn.bind("<Leave>", lambda e: manage_btn.configure(bg=POPUP_BTN_BG))

    def _build_list(self):
        # Vider
        for w in self._list_container.winfo_children():
            w.destroy()
        self.item_frames = []

        if not self.filtered:
            tk.Label(
                self._list_container,
                text="Aucun résultat",
                bg=POPUP_BG, fg=POPUP_FG_DIM,
                font=("Segoe UI", 9), pady=12
            ).pack()
            return

        # Canvas scrollable
        item_h = 48  # hauteur estimée par item
        max_h = self.MAX_VISIBLE * item_h
        total_h = len(self.filtered) * item_h
        canvas_h = min(total_h, max_h)

        self._canvas = tk.Canvas(
            self._list_container,
            bg=POPUP_BG, highlightthickness=0,
            height=canvas_h
        )
        scrollbar = tk.Scrollbar(self._list_container, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        if total_h > max_h:
            scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg=POPUP_BG)
        canvas_window = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", lambda e: self._canvas.configure(
            scrollregion=self._canvas.bbox("all")
        ))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(
            canvas_window, width=e.width
        ))
        self._canvas.bind("<MouseWheel>", lambda e: self._canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        for i, template in enumerate(self.filtered):
            self._add_item(i, template)

        if self.focused_idx >= len(self.filtered):
            self.focused_idx = 0
        self._highlight(self.focused_idx)

    def _add_item(self, idx, template):
        name = template.get("name", "Sans titre")
        content = template.get("content", "")
        preview = content[:70].replace("\n", " ")
        if len(content) > 70:
            preview += "..."

        frame = tk.Frame(self._inner, bg=POPUP_BG, cursor="hand2")
        frame.pack(fill="x", pady=1, padx=4)

        tk.Label(
            frame, text=name,
            bg=POPUP_BG, fg=POPUP_FG,
            font=("Segoe UI", 10, "bold"),
            anchor="w", padx=10, pady=3
        ).pack(fill="x")

        if preview:
            tk.Label(
                frame, text=preview,
                bg=POPUP_BG, fg=POPUP_FG_DIM,
                font=("Segoe UI", 8),
                anchor="w", padx=10, pady=0
            ).pack(fill="x")

        tk.Frame(self._inner, bg=POPUP_BORDER, height=1).pack(fill="x", padx=10)

        self.item_frames.append(frame)

        def on_enter(e, i=idx):
            self._highlight(i)

        def on_click(e, t=template):
            self._select_template(t["content"])

        frame.bind("<Enter>", on_enter)
        frame.bind("<Button-1>", on_click)
        for child in frame.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Button-1>", on_click)

    def _highlight(self, idx):
        self.focused_idx = idx
        for i, frame in enumerate(self.item_frames):
            color = POPUP_BG_HOVER if i == idx else POPUP_BG
            frame.configure(bg=color)
            for child in frame.winfo_children():
                child.configure(bg=color)

    def _move_focus(self, direction):
        if not self.item_frames:
            return
        new_idx = (self.focused_idx + direction) % len(self.filtered)
        self._highlight(new_idx)
        # Scroll pour garder l'item visible
        if self._canvas:
            self._canvas.yview_moveto(new_idx / max(len(self.filtered), 1))

    def _select_focused(self):
        if self.filtered and 0 <= self.focused_idx < len(self.filtered):
            self._select_template(self.filtered[self.focused_idx]["content"])

    def _on_search(self, *_):
        query = self._search_var.get().lower()
        self.filtered = [t for t in self.all_templates if query in t["name"].lower() or query in t.get("content", "").lower()]
        self.focused_idx = 0
        self._build_list()

    def _open_manager(self):
        self._close()
        def _open():
            manager = TemplateManager()
            manager.run()
        threading.Thread(target=_open, daemon=True).start()

    def _select_template(self, content):
        self._close()

        def paste():
            time.sleep(0.15)
            try:
                import pyperclip
                pyperclip.copy(content)
            except ImportError:
                import subprocess
                subprocess.run(["clip"], input=content.encode("utf-16"), check=True)
            try:
                import pyautogui
                pyautogui.hotkey("ctrl", "v")
            except ImportError:
                pass

        threading.Thread(target=paste, daemon=True).start()

    def _close(self):
        global _active_popup
        _active_popup = None
        for attr in ("blocker", "root"):
            w = getattr(self, attr, None)
            if w:
                try:
                    w.destroy()
                except Exception:
                    pass
                setattr(self, attr, None)


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

        # Thème ttk moderne
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 9), padding=5)
        style.configure("Accent.TButton", font=("Segoe UI", 9, "bold"), padding=5)
        style.configure("TLabel", font=("Segoe UI", 9))
        style.configure("TLabelframe.Label", font=("Segoe UI", 9, "bold"))

        self.title("Gestionnaire de Templates")
        self.geometry("720x500")
        self.minsize(580, 400)
        self.resizable(True, True)
        self.templates = load_templates()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # --- Zone principale ---
        main = tk.Frame(self, bg="#f0f0f0")
        main.pack(fill="both", expand=True, padx=12, pady=12)

        # --- Colonne gauche : liste ---
        left = ttk.LabelFrame(main, text=" Liste des templates ")
        left.pack(fill="both", expand=True, side="left", padx=(0, 6))

        sb = ttk.Scrollbar(left)
        sb.pack(side="right", fill="y")
        self.listbox = tk.Listbox(
            left,
            yscrollcommand=sb.set,
            selectmode="single",
            font=("Segoe UI", 10),
            width=22,
            relief="flat",
            bg="white",
            selectbackground="#4a90d9",
            selectforeground="white",
            activestyle="none",
        )
        self.listbox.pack(fill="both", expand=True, padx=4, pady=4)
        sb.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.bind("<Double-Button-1>", lambda e: self._edit_template())

        # Boutons sous la liste
        btn_row = tk.Frame(left, bg="#f0f0f0")
        btn_row.pack(fill="x", padx=4, pady=(0, 4))
        ttk.Button(btn_row, text="➕ Nouveau",   command=self._new_template).pack(side="left", padx=2)
        ttk.Button(btn_row, text="✏️ Modifier",  command=self._edit_template).pack(side="left", padx=2)
        ttk.Button(btn_row, text="🗑️ Supprimer", command=self._delete_template).pack(side="left", padx=2)
        ttk.Button(btn_row, text="⬆",            command=self._move_up,   width=3).pack(side="right", padx=1)
        ttk.Button(btn_row, text="⬇",            command=self._move_down, width=3).pack(side="right", padx=1)

        # --- Colonne droite : aperçu ---
        right = ttk.LabelFrame(main, text=" Aperçu du contenu ")
        right.pack(fill="both", expand=True, side="left")

        self.preview_text = tk.Text(
            right,
            font=("Segoe UI", 10),
            wrap="word",
            relief="flat",
            bg="white",
            state="disabled",
            padx=8, pady=8
        )
        preview_sb = ttk.Scrollbar(right, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=preview_sb.set)
        preview_sb.pack(side="right", fill="y")
        self.preview_text.pack(fill="both", expand=True, padx=4, pady=4)

        # --- Barre du bas : menu clic droit ---
        bottom = ttk.LabelFrame(self, text=" Menu contextuel Windows (clic droit bureau) ")
        bottom.pack(fill="x", padx=12, pady=(0, 12))

        inner = tk.Frame(bottom)
        inner.pack(fill="x", padx=8, pady=6)

        self.ctx_status_var = tk.StringVar()
        ttk.Label(inner, textvariable=self.ctx_status_var).pack(side="left", padx=(0, 12))
        self.ctx_btn = ttk.Button(inner, text="", command=self._toggle_context_menu, width=28)
        self.ctx_btn.pack(side="left")

        self._refresh_ctx_status()
        self._refresh_list()

    def _refresh_list(self, select_index=None):
        self.listbox.delete(0, "end")
        for t in self.templates:
            self.listbox.insert("end", f"  {t['name']}")
        if select_index is not None:
            self.listbox.selection_set(select_index)
            self.listbox.see(select_index)
            self._update_preview(select_index)

    def _on_select(self, event):
        idx = self._get_selected_index()
        if idx is not None:
            self._update_preview(idx)

    def _update_preview(self, idx):
        content = self.templates[idx].get("content", "") if idx < len(self.templates) else ""
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", content)
        self.preview_text.configure(state="disabled")

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
            messagebox.showinfo("Info", "Sélectionnez un template à modifier.", parent=self)
            return
        dialog = TemplateDialog(self, title="Modifier le template", template=self.templates[idx])
        if dialog.result:
            self.templates[idx] = dialog.result
            save_templates(self.templates)
            self._refresh_list(idx)

    def _delete_template(self):
        idx = self._get_selected_index()
        if idx is None:
            messagebox.showinfo("Info", "Sélectionnez un template à supprimer.", parent=self)
            return
        name = self.templates[idx]["name"]
        if messagebox.askyesno("Confirmer", f'Supprimer le template "{name}" ?', parent=self):
            del self.templates[idx]
            save_templates(self.templates)
            new_idx = min(idx, len(self.templates) - 1) if self.templates else None
            self._refresh_list(new_idx)
            if new_idx is None:
                self.preview_text.configure(state="normal")
                self.preview_text.delete("1.0", "end")
                self.preview_text.configure(state="disabled")

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
            self.ctx_status_var.set("✅  Installé")
            self.ctx_btn.configure(text="Désinstaller le menu clic droit")
        else:
            self.ctx_status_var.set("❌  Non installé")
            self.ctx_btn.configure(text="Installer le menu clic droit")

    def _toggle_context_menu(self):
        if is_context_menu_installed():
            if uninstall_context_menu():
                messagebox.showinfo("Succès", "Menu contextuel désinstallé.", parent=self)
        else:
            if install_context_menu():
                messagebox.showinfo(
                    "Succès",
                    'Menu contextuel installé !\n\nFaites un clic droit sur le bureau\npour voir l\'entrée "Coller un template..."',
                    parent=self
                )
        self._refresh_ctx_status()

    def _on_close(self):
        self.destroy()
        try:
            self._root.destroy()
        except Exception:
            pass

    def run(self):
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
        self.geometry("520x380")
        self.minsize(400, 300)
        self.transient(parent)
        self.grab_set()
        self.wait_window()

    def _build_ui(self):
        frame = tk.Frame(self, padx=15, pady=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Nom du template :").pack(anchor="w")
        self.name_var = tk.StringVar(value=self._template["name"])
        ttk.Entry(frame, textvariable=self.name_var, font=("Segoe UI", 10)).pack(fill="x", pady=(2, 10))

        ttk.Label(frame, text="Contenu :").pack(anchor="w")
        text_frame = tk.Frame(frame)
        text_frame.pack(fill="both", expand=True, pady=(2, 0))
        sb = ttk.Scrollbar(text_frame)
        sb.pack(side="right", fill="y")
        self.content_text = tk.Text(
            text_frame,
            font=("Segoe UI", 10), wrap="word",
            yscrollcommand=sb.set, relief="solid", bd=1
        )
        sb.config(command=self.content_text.yview)
        self.content_text.pack(fill="both", expand=True)
        self.content_text.insert("1.0", self._template["content"])

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="Annuler",      command=self.destroy,  width=10).pack(side="right", padx=(4, 0))
        ttk.Button(btn_frame, text="💾 Enregistrer", command=self._save,  width=14).pack(side="right")

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
        threading.Thread(target=hotkey_handler, daemon=True).start()

    def toggle_ctx(icon, item):
        if is_context_menu_installed():
            uninstall_context_menu()
        else:
            install_context_menu()
        icon.update_menu()

    def ctx_menu_label(item):
        return "Désinstaller menu clic droit" if is_context_menu_installed() else "Installer menu clic droit"

    def quit_app(icon, item):
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Coller un template...  (Ctrl+Shift+Q)", open_popup),
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
        popup = TemplatePopup()
        popup.show()
    elif "--manage" in sys.argv:
        manager = TemplateManager()
        manager.run()
    else:
        run_tray()


if __name__ == "__main__":
    main()
