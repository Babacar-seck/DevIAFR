# 🌐 Interface Web DevIAFR

Interface web complète pour la production vidéo automatisée avec personas.

## 🚀 Démarrage rapide

### Prérequis
- Node.js 18+
- Python 3.9+
- Le venv MPT (`~/MyWorkProjectGithub/MoneyPrinterTurbo/.venv`)

### Installation et lancement

```bash
cd DevIAFR
./start-web.sh
```

Ce script :
1. Installe les dépendances Node.js du frontend
2. Utilise le venv MPT pour le backend (FastAPI/Pydantic déjà installés)
3. Lance le backend sur http://localhost:8000
4. Lance le frontend sur http://localhost:3000

## 📖 Utilisation

### 1. Accéder à l'interface
Ouvrir http://localhost:3000 dans votre navigateur

### 2. Créer un persona
- Cliquer sur "Personas" dans le menu
- Cliquer sur "Nouveau Persona"
- Remplir le formulaire (nom, niche, langue, etc.)
- Cliquer sur "Créer"

### 3. Produire une vidéo
- Cliquer sur "Production" dans le menu
- Sélectionner un persona
- Entrer le sujet de la vidéo
- Cliquer sur "Produire"
- Attendre la génération (script + vidéo + thumbnail)
- Télécharger depuis le dashboard

## 🏗️ Architecture

```
DevIAFR/
├── api/                    # Backend FastAPI
│   ├── main.py            # Point d'entrée
│   ├── routers/
│   │   ├── personas.py    # CRUD personas
│   │   └── videos.py      # Production/téléchargement vidéos
│   ├── models/
│   │   └── schemas.py     # Modèles Pydantic
│   └── requirements.txt   # Dépendances Python
│
├── frontend/              # Frontend Next.js
│   ├── app/              # Pages (App Router)
│   │   ├── dashboard/    # Vue d'ensemble + vidéos
│   │   ├── personas/     # Liste + création/édition
│   │   ├── production/   # Production de vidéos
│   │   └── videos/       # Liste des vidéos
│   ├── components/       # Composants réutilisables
│   └── lib/
│       └── api.ts        # Client API
│
└── start-web.sh          # Script de démarrage
```

## 🎯 Fonctionnalités

### Backend (FastAPI)
- ✅ 5 endpoints pour gérer les personas (CRUD)
- ✅ 8 endpoints pour produire/télécharger des vidéos
- ✅ CORS configuré pour le frontend
- ✅ Swagger UI disponible sur /docs

### Frontend (Next.js)
- ✅ Dashboard avec statistiques et vidéos récentes
- ✅ Liste et édition des personas
- ✅ Formulaire de création de persona
- ✅ Interface de production vidéo avec preview
- ✅ Téléchargement de vidéos/scripts/thumbnails
- ✅ Design responsive avec Tailwind CSS

## 🔧 Développement

### Lancer manuellement

**Backend :**
```bash
cd api
~/MyWorkProjectGithub/MoneyPrinterTurbo/.venv/bin/python -m uvicorn main:app --reload --port 8000
```

**Frontend :**
```bash
cd frontend
npm run dev
```

### Tester l'API

```bash
# Liste des personas
curl http://localhost:8000/api/personas

# Créer un persona
curl -X POST http://localhost:8000/api/personas \
  -H "Content-Type: application/json" \
  -d '{"id": "test", "name": "Test", "niche": "Tech", "language": "fr"}'

# Produire une vidéo
curl -X POST http://localhost:8000/api/videos/generate \
  -H "Content-Type: application/json" \
  -d '{"persona_id": "test", "subject": "Test vidéo", "dry_run": true}'
```

## 📝 Notes

- Le backend utilise le venv MPT pour éviter les conflits de dépendances
- Les vidéos sont stockées dans `/tmp/deviafr_web/videos/`
- Les personas sont stockés dans `config/personas/` (YAML)
- Le mode "dry_run" permet de tester sans générer de vidéo complète

## 🎉 Statut

**Tous les 9 issues WEB-* sont terminés :**
- ✅ WEB-01: Setup FastAPI backend
- ✅ WEB-02: API CRUD personas
- ✅ WEB-03: API production vidéo
- ✅ WEB-04: API téléchargement et statut
- ✅ WEB-05: Setup Next.js frontend
- ✅ WEB-06: Dashboard
- ✅ WEB-07: Éditeur de persona
- ✅ WEB-08: Page production vidéo
- ✅ WEB-09: Intégration et tests

## 🚀 Prochaines étapes (Option A)

Pour transformer DevIAFR en SaaS sans auth ni queue :
1. Ajouter un système de paiement (Stripe)
2. Créer des plans d'abonnement
3. Ajouter un système de quotas par utilisateur
4. Déployer sur une plateforme (Vercel + Railway/Fly.io)

Voir les issues #1, #5-10 pour plus de détails.
