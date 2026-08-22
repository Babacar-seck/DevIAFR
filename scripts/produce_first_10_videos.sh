#!/bin/bash
# produce_first_10_videos.sh — Orchestre la production des 10 premières vidéos Dev IA FR
#
# Usage:
#   ./produce_first_10_videos.sh
#   ./produce_first_10_videos.sh --dry-run  # test sans production réelle

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🧪 Mode dry-run activé"
fi

PYTHON="/Users/seckbabacar/MyWorkProjectGithub/MoneyPrinterTurbo/.venv/bin/python"
OUTPUT_DIR="storage/output/first_10_videos"
mkdir -p "$OUTPUT_DIR"

echo "============================================================"
echo "🎬 Production des 10 premières vidéos Dev IA FR"
echo "============================================================"
echo ""

# Liste des 10 sujets (top 10 du rapport etude_marche_niche_et_100_videos.md)
SUBJECTS=(
    "Comment créer une API REST .NET avec Entity Framework Core"
    "Angular vs React en 2026 : quel framework choisir pour votre prochain projet"
    "Intégrer Claude AI dans une application .NET en 10 minutes"
    "Les 5 patterns de conception que tout développeur .NET doit connaître"
    "Docker pour les développeurs .NET : de zéro à production"
    "Comment optimiser les performances d'une API .NET Core"
    "Tester son code Angular comme un pro avec Jest et Testing Library"
    "Architecture Clean Architecture en .NET : guide pratique"
    "Les nouveautés de .NET 9 qui changent tout"
    "Comment déployer une application Angular sur Azure avec CI/CD"
)

for i in "${!SUBJECTS[@]}"; do
    SUBJECT="${SUBJECTS[$i]}"
    VIDEO_NUM=$((i + 1))
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📹 Vidéo $VIDEO_NUM/10 : $SUBJECT"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    VIDEO_DIR="$OUTPUT_DIR/video_${VIDEO_NUM}_$(echo "$SUBJECT" | sed 's/[^a-zA-Z0-9]/_/g' | cut -c1-50)"
    mkdir -p "$VIDEO_DIR"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "🧪 [DRY-RUN] Script generation: $SUBJECT"
        $PYTHON scripts/humanize_script.py --subject "$SUBJECT" --output "$VIDEO_DIR/script.txt"
        
        echo "🧪 [DRY-RUN] Quality score check"
        # Créer une vidéo factice pour le test
        echo "fake video" > "$VIDEO_DIR/video.mp4"
        $PYTHON scripts/quality_score.py --video "$VIDEO_DIR/video.mp4" --script "$VIDEO_DIR/script.txt" --json || true
        
        echo "🧪 [DRY-RUN] Thumbnail generation"
        $PYTHON scripts/unified_pipeline.py --script "$VIDEO_DIR/script.txt" --subject "$SUBJECT" --skip-mpt --video "$VIDEO_DIR/video.mp4" 2>&1 | grep -E "(✓|✗|→)" || true
        
        continue
    fi
    
    # Étape 1 : Générer le script humanisé
    echo "📝 Étape 1/7 : Génération du script humanisé"
    $PYTHON scripts/humanize_script.py --subject "$SUBJECT" --output "$VIDEO_DIR/script.txt"
    echo ""
    
    # Étape 2 : Production vidéo via MPT (manuel pour l'instant)
    echo "🎥 Étape 2/7 : Production vidéo via MPT"
    echo "   ⚠️  Lancer manuellement :"
    echo "   cd ~/MyWorkProjectGithub/MoneyPrinterTurbo"
    echo "   .venv/bin/python webui.py"
    echo "   Puis utiliser l'API ou le WebUI avec le script : $VIDEO_DIR/script.txt"
    echo ""
    echo "   En attente de la vidéo... (appuyer sur Entrée quand prête)"
    read -r
    echo ""
    
    # Étape 3 : Sous-titres Whisper
    echo "📜 Étape 3/7 : Génération des sous-titres Whisper"
    if [[ -f "$VIDEO_DIR/video.mp4" ]]; then
        $PYTHON scripts/whisper_subtitles.py --input "$VIDEO_DIR/video.mp4" --output "$VIDEO_DIR/video_subtitled.mp4" --srt "$VIDEO_DIR/subtitles.srt"
        mv "$VIDEO_DIR/video_subtitled.mp4" "$VIDEO_DIR/video.mp4"
    else
        echo "   ⚠️  Vidéo non trouvée, skip"
    fi
    echo ""
    
    # Étape 4 : Color grading
    echo "🎨 Étape 4/7 : Color grading (LUT)"
    if [[ -f "$VIDEO_DIR/video.mp4" ]]; then
        $PYTHON scripts/color_grading.py --input "$VIDEO_DIR/video.mp4" --output "$VIDEO_DIR/video_graded.mp4"
        mv "$VIDEO_DIR/video_graded.mp4" "$VIDEO_DIR/video.mp4"
    fi
    echo ""
    
    # Étape 5 : Intro/Outro
    echo "🎬 Étape 5/7 : Ajout intro/outro"
    if [[ -f "$VIDEO_DIR/video.mp4" ]]; then
        $PYTHON scripts/intro_outro.py --input "$VIDEO_DIR/video.mp4" --output "$VIDEO_DIR/video_final.mp4" --channel dev_ia_fr
        mv "$VIDEO_DIR/video_final.mp4" "$VIDEO_DIR/video.mp4"
    fi
    echo ""
    
    # Étape 6 : Quality score
    echo "✅ Étape 6/7 : Quality score"
    THUMBNAIL=$(ls storage/thumbnails/thumb_*.png 2>/dev/null | tail -1 || echo "")
    if [[ -f "$VIDEO_DIR/video.mp4" ]]; then
        SCORE=$($PYTHON scripts/quality_score.py --video "$VIDEO_DIR/video.mp4" --script "$VIDEO_DIR/script.txt" --thumbnail "$THUMBNAIL" --json | grep -o '"total": [0-9]*' | grep -o '[0-9]*')
        echo "   Score : $SCORE/100"
        if [[ "$SCORE" -lt 70 ]]; then
            echo "   ⚠️  Score insuffisant (< 70), vidéo rejetée"
            continue
        fi
    fi
    echo ""
    
    # Étape 7 : Revue humaine
    echo "👤 Étape 7/7 : Revue humaine"
    if [[ -f "$VIDEO_DIR/video.mp4" ]]; then
        $PYTHON scripts/human_review.py --video "$VIDEO_DIR/video.mp4" --script "$VIDEO_DIR/script.txt" --thumbnail "$THUMBNAIL" --channel dev_ia_fr
    fi
    echo ""
    
    echo "✅ Vidéo $VIDEO_NUM terminée : $VIDEO_DIR/video.mp4"
done

echo ""
echo "============================================================"
echo "🎉 Production des 10 vidéos terminée !"
echo "============================================================"
echo ""
echo "Prochaines étapes :"
echo "  1. Upload YouTube : utiliser TST uploader.py ou MPT upload_post.py"
echo "  2. Cross-platform : python scripts/cross_publish.py --video ... --title ..."
echo "  3. Repurposing : python scripts/repurpose.py --input video_long.mp4 --output-dir clips/"
echo "  4. Analytics : python scripts/analytics_loop.py --channel dev_ia_fr"
echo ""
