"""
Integração de janela embutida do Grafana para a Ground Station.
"""

from __future__ import annotations

import configparser
import importlib
import multiprocessing as mp
import webbrowser
from typing import Dict, Any

from config_manager import CONFIG_FILE


def _load_grafana_config() -> Dict[str, Any]:
    parser = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=("#", ";"))
    parser.read(CONFIG_FILE)

    section = parser["GRAFANA"] if "GRAFANA" in parser else {}

    return {
        "enabled": str(section.get("enabled", "true")).strip().lower() in ("1", "true", "yes", "on"),
        "url": str(section.get("url", "http://localhost:3000/d/pucpr-telemetry-live")).strip(),
        "query": str(section.get("query", "orgId=1&refresh=500ms")).strip(),
        "title": str(section.get("title", "PUCPR Racing - Grafana Live")).strip(),
        "width": int(str(section.get("width", "1300")).strip()),
        "height": int(str(section.get("height", "820")).strip()),
    }


def _build_full_url(config: Dict[str, Any]) -> str:
    base = config["url"]
    query = config["query"]

    if not query:
        return base

    if "?" in base:
        return f"{base}&{query}"

    return f"{base}?{query}"


def _run_webview_process(config: Dict[str, Any], full_url: str) -> None:
    webview_module = importlib.import_module("webview")
    webview_module.create_window(
        title=config["title"],
        url=full_url,
        width=config["width"],
        height=config["height"],
        resizable=True,
    )
    webview_module.start(gui="edgechromium", debug=False)


def open_grafana_embedded(app_instance) -> None:
    config = _load_grafana_config()
    full_url = _build_full_url(config)

    if not config["enabled"]:
        app_instance.atualizar_status("Grafana desabilitado no INI.")
        return

    existing_process = getattr(app_instance, "grafana_embed_process", None)
    if existing_process and existing_process.is_alive():
        app_instance.atualizar_status("Janela Grafana já está aberta.")
        return

    try:
        webview_module = importlib.import_module("webview")
    except Exception:
        webbrowser.open(full_url)
        app_instance.atualizar_status("pywebview não encontrado. Abrindo Grafana no navegador.")
        return

    try:
        process = mp.Process(target=_run_webview_process, args=(config, full_url), daemon=True)
        process.start()
        app_instance.grafana_embed_process = process
        app_instance.atualizar_status("Abrindo Grafana embutido...")
    except Exception:
        webbrowser.open(full_url)
        app_instance.atualizar_status("Falha no embed. Abrindo Grafana no navegador.")
