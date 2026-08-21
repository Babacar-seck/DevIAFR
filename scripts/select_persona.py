#!/usr/bin/env python3
"""
select_persona.py — Charge et fusionne un persona avec la configuration principale

Usage:
    python select_persona.py --persona dev_ia_fr
    python select_persona.py --persona finance_par_age --merge
    python select_persona.py --list
"""

import argparse
import json
import sys
from pathlib import Path

import yaml


def load_yaml(path: Path) -> dict:
    """Charge un fichier YAML."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def deep_merge(base: dict, override: dict) -> dict:
    """Fusionne récursivement deux dictionnaires (override écrase base)."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def list_personas(personas_dir: Path) -> list[dict]:
    """Liste tous les personas disponibles."""
    personas = []
    for yaml_file in sorted(personas_dir.glob("*.yaml")):
        persona = load_yaml(yaml_file)
        personas.append({
            "id": persona.get("id", yaml_file.stem),
            "name": persona.get("name", yaml_file.stem),
            "niche": persona.get("channel", {}).get("niche", "N/A"),
            "file": yaml_file.name,
        })
    return personas


def load_persona(persona_id: str, personas_dir: Path) -> dict:
    """Charge un persona spécifique."""
    persona_file = personas_dir / f"{persona_id}.yaml"
    if not persona_file.exists():
        raise FileNotFoundError(f"Persona '{persona_id}' introuvable dans {personas_dir}")
    return load_yaml(persona_file)


def merge_with_unified(persona: dict, unified_config: dict) -> dict:
    """Fusionne un persona avec unified_config.yaml."""
    # Le persona écrase les valeurs de unified_config
    merged = deep_merge(unified_config, persona)
    
    # Copie les valeurs du persona dans les sections appropriées
    if "channel" in persona:
        merged["channel"] = persona["channel"]
    
    if "branding" in persona:
        merged["branding"] = deep_merge(
            merged.get("branding", {}),
            persona["branding"]
        )
    
    if "voice" in persona:
        merged["tts"]["engine"] = persona["voice"]["engine"]
        merged["tts"]["voice_id"] = persona["voice"]["voice_id"]
        merged["tts"]["voice_style"] = persona["voice"]["style"]
    
    if "script" in persona:
        merged["script"] = deep_merge(
            merged.get("script", {}),
            persona["script"]
        )
    
    if "content" in persona:
        merged["content"] = persona["content"]
    
    if "quality" in persona:
        merged["quality"] = persona["quality"]
    
    if "publishing" in persona:
        merged["publishing"] = persona["publishing"]
    
    return merged


def main():
    parser = argparse.ArgumentParser(description="Sélectionne et charge un persona")
    parser.add_argument("--persona", type=str, help="ID du persona à charger")
    parser.add_argument("--list", action="store_true", help="Liste tous les personas")
    parser.add_argument("--merge", action="store_true", help="Fusionne avec unified_config.yaml")
    parser.add_argument("--output", type=str, help="Sauvegarde la config fusionnée dans un fichier")
    parser.add_argument("--json", action="store_true", help="Affiche en JSON au lieu de YAML")
    
    args = parser.parse_args()
    
    # Chemins
    script_dir = Path(__file__).parent
    config_dir = script_dir.parent / "config"
    personas_dir = config_dir / "personas"
    unified_config_file = config_dir / "unified_config.yaml"
    
    # Liste des personas
    if args.list:
        personas = list_personas(personas_dir)
        print("\n=== Personas disponibles ===\n")
        for p in personas:
            print(f"  [{p['id']}] {p['name']}")
            print(f"    Niche: {p['niche']}")
            print(f"    Fichier: {p['file']}")
            print()
        print(f"Total: {len(personas)} personas\n")
        return
    
    # Chargement d'un persona
    if not args.persona:
        parser.error("--persona requis (ou utiliser --list)")
    
    try:
        persona = load_persona(args.persona, personas_dir)
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    
    # Fusion avec unified_config
    if args.merge:
        if not unified_config_file.exists():
            print(f"❌ {unified_config_file} introuvable", file=sys.stderr)
            sys.exit(1)
        
        unified_config = load_yaml(unified_config_file)
        merged_config = merge_with_unified(persona, unified_config)
        
        print(f"✅ Persona '{args.persona}' fusionné avec unified_config.yaml\n")
        
        # Affichage
        if args.json:
            print(json.dumps(merged_config, indent=2, ensure_ascii=False))
        else:
            print(yaml.dump(merged_config, allow_unicode=True, sort_keys=False))
        
        # Sauvegarde optionnelle
        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w", encoding="utf-8") as f:
                if args.json:
                    json.dump(merged_config, f, indent=2, ensure_ascii=False)
                else:
                    yaml.dump(merged_config, f, allow_unicode=True, sort_keys=False)
            print(f"\n💾 Config sauvegardée: {output_path}")
    else:
        # Affichage simple du persona
        print(f"✅ Persona chargé: {persona.get('name', args.persona)}\n")
        if args.json:
            print(json.dumps(persona, indent=2, ensure_ascii=False))
        else:
            print(yaml.dump(persona, allow_unicode=True, sort_keys=False))


if __name__ == "__main__":
    main()
