#!/bin/bash
# Script de développement — lance backend + frontend en parallèle

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Démarrage DevIAFR..."
echo ""

# Vérifier que le venv API existe
if [ ! -d "$PROJECT_DIR/api/.venv" ]; then
    echo "📦 Création du venv API..."
    cd "$PROJECT_DIR/api"
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    cd "$PROJECT_DIR"
fi

# Lancer backend
echo "🔧 Démarrage backend FastAPI (port 8000)..."
cd "$PROJECT_DIR/api"
.venv/bin/uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd "$PROJECT_DIR"

# Lancer frontend
echo "🎨 Démarrage frontend Next.js (port 3000)..."
cd "$PROJECT_DIR/frontend"

if [ ! -d "node_modules" ]; then
    echo "📦 Installation dépendances frontend..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
cd "$PROJECT_DIR"

echo ""
echo "✅ DevIAFR démarré !"
echo ""
echo "  Backend:  http://localhost:8000"
echo "  Docs:     http://localhost:8000/docs"
echo "  Frontend: http://localhost:3000"
echo ""
echo "Appuyer sur Ctrl+C pour arrêter"
echo ""

# Capturer Ctrl+C
trap "echo ''; echo '🛑 Arrêt...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

# Attendre
wait
