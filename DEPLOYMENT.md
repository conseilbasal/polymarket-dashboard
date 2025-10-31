# Déploiement du Dashboard Polymarket Copy Trading

Ce guide explique comment déployer le backend sur Railway et le frontend sur Vercel.

## Architecture

- **Backend (Railway)**: API FastAPI avec scheduler automatique + PostgreSQL
- **Frontend (Vercel)**: Application React statique
- **Coût estimé**: $2-3/mois (bien en dessous de la limite de $5/mois)

## Prérequis

1. Compte Railway: https://railway.app/
2. Compte Vercel: https://vercel.com/
3. Compte GitHub (pour connecter les repos)

---

## 🚀 Déploiement Backend sur Railway

### 1. Créer un nouveau projet Railway

1. Aller sur https://railway.app/new
2. Cliquer sur "Deploy from GitHub repo"
3. Connecter votre dépôt GitHub contenant ce code
4. Railway détectera automatiquement Python et utilisera le Procfile

### 2. Ajouter PostgreSQL

1. Dans votre projet Railway, cliquer sur "+ New"
2. Sélectionner "Database" > "Add PostgreSQL"
3. Railway créera automatiquement la variable DATABASE_URL

### 3. Configurer les variables d'environnement

Dans Railway > Variables, ajouter:

```
SECRET_KEY=<générer avec: openssl rand -hex 32>
APP_PASSWORD=<votre-mot-de-passe-sécurisé>
FETCH_INTERVAL_MINUTES=5
FRONTEND_URL=https://votre-app.vercel.app
```

### 4. Vérifier le déploiement

Railway déploiera automatiquement. Vérifier les logs pour:
- `[SCHEDULER] Scheduler started - will fetch every 5 minutes`
- `Application startup complete`

---

## ✅ Résumé

Tous les fichiers de configuration Railway sont prêts:
- ✅ Procfile
- ✅ railway.json  
- ✅ requirements.txt
- ✅ database.py (PostgreSQL ready)
- ✅ scheduler.py (automatic data fetching)
- ✅ auth.py (password protection)

**Prochaines étapes**: Déployer sur Railway et configurer les variables d'environnement.
