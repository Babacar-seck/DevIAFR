#!/bin/bash

# Script de démarrage pour l'interface web DevIAFR
# Lance le backend (FastAPI) et le frontend (Next.js) en parallèle

set -e

echo "🚀 Démarrage de l'interface web DevIAFR..."
echo ""

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier que Python est disponible
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python 3 n'est pas installé${NC}"
    exit 1
fi

# Vérifier que Node.js est disponible
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js n'est pas installé${NC}"
    exit 1
fi

# Chemins
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$PROJECT_DIR/api"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Fonction de nettoyage
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Arrêt des services...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Capturer Ctrl+C
trap cleanup SIGINT SIGTERM

# ===== BACKEND =====
echo -e "${BLUE}📦 Configuration du backend...${NC}"

cd "$API_DIR"

# Créer le venv si nécessaire
if [ ! -d ".venv" ]; then
    echo "   Création du virtual environment..."
    python3 -m venv .venv
fi

# Utiliser le venv MPT (déjà configuré avec FastAPI/Pydantic)
MPT_VENV="$HOME/MyWorkProjectGithub/MoneyPrinterTurbo/.venv"
if [ ! -d "$MPT_VENV" ]; then
    echo "   ⚠️  Venv MPT non trouvé, création d'un venv local..."
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -q -r requirements.txt
        touch .venv/.installed
    else
        source .venv/bin/activate
    fi
else
    echo "   Utilisation du venv MPT (FastAPI/Pydantic déjà installés)"
    PYTHON_BIN="$MPT_VENV/bin/python"
fi

echo -e "${GREEN}✓ Backend prêt${NC}"
echo ""

# ===== FRONTEND =====
echo -e "${BLUE}📦 Configuration du frontend...${NC}"

cd "$FRONTEND_DIR"

# Installer les dépendances si nécessaire
if [ ! -d "node_modules" ]; then
    echo "   Installation des dépendances Node.js..."
    npm install
fi

echo -e "${GREEN}✓ Frontend prêt${NC}"
echo ""

# ===== DÉMARRAGE =====
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 Démarrage des services...${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Démarrer le backend
cd "$API_DIR"
if [ ! -z "$PYTHON_BIN" ]; then
    "$PYTHON_BIN" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
else
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
fi
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend démarré${NC} (PID: $BACKEND_PID)"
echo -e "  ${BLUE}→ API Docs:${NC} http://localhost:8000/docs"
echo -e "  ${BLUE}→ Health:${NC}   http://localhost:8000/health"
echo ""

# Attendre que le backend soit prêt
sleep 2

# Démarrer le frontend
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓ Frontend démarré${NC} (PID: $FRONTEND_PID)"
echo -e "  ${BLUE}→ App:${NC}      http://localhost:3000"
echo ""

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Interface web DevIAFR prête !${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Appuyer sur ${YELLOW}Ctrl+C${NC} pour arrêter"
echo ""

# Attendre que les processus se terminent
wait
