# *-- UTF-8 --*

# ======== IMPORTS ========
import os
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Imports compatibles exécutions et import package
def _resolve_repo_root() -> str : 
    candidates = []
    project_root_env = os.getenv("PROJECT_ROOT", None)
    if project_root_env : 
        candidates.append(Path(project_root_env).resolve())
    candidates.append(Path.cwd().resolve())
    module_path = Path(__file__).resolve()
    candidates.extend(module_path.parents)

    for candidate in candidates : 
        if (candidate / "backend").exists()  and (candidate / "shared").exists() : 
            return str(candidate)
    return str(module_path.parents[4])  # fallback to the 4th parent of the module path

    _REPO_ROOT = _resolve_repo_root()

    try : 
        from .lm_utils import * 