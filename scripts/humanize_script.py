#!/usr/bin/env python3
"""
humanize_script.py — Humanise et structure un script LLM brut avec storytelling.

Prend un script LLM brut et applique :
1. Structure storytelling obligatoire (Hook → Problème → Enquête → Twist → Résolution → CTA+boucle)
2. Anecdote personnelle (expérience .NET/Angular)
3. Émotion et engagement
4. Exemples concrets

Usage:
    python humanize_script.py --input script_brut.txt --output script_final.txt
    python humanize_script.py --subject "Comment créer une API REST .NET" --output script_final.txt
"""

import argparse
import os
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent.parent
UNIFIED_CONFIG = SCRIPT_DIR / "config" / "unified_config.yaml"


def load_config() -> dict:
    with open(UNIFIED_CONFIG) as f:
        return yaml.safe_load(f)


def call_llm(prompt: str, cfg: dict, max_tokens: int = 2000, temperature: float = 0.8) -> str:
    """Appelle le LLM configuré (Ollama, Gemini ou Alibaba DashScope)."""
    llm_cfg = cfg.get("llm", {})
    provider = llm_cfg.get("provider", "ollama")

    # Helper : charge une variable d'env depuis ~/.hermes/.env si absente
    def _env_from_hermes(key: str) -> str | None:
        val = os.getenv(key)
        if val:
            return val
        env_file = Path.home() / ".hermes" / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip("\"'")
        return None

    # Le provider humanizer peut surcharger le provider principal
    humanizer_provider = llm_cfg.get("humanizer_provider", provider)

    if humanizer_provider == "ollama":
        import requests
        base_url = llm_cfg.get("ollama_base_url", "http://localhost:11434/v1")
        model = llm_cfg.get("humanizer_model", "gemma4:latest")

        response = requests.post(
            f"{base_url}/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=120,
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise RuntimeError(f"Ollama API error: {response.status_code} - {response.text[:200]}")

    elif humanizer_provider == "alibaba":
        import requests
        base_url = llm_cfg.get("alibaba_base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        api_key = llm_cfg.get("alibaba_api_key") or _env_from_hermes("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY non configuré (ni dans unified_config.yaml, ni dans ~/.hermes/.env)")
        model = llm_cfg.get("humanizer_model", "qwen3.7-max")

        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=180,
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise RuntimeError(f"Alibaba API error: {response.status_code} - {response.text[:200]}")

    elif humanizer_provider == "gemini":
        import google.generativeai as genai
        api_key = llm_cfg.get("gemini_api_key") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY non configuré")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(llm_cfg.get("humanizer_model", "gemini-3.5-flash-lite"))
        response = model.generate_content(prompt)
        return response.text

    else:
        raise ValueError(f"Provider LLM non supporté: {humanizer_provider}")


def generate_script_from_subject(subject: str, cfg: dict) -> str:
    """Génère un script LLM brut à partir d'un sujet."""
    llm_cfg = cfg.get("llm", {})
    script_cfg = cfg.get("script", {})

    prompt = f"""Tu es un expert YouTube Tech francophone. Génère un script vidéo pour le sujet suivant :

Sujet : {subject}
Durée cible : {script_cfg.get('target_duration_s', 60)} secondes
Style : {script_cfg.get('style', 'conversational, confident, direct')}

Génère un script brut qui couvre :
- Introduction (hook fort)
- Explication du problème/opportunité
- Solution technique (avec exemples de code si pertinent)
- Conclusion et appel à l'action

Ne structure pas encore — génère juste le contenu brut.
"""

    return call_llm(prompt, cfg, max_tokens=1500, temperature=0.7)


def humanize_script(brut_script: str, subject: str, cfg: dict) -> str:
    """Humanise et structure un script LLM brut avec storytelling."""
    script_cfg = cfg.get("script", {})
    storytelling = script_cfg.get("storytelling", {})
    channel_cfg = cfg.get("channel", {})

    structure_template = storytelling.get(
        "structure",
        "Hook (3s) → Problème (10s) → Enquête (20s) → Twist (10s) → Résolution (10s) → CTA+boucle (7s)"
    )

    prompt = f"""Tu es un scriptwriter YouTube expert en storytelling tech. Humanise et structure ce script brut avec la structure suivante :

STRUCTURE OBLIGATOIRE :
{structure_template}

RÈGLES :
- Langue : {channel_cfg.get('language', 'fr')}
- Ton : {channel_cfg.get('tone', 'conversational, direct, sans blabla')}
- Ajoute UNE anecdote personnelle (expérience .NET/Angular)
- Ajoute de l'émotion (frustration, surprise, satisfaction)
- Utilise des exemples concrets (pas de théorie abstraite)
- CTA final : "Abonne-toi" ou "Commente"
- Boucle finale : tease le prochain sujet

SUJET : {subject}

SCRIPT BRUT :
{brut_script}

GÉNÈRE LE SCRIPT HUMANISÉ ET STRUCTURÉ :
"""

    return call_llm(prompt, cfg, max_tokens=2000, temperature=0.8)


def main():
    parser = argparse.ArgumentParser(description="Humanise un script LLM avec storytelling")
    parser.add_argument("--input", type=str, help="Fichier script brut (si pas --subject)")
    parser.add_argument("--subject", type=str, help="Sujet à scripter (si pas --input)")
    parser.add_argument("--output", type=str, required=True, help="Fichier de sortie")
    args = parser.parse_args()

    if not args.input and not args.subject:
        print("Erreur: --input ou --subject requis", file=sys.stderr)
        sys.exit(1)

    cfg = load_config()

    # Étape 1 : obtenir le script brut
    if args.input:
        brut_script = Path(args.input).read_text()
        print(f"✓ Script brut chargé depuis {args.input}")
    else:
        print(f"Génération du script brut pour : {args.subject}")
        brut_script = generate_script_from_subject(args.subject, cfg)
        print(f"✓ Script brut généré ({len(brut_script)} caractères)")

    # Étape 2 : humaniser et structurer
    print("Humanisation et structuration du script...")
    humanized = humanize_script(brut_script, args.subject or "Script personnalisé", cfg)

    # Étape 3 : sauvegarder
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(humanized)

    print(f"\n✓ Script humanisé sauvegardé : {output_path}")
    print(f"  Taille : {len(humanized)} caractères")
    print(f"  Structure : {cfg.get('script', {}).get('storytelling', {}).get('structure', 'N/A')}")


if __name__ == "__main__":
    main()
