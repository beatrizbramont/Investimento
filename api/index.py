"""Ponto de entrada da API na Vercel.

A Vercel transforma cada arquivo em `api/` numa função serverless. Para apps
ASGI (como o FastAPI) basta expor uma variável chamada `app` — é o que fazemos
aqui, reaproveitando exatamente o mesmo código que roda em desenvolvimento.

Nada de lógica neste arquivo: ele só coloca `backend/` no caminho de importação,
já que o pacote vive fora da pasta `api/` para manter o repositório legível.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))

from app.main import app  # noqa: E402  (precisa vir depois do sys.path)

__all__ = ["app"]
