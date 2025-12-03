# 🚀 Déploiement sur Vercel

## Étapes de déploiement :

### 1. **Connecter ton dépôt GitHub à Vercel**
   - Va sur https://vercel.com
   - Clique sur "Sign Up" (ou "Log In" si tu as déjà un compte)
   - Clique sur "Continue with GitHub"
   - Autorise Vercel à accéder à tes dépôts

### 2. **Importer le projet**
   - Dans le dashboard Vercel, clique sur "New Project" ou "Import Project"
   - Sélectionne le dépôt `formulaire-intervention`
   - Vercel devrait détecter automatiquement la configuration

### 3. **Vérifier les paramètres**
   - **Framework**: Python
   - **Build Command**: (laisser vide si vercel.json est présent)
   - **Install Command**: pip install -r requirements.txt
   - Clique sur "Deploy"

### 4. **Voilà ! 🎉**
   - Vercel te génère une URL du type: `https://formulaire-intervention.vercel.app`
   - Ton application est en ligne !

---

## Fichiers créés pour Vercel :

✅ `vercel.json` - Configuration Vercel  
✅ `api/index.py` - Endpoint Flask pour Vercel  
✅ `requirements.txt` - Dépendances Python existantes

---

## Lien pour déployer :

👉 **https://vercel.com/new**

