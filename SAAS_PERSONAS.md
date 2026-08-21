# 🎭 Système Multi-Persona & SaaS

Ce pipeline supporte **3 niveaux de personnalisation** pour transformer ton outil en SaaS multi-chaînes.

---

## 📋 Niveau 1 : Personas YAML (Configuration locale)

Chaque chaîne a son propre fichier persona dans `config/personas/`.

### Personas disponibles

```bash
python scripts/select_persona.py --list
```

**6 personas pré-configurés :**

| ID | Nom | Niche | CPM estimé |
|---|---|---|---|
| `dev_ia_fr` | Dev IA FR | Tech/AI pour devs | $15-30 |
| `finance_par_age` | Finance Par Âge | Finance personnelle | $8-20 |
| `psy_stick_fr` | Psy Stick FR | Psychologie | $4-10 |
| `coran_lumiere_fr` | Coran Lumière FR | Spiritualité | $2-5 |
| `mini_melodies_fr` | Mini Mélodies FR | Enfants (COPPA) | $1-3 |
| `motivation_fr` | Motivation FR | Motivation | $3-8 |

### Utiliser un persona

```bash
# Charger un persona seul
python scripts/select_persona.py --persona dev_ia_fr

# Fusionner avec unified_config.yaml
python scripts/select_persona.py --persona finance_par_age --merge

# Sauvegarder la config fusionnée
python scripts/select_persona.py --persona psy_stick_fr --merge --output config/final_config.yaml
```

### Créer un nouveau persona

1. Copie `config/personas/dev_ia_fr.yaml` vers `config/personas/mon_nouveau_persona.yaml`
2. Modifie les champs :
   - `name`, `id`, `channel.name`, `channel.handle`
   - `branding.colors` (palette de couleurs)
   - `voice.voice_id` (ElevenLabs custom)
   - `script.storytelling.structure` (structure narrative)
   - `content.topics` (sujets traités)
   - `quality.min_score` (score minimum)

3. Teste :
```bash
python scripts/select_persona.py --list
```

---

## 🔌 Niveau 2 : API REST (SaaS multi-tenant)

Expose le pipeline via une API FastAPI pour permettre aux clients de créer leurs propres chaînes.

### Architecture SaaS

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React/Next.js)                               │
│  - Dashboard client                                     │
│  - Éditeur de persona visuel                            │
│  - Upload voix ElevenLabs                               │
│  - Suivi production vidéo                               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  API FastAPI (Python)                                   │
│  - POST /personas (créer un persona)                    │
│  - POST /videos (générer une vidéo)                     │
│  - GET /videos/{id}/status (suivre production)          │
│  - POST /upload (publier sur YouTube)                   │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  PostgreSQL (Base de données)                           │
│  - users (clients SaaS)                                 │
│  - personas (configs personnalisées)                    │
│  - videos (historique production)                       │
│  - quotas (vidéos restantes)                            │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  Workers Celery (Production async)                      │
│  - Script generation (qwen3.7-max)                      │
│  - Video rendering (MPT + TST)                          │
│  - Upload YouTube/TikTok                                │
└─────────────────────────────────────────────────────────┘
```

### Schéma de base de données

```sql
-- Table des utilisateurs (clients SaaS)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',  -- free | pro | enterprise
    quota_videos_remaining INT DEFAULT 5,
    quota_reset_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table des personas (configs personnalisées)
