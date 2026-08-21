#!/bin/bash
# ============================================================================
# run.sh — Point d'entrée principal pour le pipeline DevIAFR
# ============================================================================
# Usage:
#   ./run.sh                          # Mode interactif (choix du persona + sujet)
#   ./run.sh --persona dev_ia_fr      # Lancer avec un persona spécifique
#   ./run.sh --subject "Sujet vidéo"  # Spécifier le sujet directement
#   ./run.sh --dry-run                # Tester sans produire de vidéo
#   ./run.sh --list-personas          # Lister tous les personas disponibles
#   ./run.sh --check                  # Vérifier l'environnement uniquement
#   ./run.sh --help                   # Afficher l'aide
# ============================================================================

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Chemins
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/.."
MPT_DIR="$HOME/MyWorkProjectGithub/MoneyPrinterTurbo"
MPT_VENV="$MPT_DIR/.venv"
MPT_PYTHON="$MPT_VENV/bin/python"
HERMES_ENV="$HOME/.hermes/.env"

# Variables
PERSONA=""
SUBJECT=""
DRY_RUN=false
LIST_PERSONAS=false
CHECK_ONLY=false
SHOW_HELP=false
OUTPUT_DIR="$PROJECT_DIR/storage/output"

# ============================================================================
# Fonctions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

