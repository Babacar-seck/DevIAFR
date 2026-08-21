#!/usr/bin/env python3
"""_tst_bridge_runner.py — helper exécuté dans le venv de TestShortYoutube (TST).

Ce script n'est pas destiné à être appelé directement : `unified_pipeline.py`
le lance en subprocess avec l'interpréteur `TST/.venv/bin/python` (pour
bénéficier des dépendances de TST — sqlalchemy, google-api-client, etc. —
sans les dupliquer dans l'environnement de DevIAFR), `cwd=<tst_path>`, et lui
passe ses paramètres en JSON sur stdin (jamais interpolés dans du code Python
— évite tout risque d'injection si le sujet contient des guillemets).

Il appelle `src.batch_runner.run_single()` et imprime le résultat sur stdout,
préfixé par `RESULT_JSON:`, pour que le processus appelant puisse le parser
sans dépendre du format des logs `rich` imprimés par le pipeline lui-même.
"""
from __future__ import annotations

import json
import sys

from dotenv import load_dotenv


def main() -> None:
    params = json.loads(sys.stdin.read())

    # TST résout sa DATABASE_URL (sqlite:///data/dev.db) depuis son .env —
    # sans ça, src/db/engine.py retombe sur son défaut PostgreSQL codé en dur.
    # main.py de TST fait le même load_dotenv() avant de toucher la DB, mais
    # là-bas ça marche par accident : python-dotenv (sans argument) cherche
    # le .env en remontant depuis le fichier *appelant*, pas depuis le cwd.
    # Comme ce script vit dans DevIAFR/scripts/ (hors de l'arbre TST), cette
    # recherche par pile d'appel ne trouve jamais TST/.env — il faut un
    # chemin explicite, relatif au cwd (=tst_path, fixé par unified_pipeline.py).
    load_dotenv(".env")

    sys.path.insert(0, ".")
    from src.batch_runner import run_single
    from src.database import ensure_user, init_db

    user_id = "default"
    init_db()
    # videos.user_id est une clé étrangère vers users — TST seede toujours
    # cette ligne avant d'écrire un video record (voir main.py, src/auth.py).
    ensure_user(user_id, f"{user_id}@local")
    result = run_single(
        user_id=user_id,
        topic=params["topic"],
        fmt=params["fmt"],
        privacy="private",
        upload=params.get("upload", False),
        content_profile=params["content_profile"],
    )

    print("RESULT_JSON:" + json.dumps(result))


if __name__ == "__main__":
    main()
