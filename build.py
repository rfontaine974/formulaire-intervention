"""
Script de build - Template Manager
===================================
Génère dist/TemplateManager.exe via PyInstaller.

Usage :
  python build.py
"""

import sys
import os
import subprocess
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(ROOT, "assets")
ICON_PATH = os.path.join(ASSETS_DIR, "icon.ico")
DIST_DIR = os.path.join(ROOT, "dist")
BUILD_DIR = os.path.join(ROOT, "build")


def ensure_pyinstaller():
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} déjà installé.")
    except ImportError:
        print("📦 Installation de PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installé.")


def generate_icon():
    """Génère assets/icon.ico avec Pillow."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        from PIL import Image, ImageDraw, ImageFont

    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        margin = max(1, size // 16)
        radius = max(2, size // 5)
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=radius,
            fill="#4a90d9"
        )
        font_size = int(size * 0.55)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        # Centrer le "T"
        bbox = draw.textbbox((0, 0), "T", font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx = (size - tw) // 2 - bbox[0]
        ty = (size - th) // 2 - bbox[1] - max(1, size // 16)
        draw.text((tx, ty), "T", fill="white", font=font)
        images.append(img)

    images[0].save(ICON_PATH, format="ICO", sizes=[(s, s) for s in sizes], append_images=images[1:])
    print(f"✅ Icône générée : {ICON_PATH}")


def build_exe():
    """Lance PyInstaller pour créer l'exe."""
    print("\n🔨 Compilation avec PyInstaller...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "TemplateManager",
        "--icon", ICON_PATH,
        "--add-data", f"{os.path.join(ROOT, 'templates.json')};." if os.path.exists(os.path.join(ROOT, "templates.json")) else ".",
        "--clean",
        os.path.join(ROOT, "clipboard_app.py"),
    ]

    # Supprimer --add-data si templates.json absent (sera créé au 1er lancement)
    if not os.path.exists(os.path.join(ROOT, "templates.json")):
        cmd = [c for c in cmd if "templates.json" not in c and c != "."]

    result = subprocess.run(cmd, cwd=ROOT)

    if result.returncode == 0:
        exe_path = os.path.join(DIST_DIR, "TemplateManager.exe")
        print(f"\n✅ Compilation réussie !")
        print(f"   → {exe_path}")
        print(f"\nProchaine étape : compiler installer.iss avec Inno Setup")
        print(f"   Inno Setup : https://jrsoftware.org/isdl.php")
    else:
        print("\n❌ Erreur lors de la compilation.")
        sys.exit(1)


def check_inno_setup():
    """Vérifie si Inno Setup est installé et affiche des instructions."""
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
    ]
    for path in inno_paths:
        if os.path.exists(path):
            return path
    return None


def main():
    print("=" * 50)
    print("  Template Manager - Script de Build")
    print("=" * 50)

    ensure_pyinstaller()
    generate_icon()
    build_exe()

    print("\n" + "=" * 50)
    inno = check_inno_setup()
    if inno:
        print(f"✅ Inno Setup détecté : {inno}")
        print(f"\nPour créer le setup.exe :")
        print(f'  "{inno}" installer.iss')
        print(f"  → Output/setup_TemplateManager.exe")

        compile_now = input("\nVoulez-vous compiler l'installeur maintenant ? (o/n) : ").strip().lower()
        if compile_now == "o":
            iss_path = os.path.join(ROOT, "installer.iss")
            result = subprocess.run([inno, iss_path])
            if result.returncode == 0:
                print("\n✅ Installeur créé : Output/setup_TemplateManager.exe")
            else:
                print("\n❌ Erreur lors de la création de l'installeur.")
    else:
        print("ℹ️  Inno Setup non détecté.")
        print("   Pour créer un vrai installeur Windows :")
        print("   1. Téléchargez Inno Setup : https://jrsoftware.org/isdl.php")
        print("   2. Installez-le")
        print("   3. Relancez ce script, ou compilez installer.iss manuellement")
        print("\n   En attendant, vous pouvez utiliser directement :")
        print(f"   dist/TemplateManager.exe  (portable, aucune installation requise)")


if __name__ == "__main__":
    main()