CREATE TABLE personas (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    config JSONB NOT NULL,  -- YAML converti en JSON
    voice_id VARCHAR(255),  -- ElevenLabs voice ID
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table des vidéos produites
CREATE TABLE videos (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    persona_id UUID REFERENCES personas(id),
    title VARCHAR(255) NOT NULL,
    script TEXT,
    video_url VARCHAR(500),
    thumbnail_url VARCHAR(500),
    status VARCHAR(50) DEFAULT 'pending',  -- pending | generating | ready | uploaded | failed
    quality_score INT,
    youtube_video_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    uploaded_at TIMESTAMP
);

-- Index pour les requêtes fréquentes
CREATE INDEX idx_videos_user_id ON videos(user_id);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_personas_user_id ON personas(user_id);
```

### Plans de tarification

| Plan | Prix/mois | Vidéos/mois | Personas | Features |
|---|---|---|---|---|
| **Free** | $0 | 5 | 1 | Scripts uniquement, pas de vidéo |
| **Pro** | $49 | 50 | 3 | Vidéos 1080p, upload auto, analytics |
| **Enterprise** | $199 | 200 | 10 | 4K, API illimitée, support prioritaire |

---

## 🚀 Niveau 3 : SaaS complet (Déploiement)

### Stack technique

- **Backend** : FastAPI + Celery + Redis
- **Frontend** : Next.js + Tailwind CSS
- **Database** : PostgreSQL (Supabase)
- **Storage** : AWS S3 / Cloudflare R2
- **Queue** : Redis + Celery workers
- **Auth** : Clerk / Auth0
- **Payments** : Stripe

### Déploiement

```bash
# Docker Compose pour le SaaS
docker-compose up -d

# Services :
# - api (FastAPI, port 8000)
# - worker (Celery, production vidéo)
# - db (PostgreSQL)
# - redis (queue)
# - frontend (Next.js, port 3000)
```

### Exemple d'API endpoint

```python
# api/personas.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import User, Persona
from schemas import PersonaCreate, PersonaResponse

router = APIRouter()

@router.post("/personas", response_model=PersonaResponse)
async def create_persona(
    persona: PersonaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crée un nouveau persona pour l'utilisateur connecté."""
    
    # Vérifier le quota
    if current_user.plan == 'free' and db.query(Persona).filter_by(user_id=current_user.id).count() >= 1:
        raise HTTPException(403, "Plan Free limité à 1 persona. Upgrade vers Pro.")
    
    # Sauvegarder le persona
    db_persona = Persona(
        user_id=current_user.id,
        name=persona.name,
        config=persona.config.dict()
    )
    db.add(db_persona)
    db.commit()
    db.refresh(db_persona)
    
    return db_persona

@router.post("/videos/generate")
async def generate_video(
    request: VideoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Génère une vidéo avec le persona sélectionné."""
    
    # Vérifier le quota
    if current_user.quota_videos_remaining <= 0:
        raise HTTPException(403, "Quota vidéos épuisé. Upgrade ou attends le reset.")
    
    # Récupérer le persona
    persona = db.query(Persona).filter_by(
        id=request.persona_id,
        user_id=current_user.id
    ).first()
    
    if not persona:
        raise HTTPException(404, "Persona introuvable")
    
    # Créer le job Celery
    from tasks import generate_video_task
    task = generate_video_task.delay(
        persona_config=persona.config,
        subject=request.subject,
        user_id=str(current_user.id)
    )
    
    # Décrémenter le quota
    current_user.quota_videos_remaining -= 1
    db.commit()
    
    return {"task_id": task.id, "status": "queued"}
```

---

## 📊 Exemple : Client crée son persona "Crypto FR"

### 1. Via l'interface web

Le client remplit le formulaire :

```yaml
name: "Crypto FR"
id: "crypto_fr"
channel:
  name: "Crypto FR"
  handle: "@cryptofr"
  slogan: "Comprendre la crypto sans jargon"
  niche: "Cryptomonnaies / Finance"
  language: "fr"

branding:
  colors:
    primary: "#f7931a"  # Bitcoin orange
    accent: "#627eea"   # Ethereum blue

voice:
  engine: "elevenlabs"
  voice_id: "crypto_narrator_fr"
  style: "confident, pédagogique"

script:
  storytelling:
    structure:
      - name: "Hook"
        duration_pct: 5
        description: "News crypto choc ou question provocatrice"
      - name: "Contexte"
        duration_pct: 20
        description: "Pourquoi c'est important maintenant"
      - name: "Analyse"
        duration_pct: 60
        description: "Explication technique simplifiée"
      - name: "Prédiction"
        duration_pct: 10
        description: "Ce qui pourrait se passer"
      - name: "CTA"
        duration_pct: 5
        description: "Rejoins le Discord gratuit"

content:
  topics:
    - "Bitcoin / Ethereum"
    - "DeFi / NFT"
    - "Analyse technique"
    - "Régulation crypto"
  format: "medium-form (8-12 min)"
```

### 2. Upload de la voix ElevenLabs

Le client :
1. Va sur ElevenLabs → Voice Design
2. Crée "Crypto Narrator FR" (voix masculine, 30-40 ans, français)
3. Copie le `voice_id` (ex: `a1b2c3d4e5f6`)
4. Colle dans le formulaire

### 3. Génération automatique

Le système :
1. Sauvegarde le persona dans PostgreSQL
2. Génère un fichier `config/personas/crypto_fr_{user_id}.yaml`
3. Lance la première vidéo de test
4. Envoie un email de confirmation

---

## 🎯 Roadmap SaaS

### Phase 1 : MVP (2-3 mois)

- [x] Système multi-persona YAML
- [ ] API FastAPI (CRUD personas + vidéos)
- [ ] Auth (Clerk / Auth0)
- [ ] Dashboard simple (liste vidéos, download)
- [ ] Payments Stripe (plans Free / Pro)

### Phase 2 : Scale (3-6 mois)

- [ ] Éditeur de persona visuel (drag & drop)
- [ ] Upload voix ElevenLabs intégré
- [ ] Queue Celery + workers scalables
- [ ] Analytics dashboard (vues, RPM, revenus)
- [ ] Plan Enterprise (API illimitée)

### Phase 3 : Features avancées (6-12 mois)

- [ ] A/B testing thumbnails (AI-generated variants)
- [ ] Auto-scheduling (publication optimale selon fuseau horaire)
- [ ] Collaboration (plusieurs users sur un persona)
- [ ] White-label (clients revendent sous leur marque)
- [ ] Marketplace de personas (templates prêts à l'emploi)

---

## 💰 Business Model

### Revenue streams

1. **Abonnements SaaS** : $49-199/mois par client
2. **Revenue share** : 10-20% des revenus YouTube des clients
3. **Templates premium** : $29-99 pour personas pré-configurés
4. **Services** : Coaching, audit de chaîne, optimisation

### Projection (12 mois)

| Mois | Clients Pro | Clients Enterprise | MRR | ARR |
|---|---|---|---|---|
| 1 | 10 | 0 | $490 | $5,880 |
| 3 | 30 | 2 | $1,867 | $22,404 |
| 6 | 80 | 8 | $5,512 | $66,144 |
| 12 | 200 | 25 | $14,775 | $177,300 |

**Objectif an 1 : $177K ARR** (Monthly Recurring Revenue)

---

## 🔐 Sécurité & Conformité

### Données sensibles

- **Clés API ElevenLabs** : Chiffrées en base (AES-256)
- **Tokens YouTube OAuth** : Stockés séparément, rotation auto
- **Scripts clients** : Isolés par user_id (pas de cross-contamination)

### Conformité

- **COPPA** : Flag `made_for_kids` dans chaque persona
- **RGPD** : Droit à l'oubli, export données, consentement cookies
- **YouTube ToS** : Pas de spam, pas de contenu dupliqué, revue humaine obligatoire

---

## 📚 Ressources

- **Documentation API** : `/docs` (Swagger auto-généré)
- **Guide persona** : `docs/persona_guide.md`
- **Templates** : `config/personas/*.yaml`
- **Support** : Discord privé pour clients Pro/Enterprise

---

**Prochaine étape** : Déployer l'API FastAPI et le dashboard React pour lancer le MVP en 2-3 mois.
