"""Fixtures and import stubs for the FastAPI API tests.

The API module instantiates ChromaDB, the catalog parser and the Ollama client
at import time. These tests only exercise authorization logic, so those heavy
collaborators are replaced with minimal fakes before ``src.api`` is imported.
"""

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class _FakeRAGSystem:
    def __init__(self, *args, **kwargs):
        pass

    def query(self, *args, **kwargs):
        return {"answer": "", "sources": [], "latency_ms": 0}

    def get_stats(self):
        return {}


class _FakeCatalogo:
    def __init__(self, *args, **kwargs):
        pass


class _FakeOllamaClient:
    def __init__(self, *args, **kwargs):
        pass


def _install_stub(name: str, attribute: str, value) -> None:
    module = types.ModuleType(name)
    setattr(module, attribute, value)
    sys.modules.setdefault(name, module)


_install_stub("src.rag", "RAGSystem", _FakeRAGSystem)
_install_stub("src.catalogo", "Catalogo", _FakeCatalogo)
_install_stub("src.ollama_client", "OllamaClient", _FakeOllamaClient)


@pytest.fixture()
def api_module():
    import src.api as api

    return api
