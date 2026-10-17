"""P2: the core must not depend on a web framework, so any intake can sit on top of it."""

import ast
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parents[1] / "src" / "notifications" / "core"
FORBIDDEN = {"fastapi", "starlette", "pydantic", "uvicorn", "websockets", "pika"}


def imported_roots(source: str) -> set[str]:
    roots = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_scanner_finds_forbidden_imports():
    assert imported_roots("import fastapi.routing\nfrom pydantic import BaseModel") == {
        "fastapi",
        "pydantic",
    }


def test_core_does_not_import_a_web_framework():
    offenders = {
        path.name: imported_roots(path.read_text(encoding="utf-8")) & FORBIDDEN
        for path in CORE_DIR.rglob("*.py")
    }
    assert {name: found for name, found in offenders.items() if found} == {}
