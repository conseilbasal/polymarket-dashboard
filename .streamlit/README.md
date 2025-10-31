# Déploiement Streamlit Cloud

## 📊 Dashboard Polymarket Copy Trading

Ce dashboard Streamlit se connecte à l'API Railway pour afficher les données de trading.

---

## 🚀 Étapes de Déploiement

### 1. Déployer sur Streamlit Cloud

1. Allez sur: https://share.streamlit.io
2. Cliquez sur "New app"
3. Sélectionnez:
   - **Repository**: conseilbasal/polymarket-dashboard
   - **Branch**: main  
   - **Main file**: dashboard/app_copy_trading.py
4. Cliquez sur "Advanced settings"

### 2. Configurer les Secrets

Dans "Advanced settings", section "Secrets", ajoutez:

```toml
[api]
url = "https://web-production-62f43.up.railway.app"
password = "votre-mot-de-passe-railway"
```

Remplacez:
- `url` par l'URL de votre backend Railway
- `password` par la valeur de APP_PASSWORD configurée sur Railway

### 3. Déployer

Cliquez sur "Deploy"! Streamlit va:
- Installer les dépendances depuis `dashboard/requirements.txt`
- Lancer l'application
- Vous donner une URL type: `https://votre-app.streamlit.app`

---

## 🔧 Pour le Développement Local

1. Copiez `.streamlit/secrets.toml.example` vers `.streamlit/secrets.toml`
2. Remplissez vos valeurs dans `secrets.toml`
3. Lancez: `streamlit run dashboard/app_copy_trading.py`

---

## ⚠️ Important

- **NE COMMITEZ JAMAIS** le fichier `.streamlit/secrets.toml`
- Il contient votre mot de passe API
- Il est déjà dans `.gitignore`

---

## 📝 URL du Dashboard

Une fois déployé: **https://polymarket-dashboard.streamlit.app**
