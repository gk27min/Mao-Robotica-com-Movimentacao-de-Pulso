"""
REPL de teste do "cérebro" — valida que o Ollama está escolhendo os sinais
corretos a partir de uma fala, SEM precisar do Flutter nem do Arduino.

Uso:
    python test_ollama.py

Digite frases em PT-BR e veja qual sinal o Ollama escolhe.
Use `lista` para ver os sinais cadastrados, `sair` para encerrar.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ollama_client import OllamaError, classificar_intencao, healthcheck

SIGNS_FILE = Path(__file__).parent / "signs.json"


def carregar_sinais() -> list[dict]:
    if not SIGNS_FILE.exists():
        print(f"[ERRO] Arquivo {SIGNS_FILE} não encontrado.")
        sys.exit(1)
    with open(SIGNS_FILE, "r", encoding="utf-8") as f:
        return json.load(f).get("sinais", [])


def banner():
    print("=" * 60)
    print("  FalaComaMão — teste do classificador Ollama")
    print("=" * 60)


def checar_ollama():
    info = healthcheck()
    if not info["online"]:
        print("[ERRO] Ollama não está respondendo em http://localhost:11434.")
        print("       Abra o PowerShell e rode: ollama list")
        sys.exit(1)
    if not info["modelo_instalado"]:
        print("[AVISO] Modelo llama3.1:8b não aparece em `ollama list`.")
        print("        Rode: ollama pull llama3.1:8b")
        print(f"        Modelos detectados: {info['modelos']}")
        sys.exit(1)
    print(f"[OK] Ollama online. Modelos: {info['modelos']}")


def main():
    banner()
    checar_ollama()
    sinais = carregar_sinais()
    print(f"[OK] Sinais cadastrados ({len(sinais)}): "
          f"{[s['id'] for s in sinais]}")
    print()
    print("Digite uma fala em português. Comandos: 'lista', 'sair'.")
    print()

    while True:
        try:
            texto = input("você> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not texto:
            continue
        if texto.lower() in {"sair", "exit", "quit"}:
            break
        if texto.lower() in {"lista", "list", "ls"}:
            sinais = carregar_sinais()
            for s in sinais:
                print(f"  - {s['id']:>10}  {s['nome']:<10}  → {s['descricao']}")
            continue

        try:
            escolhido = classificar_intencao(texto, sinais)
        except OllamaError as e:
            print(f"  [ERRO] {e}")
            continue

        if escolhido is None:
            print("  → nenhum sinal corresponde")
        else:
            print(f"  → {escolhido['nome']}  (id={escolhido['id']})")
            print(f"     ângulos: {escolhido['angulos']}")
        print()

    print("Até mais!")


if __name__ == "__main__":
    main()
