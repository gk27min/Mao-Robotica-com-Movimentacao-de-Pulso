"""
Servidor Flask do projeto FalaComaMão (LIBRAS-BOT).

Etapa 1 — orquestração entre Flutter e Ollama:

    Flutter (texto NLP) ──HTTP──> /api/comando ──> Ollama ──> sinal escolhido
                                                                  │
                                                                  └──> (etapa 4) BLE → Arduino

Endpoints:
  GET  /api/status          — saúde do servidor + Ollama
  GET  /api/sinais          — lista todos os sinais cadastrados
  POST /api/sinais          — cadastra um novo sinal
  DELETE /api/sinais/<id>   — remove um sinal pelo id
  POST /api/comando         — recebe texto e devolve qual sinal o Ollama escolheu
"""

from __future__ import annotations

import json
import logging
import re
import threading
from pathlib import Path
from typing import Any

from flask import Flask, abort, jsonify, request
from flask_cors import CORS

from ollama_client import OllamaError, classificar_intencao, healthcheck

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("falacomamao")

SIGNS_FILE = Path(__file__).parent / "signs.json"
_signs_lock = threading.Lock()  # protege leitura/escrita concorrente do JSON

DEDOS = ("polegar", "indicador", "medio", "anelar", "minimo")
SERVOS = (*DEDOS, "pulso")
ID_REGEX = re.compile(r"^[a-z0-9_\-]{1,40}$")

app = Flask(__name__)
CORS(app)  # permite chamadas do Flutter Web; em mobile é inofensivo.


# ---------------------------------------------------------------------------
# Persistência (JSON file)
# ---------------------------------------------------------------------------

def carregar_sinais() -> list[dict]:
    with _signs_lock:
        if not SIGNS_FILE.exists():
            return []
        with open(SIGNS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("sinais", [])


def salvar_sinais(sinais: list[dict]) -> None:
    with _signs_lock:
        with open(SIGNS_FILE, "w", encoding="utf-8") as f:
            json.dump({"sinais": sinais}, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------

def _validar_sinal(payload: Any) -> dict:
    """
    Valida o payload de um novo sinal e devolve o dict normalizado.
    Levanta `ValueError` com mensagem amigável se algo estiver errado.
    """
    if not isinstance(payload, dict):
        raise ValueError("Esperado um objeto JSON com os campos do sinal.")

    sid = str(payload.get("id", "")).strip().lower()
    nome = str(payload.get("nome", "")).strip()
    descricao = str(payload.get("descricao", "")).strip()
    sinonimos = payload.get("sinonimos", [])
    angulos_raw = payload.get("angulos", {})

    if not sid or not ID_REGEX.match(sid):
        raise ValueError(
            "Campo 'id' inválido. Use minúsculas, números, hífen ou underscore (1-40 caracteres)."
        )
    if not nome:
        raise ValueError("Campo 'nome' é obrigatório.")
    if not descricao:
        raise ValueError("Campo 'descricao' é obrigatório (o Ollama usa pra decidir).")
    if not isinstance(sinonimos, list) or not all(isinstance(x, str) for x in sinonimos):
        raise ValueError("Campo 'sinonimos' deve ser uma lista de strings.")
    if not isinstance(angulos_raw, dict):
        raise ValueError("Campo 'angulos' deve ser um objeto com os 6 servos.")

    angulos: dict[str, int] = {}
    for servo in SERVOS:
        if servo not in angulos_raw:
            raise ValueError(f"Faltando ângulo do servo '{servo}'.")
        try:
            valor = int(angulos_raw[servo])
        except (TypeError, ValueError) as e:
            raise ValueError(f"Ângulo de '{servo}' precisa ser inteiro.") from e
        if not 0 <= valor <= 180:
            raise ValueError(f"Ângulo de '{servo}' fora do intervalo 0..180.")
        angulos[servo] = valor

    return {
        "id": sid,
        "nome": nome,
        "descricao": descricao,
        "sinonimos": [s.strip() for s in sinonimos if s.strip()],
        "angulos": angulos,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/status", methods=["GET"])
def status():
    ollama = healthcheck()
    sinais = carregar_sinais()
    return jsonify({
        "servidor": "online",
        "sinais_cadastrados": len(sinais),
        "ollama": ollama,
    })


@app.route("/api/sinais", methods=["GET"])
def listar_sinais():
    return jsonify({"sinais": carregar_sinais()})


@app.route("/api/sinais", methods=["POST"])
def cadastrar_sinal():
    try:
        novo = _validar_sinal(request.get_json(silent=True))
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

    sinais = carregar_sinais()
    if any(s["id"] == novo["id"] for s in sinais):
        return jsonify({"erro": f"Já existe um sinal com id '{novo['id']}'."}), 409

    sinais.append(novo)
    salvar_sinais(sinais)
    log.info("Sinal cadastrado: %s", novo["id"])
    return jsonify({"ok": True, "sinal": novo}), 201


@app.route("/api/sinais/<sinal_id>", methods=["DELETE"])
def remover_sinal(sinal_id: str):
    sid = sinal_id.strip().lower()
    sinais = carregar_sinais()
    novos = [s for s in sinais if s["id"] != sid]
    if len(novos) == len(sinais):
        abort(404, description=f"Sinal '{sid}' não encontrado.")
    salvar_sinais(novos)
    log.info("Sinal removido: %s", sid)
    return jsonify({"ok": True, "id": sid})


@app.route("/api/comando", methods=["POST"])
def comando():
    """
    Recebe o texto do Flutter (form-urlencoded `comando=...` OU JSON `{"comando": ...}`),
    pergunta pro Ollama qual sinal usar e devolve o sinal + ângulos.
    """
    texto = (
        request.form.get("comando")
        or (request.get_json(silent=True) or {}).get("comando")
        or ""
    ).strip()

    if not texto:
        return jsonify({"erro": "Campo 'comando' vazio."}), 400

    sinais = carregar_sinais()
    if not sinais:
        return jsonify({
            "erro": "Nenhum sinal cadastrado. Cadastre sinais em /api/sinais antes."
        }), 409

    try:
        escolhido = classificar_intencao(texto, sinais)
    except OllamaError as e:
        log.exception("Falha no Ollama")
        return jsonify({"erro": str(e)}), 502

    if escolhido is None:
        return jsonify({
            "texto": texto,
            "sinal": None,
            "mensagem": "Nenhum sinal cadastrado corresponde ao que você falou.",
        })

    # TODO etapa 4: enviar `escolhido["angulos"]` para o Arduino via BLE.
    return jsonify({
        "texto": texto,
        "sinal": escolhido,
        "mensagem": f"Executando sinal: {escolhido['nome']}",
    })


@app.errorhandler(404)
def _404(e):
    return jsonify({"erro": str(e.description) if hasattr(e, "description") else "Não encontrado"}), 404


if __name__ == "__main__":
    # host=0.0.0.0 → o Flutter no celular acessa pelo IP do PC na mesma rede.
    app.run(host="0.0.0.0", port=5000, debug=True)