show_help() {
    cat << 'EOF'

🎬 DevIAFR Pipeline Runner

USAGE:
    ./run.sh [OPTIONS]

OPTIONS:
    --persona <id>          Sélectionner un persona (ex: dev_ia_fr, finance_par_age)
    --subject <texte>       Sujet de la vidéo à produire
    --dry-run               Mode test (ne produit pas de vidéo, génère seulement le script)
    --list-personas         Lister tous les personas disponibles
    --check                 Vérifier l'environnement sans lancer le pipeline
    --help                  Afficher cette aide

EXEMPLES:
    # Mode interactif (choix guidé)
    ./run.sh

    # Lancer avec un persona spécifique
    ./run.sh --persona dev_ia_fr --subject "Les secrets de .NET 9"

    # Tester sans produire de vidéo
    ./run.sh --persona finance_par_age --subject "Comment investir à 25 ans" --dry-run

    # Lister les personas
    ./run.sh --list-personas

PERSONAS DISPONIBLES:
    dev_ia_fr              Tech/AI pour devs ($15-30 CPM)
    finance_par_age        Finance par tranche d'âge ($8-20 CPM)
    psy_stick_fr           Psychologie stick figures ($4-10 CPM)
    coran_lumiere_fr       Récitation Coran ($2-5 CPM)
    mini_melodies_fr       Chansons enfants ($1-3 CPM)
    motivation_fr          Motivation quotidienne ($3-8 CPM)

FICHIERS DE CONFIGURATION:
    config/unified_config.yaml           Configuration principale
    config/personas/*.yaml               Personas personnalisés

SORTIE:
    storage/output/                      Vidéos produites
    storage/scripts/                     Scripts générés
    storage/thumbnails/                  Miniatures

DOCUMENTATION:
    PERSONA_GUIDE.md        Guide d'utilisation des personas
    SAAS_PERSONAS.md        Architecture SaaS multi-tenant
    README.md               Documentation complète

EOF
}

check_dependencies() {
    log_info "Vérification des dépendances..."
    
    local all_ok=true
    
    # Python 3
    if command -v python3 &> /dev/null; then
        log_success "Python 3: $(python3 --version)"
    else
        log_error "Python 3 non trouvé"
        all_ok=false
    fi
    
    # FFmpeg
    if command -v ffmpeg &> /dev/null; then
        log_success "FFmpeg: $(ffmpeg -version 2>&1 | head -n1 | awk '{print $3}')"
    else
        log_error "FFmpeg non trouvé (requis pour le traitement vidéo)"
        all_ok=false
    fi
    
    # MPT venv
    if [ -f "$MPT_PYTHON" ]; then
        log_success "MPT venv: $MPT_PYTHON"
    else
        log_error "MPT venv non trouvé: $MPT_PYTHON"
        log_warn "Installer MPT: cd ~/MyWorkProjectGithub/MoneyPrinterTurbo && python3 -m venv .venv"
        all_ok=false
    fi
    
    # Hermes .env (pour la clé API Alibaba)
    if [ -f "$HERMES_ENV" ]; then
        log_success "Hermes .env: $HERMES_ENV"
    else
        log_warn "Hermes .env non trouvé (clé API Alibaba requise)"
    fi
    
    # Config files
    if [ -f "$PROJECT_DIR/config/unified_config.yaml" ]; then
        log_success "Config: unified_config.yaml"
    else
        log_error "Config manquante: $PROJECT_DIR/config/unified_config.yaml"
        all_ok=false
    fi
    
    # Personas
    local persona_count=$(ls -1 "$PROJECT_DIR/config/personas/"*.yaml 2>/dev/null | wc -l | tr -d ' ')
    if [ "$persona_count" -gt 0 ]; then
        log_success "Personas: $persona_count disponibles"
    else
        log_error "Aucun persona trouvé dans config/personas/"
        all_ok=false
    fi
    
    if [ "$all_ok" = true ]; then
        echo ""
        log_success "Toutes les dépendances sont OK !"
        return 0
    else
        echo ""
        log_error "Certaines dépendances manquent. Corriger avant de continuer."
        return 1
    fi
}

list_personas() {
    log_info "Personas disponibles :"
    echo ""
    $MPT_PYTHON "$SCRIPT_DIR/select_persona.py" --list
}

select_persona_interactive() {
    echo ""
    log_info "Sélection du persona :"
    echo ""
    
    local personas=()
    local i=1
    for persona_file in "$PROJECT_DIR/config/personas/"*.yaml; do
        local persona_id=$(basename "$persona_file" .yaml)
        local persona_name=$(grep "^name:" "$persona_file" | head -n1 | cut -d'"' -f2)
        personas+=("$persona_id")
        printf "  ${CYAN}%d${NC}) %s (%s)\n" "$i" "$persona_name" "$persona_id"
        ((i++))
    done
    
    echo ""
    read -p "Choisir un persona (1-$((i-1))): " choice
    
    if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -lt "$i" ]; then
        PERSONA="${personas[$((choice-1))]}"
        log_success "Persona sélectionné: $PERSONA"
    else
        log_error "Choix invalide"
        exit 1
    fi
}

select_subject_interactive() {
    echo ""
    log_info "Sujet de la vidéo :"
    echo ""
    echo "  Exemples :"
    echo "    - Les 5 erreurs fatales en architecture .NET"
    echo "    - Comment investir à 25 ans avec 100€/mois"
    echo "    - Pourquoi 90% des gens échouent (psychologie)"
    echo ""
    read -p "Entrer le sujet: " SUBJECT
    
    if [ -z "$SUBJECT" ]; then
        log_error "Sujet requis"
        exit 1
    fi
    
    log_success "Sujet: $SUBJECT"
}

run_pipeline() {
    echo ""
    log_info "=== Lancement du pipeline ==="
    echo ""
    
    # 1. Charger le persona
    log_info "1/4. Chargement du persona: $PERSONA"
    local config_file="$PROJECT_DIR/config/active_config.yaml"
    $MPT_PYTHON "$SCRIPT_DIR/select_persona.py" --persona "$PERSONA" --merge --output "$config_file"
    
    if [ ! -f "$config_file" ]; then
        log_error "Échec du chargement du persona"
        exit 1
    fi
    log_success "Config active: $config_file"
    
    # 2. Générer le script
    log_info "2/4. Génération du script humanisé..."
    local script_file="$PROJECT_DIR/storage/scripts/script_$(date +%Y%m%d_%H%M%S).txt"
    mkdir -p "$PROJECT_DIR/storage/scripts"
    
    $MPT_PYTHON "$SCRIPT_DIR/humanize_script.py" \
        --subject "$SUBJECT" \
        --output "$script_file"
    
    if [ ! -f "$script_file" ]; then
        log_error "Échec de la génération du script"
        exit 1
    fi
    
    local script_size=$(wc -c < "$script_file" | tr -d ' ')
    log_success "Script généré: $script_file ($script_size caractères)"
    
    # 3. Mode dry-run (arrêt ici)
    if [ "$DRY_RUN" = true ]; then
        echo ""
        log_warn "=== Mode DRY-RUN ==="
        log_info "Script généré avec succès, mais aucune vidéo produite."
        log_info "Fichier: $script_file"
        echo ""
        echo "Pour voir le script:"
        echo "  cat $script_file"
        echo ""
        echo "Pour produire la vidéo:"
        echo "  ./run.sh --persona $PERSONA --subject \"$SUBJECT\""
        return 0
    fi
    
    # 4. Produire la vidéo
    log_info "3/4. Production vidéo (MPT)..."
    log_warn "Cette étape peut prendre 5-15 minutes selon la durée de la vidéo."
    echo ""
    
    # Lancer MPT avec le script
    cd "$MPT_DIR"
    $MPT_PYTHON webui.py &
    MPT_PID=$!
    
    # Attendre que MPT démarre
    log_info "Attente du démarrage de MPT (port 8080)..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/health &> /dev/null; then
            log_success "MPT démarré"
            break
        fi
        sleep 2
    done
    
    # Appeler le pipeline unifié
    cd "$PROJECT_DIR"
    $MPT_PYTHON "$SCRIPT_DIR/unified_pipeline.py" \
        --script "$script_file" \
        --persona "$PERSONA" \
        --subject "$SUBJECT"
    
    # Arrêter MPT
    kill $MPT_PID 2>/dev/null || true
    
    # 5. Post-processing
    log_info "4/4. Post-processing..."
    
    local video_file="$OUTPUT_DIR/video_$(date +%Y%m%d_%H%M%S).mp4"
    
    # Color grading
    if [ -f "$video_file" ]; then
        log_info "Application du color grading..."
        $MPT_PYTHON "$SCRIPT_DIR/color_grade.py" \
            --input "$video_file" \
            --output "${video_file%.mp4}_graded.mp4" \
            --persona "$PERSONA"
        
        # Quality score
        log_info "Calcul du score qualité..."
        $MPT_PYTHON "$SCRIPT_DIR/quality_score.py" \
            --video "$video_file" \
            --script "$script_file"
        
        log_success "Vidéo prête: $video_file"
    else
        log_warn "Fichier vidéo non trouvé (mode test ou erreur MPT)"
    fi
    
    echo ""
    log_success "=== Pipeline terminé ==="
    echo ""
    echo "Fichiers générés:"
    echo "  Script: $script_file"
    [ -f "$video_file" ] && echo "  Vidéo: $video_file"
    echo ""
}

# ============================================================================
# Parse arguments
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --persona)
            PERSONA="$2"
            shift 2
            ;;
        --subject)
            SUBJECT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --list-personas)
            LIST_PERSONAS=true
            shift
            ;;
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            log_error "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# ============================================================================
# Main
# ============================================================================

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  🎬 DevIAFR Pipeline Runner${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$SHOW_HELP" = true ]; then
    show_help
    exit 0
fi

cd "$PROJECT_DIR"

if [ "$LIST_PERSONAS" = true ]; then
    list_personas
    exit 0
fi

if [ "$CHECK_ONLY" = true ]; then
    check_dependencies
    exit $?
fi

# Vérifier les dépendances
check_dependencies || exit 1

# Mode interactif si pas de persona/sujet spécifié
if [ -z "$PERSONA" ]; then
    select_persona_interactive
fi

if [ -z "$SUBJECT" ]; then
    select_subject_interactive
fi

# Lancer le pipeline
run_pipeline

echo ""
log_success "Terminé !"
echo ""
