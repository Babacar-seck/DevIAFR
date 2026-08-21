# DevIAFR API

Interface web complète pour DevIAFR - Production vidéo automatisée avec personas.

## 🚀 Démarrage rapide

### Installation

```bash
# Backend
cd api
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Lancer l'application

**Option 1 : Script automatique** (recommandé)
```bash
./start-web.sh
```

**Option 2 : Manuellement**
```bash
# Terminal 1 - Backend
cd api
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Accéder à l'application

- **Frontend** : http://localhost:3000
- **API Docs** : http://localhost:8000/docs
- **API Health** : http://localhost:8000/health

## 📖 Utilisation

### 1. Créer un persona

1. Aller dans **Personas** (menu latéral)
2. Cliquer sur **Nouveau persona**
3. Remplir le formulaire :
   - Nom : "Crypto FR"
   - ID : "crypto_fr"
   - Niche : "Cryptomonnaies / Finance"
   - Langue : Français
   - Ton : "pédagogique, dynamique"
   - Qualité minimum : 70/100
4. Cliquer sur **Créer**

### 2. Produire une vidéo

1. Aller dans **Production**
2. Sélectionner un persona
3. Entrer le sujet : "Les 5 erreurs fatales en architecture .NET"
4. Cocher "Mode test" pour générer seulement le script (plus rapide)
5. Cliquer sur **Produire la vidéo**
6. Attendre 5-10 minutes (production synchrone)
7. Télécharger la vidéo générée

### 3. Gérer les vidéos

- **Dashboard** : Vue d'ensemble avec statistiques
- **Vidéos** : Liste complète avec téléchargement/suppression

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (Next.js 14)                                  │
│  - React Server Components                              │
│  - Tailwind CSS                                         │
│  - TypeScript                                           │
│  - App Router                                           │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP REST
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                      │
│  - Python 3.10+                                         │
│  - Pydantic schemas                                     │
│  - CORS configuré                                       │
│  - Swagger UI auto                                      │
└────────────────┬────────────────────────────────────────┘
                 │ subprocess
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Scripts DevIAFR                                        │
│  - humanize_script.py                                   │
│  - unified_pipeline.py                                  │
│  - thumbnail_generator.py                               │
│  - quality_score.py                                     │
└─────────────────────────────────────────────────────────┘
```

## 🔌 Endpoints API

### Personas

```http
GET    /api/personas              # Lister tous les personas
GET    /api/personas/{id}         # Obtenir un persona
POST   /api/personas              # Créer un persona
PUT    /api/personas/{id}         # Modifier un persona
DELETE /api/personas/{id}         # Supprimer un persona
```

### Videos

```http
GET    /api/videos                # Lister toutes les vidéos
GET    /api/videos/stats          # Statistiques globales
POST   /api/videos/generate       # Produire une vidéo
GET    /api/videos/{id}           # Obtenir une vidéo
GET    /api/videos/{id}/download  # Télécharger la vidéo
GET    /api/videos/{id}/script    # Télécharger le script
GET    /api/videos/{id}/thumbnail # Télécharger la miniature
DELETE /api/videos/{id}           # Supprimer une vidéo
```

## 📝 Exemples

### Créer un persona via API

```bash
curl -X POST http://localhost:8000/api/personas \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Crypto FR",
    "id": "crypto_fr",
    "niche": "Cryptomonnaies / Finance",
    "language": "fr",
    "tone": "pédagogique, dynamique",
    "quality_min": 70
  }'
```

### Produire une vidéo via API

```bash
curl -X POST http://localhost:8000/api/videos/generate \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": "dev_ia_fr",
    "subject": "Les 5 erreurs fatales en architecture .NET",
    "dry_run": false
  }'
```

## ⚠️ Limitations

### MVP actuel (sans auth ni queue)

- **Pas d'authentification** : Accès direct, pas de comptes utilisateurs
- **Production synchrone** : Les vidéos sont générées immédiatement (5-10 min)
- **Stockage SQLite local** (`storage/api_videos.db`) : les métadonnées vidéos survivent au redémarrage du backend (contrairement à un stockage en mémoire)
- **Pas de multi-tenant** : Une seule instance pour un seul utilisateur

### Améliorations futures

- [ ] Authentification JWT (login/signup)
- [ ] Queue Celery (production asynchrone)
- [ ] PostgreSQL (persistance des données)
- [ ] Multi-tenant (plusieurs utilisateurs)
- [ ] Stripe (paiements)
- [ ] Upload YouTube automatique
- [ ] Notifications en temps réel (WebSocket)

## 🛠️ Développement

### Structure du projet

```
DevIAFR/
├── api/                      # Backend FastAPI
│   ├── main.py              # Point d'entrée
│   ├── routers/
│   │   ├── personas.py      # CRUD personas
│   │   └── videos.py        # Production vidéos
│   ├── models/
│   │   └── schemas.py       # Pydantic schemas
│   └── requirements.txt
│
├── frontend/                 # Frontend Next.js
│   ├── app/
│   │   ├── layout.tsx       # Layout global
│   │   ├── dashboard/       # Page dashboard
│   │   ├── personas/        # Pages personas
│   │   ├── production/      # Page production
│   │   └── videos/          # Page vidéos
│   ├── components/          # Composants réutilisables
│   ├── lib/
│   │   └── api.ts          # Client API
│   └── package.json
│
├── start-web.sh             # Script de démarrage
└── WEB_INTERFACE.md         # Cette documentation
```

### Variables d'environnement

**Backend** (`api/.env`)
```env
# Optionnel : Configuration personnalisée
PERSONAS_DIR=/path/to/personas
STORAGE_DIR=/path/to/storage
```

**Frontend** (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Tests

```bash
# Backend
cd api
pytest

# Frontend
cd frontend
npm test
```

## 🐛 Dépannage

### Le backend ne démarre pas

```bash
# Vérifier que le venv est activé
which python
# Devrait afficher: /path/to/api/.venv/bin/python

# Réinstaller les dépendances
pip install -r requirements.txt
```

### Erreur CORS

Vérifier que `main.py` contient :
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### La production vidéo échoue

1. Vérifier que MPT est installé : `~/MyWorkProjectGithub/MoneyPrinterTurbo`
2. Vérifier que le venv MPT existe : `~/MyWorkProjectGithub/MoneyPrinterTurbo/.venv`
3. Tester manuellement : `./run.sh --persona dev_ia_fr --subject "Test" --dry-run`

### Les vidéos disparaissent au redémarrage

Ne devrait plus arriver : les métadonnées sont persistées dans `storage/api_videos.db` (SQLite, voir `api/db.py`). Si le problème persiste, vérifier que ce fichier existe et que le process a les droits d'écriture dessus.

## 📚 Ressources

- **Documentation FastAPI** : https://fastapi.tiangolo.com
- **Documentation Next.js** : https://nextjs.org/docs
- **Tailwind CSS** : https://tailwindcss.com/docs
- **DevIAFR Pipeline** : `../RUNBOOK.md`

## 📄 Licence

MIT
