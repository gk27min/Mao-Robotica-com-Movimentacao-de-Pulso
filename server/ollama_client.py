"""
Cliente Ollama para o projeto FalaComaMão (LIBRAS-BOT).

Recebe uma fala/texto em português e a lista de sinais cadastrados,
e devolve qual sinal melhor representa a intenção do usuário.

A API do Ollama roda localmente em http://localhost:11434.
Usamos `format=json` + `temperature=0.1` para forçar saída estruturada
e determinística — ideal para classificação de intenção.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"
TIMEOUT_SEGUNDOS = 60


class OllamaError(Exception):
    """Erro genérico ao falar com o Ollama (offline, modelo ausente, JSON inválido, etc.)."""


def _formatar_lista_sinais(sinais: list[dict]) -> str:
    """Monta a descrição dos sinais disponíveis para o LLM."""
    linhas = []
    for s in sinais:
        sinonimos = ", ".join(s.get("sinonimos", [])) or "(sem sinônimos)"
        linhas.append(
            f'- id: "{s["id"]}"\n'
            f'  nome: {s["nome"]}\n'
            f'  quando usar: {s["descricao"]}\n'
            f'  sinônimos/contextos: {sinonimos}'
        )
    return "\n".join(linhas)


def _montar_prompt(texto_usuario: str, sinais: list[dict]) -> str:
    """Prompt de classificação de intenção em PT-BR."""
    lista = _formatar_lista_sinais(sinais)
    return (
        "Você é um classificador de intenções para uma mão robótica que executa sinais (gestos).\n"
        "Sua tarefa: dada uma fala/texto do usuário em português, escolha QUAL DOS SINAIS abaixo "
        "melhor representa a intenção dele.\n\n"
        "SINAIS DISPONÍVEIS:\n"
        f"{lista}\n\n"
        "REGRAS:\n"
        '- Responda APENAS em JSON válido com o formato: {"sinal": "id_do_sinal"}.\n'
        '- Se NENHUM sinal se aplicar, responda: {"sinal": "nenhum"}.\n'
        "- O campo \"sinal\" deve conter EXATAMENTE um dos ids listados acima, ou \"nenhum\".\n"
        "- Não inclua explicações, comentários ou texto fora do JSON.\n\n"
        f'FALA DO USUÁRIO: "{texto_usuario}"\n\n'
        "JSON:"
    )


def classificar_intencao(
    texto_usuario: str,
    sinais: list[dict],
    *,
    model: str = MODEL,
    url: str = OLLAMA_URL,
    timeout: int = TIMEOUT_SEGUNDOS,
) -> Optional[dict]:
    """
    Classifica o texto do usuário e devolve o dicionário do sinal escolhido
    (com `id`, `nome`, `angulos`, ...), ou `None` se nenhum sinal corresponder.

    Levanta `OllamaError` se a chamada falhar ou se a resposta for inválida.
    """
    if not texto_usuario or not texto_usuario.strip():
        return None
    if not sinais:
        logger.warning("Nenhum sinal cadastrado — Ollama não tem o que escolher.")
        return None

    prompt = _montar_prompt(texto_usuario.strip(), sinais)

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        raise OllamaError(
            "Não consegui conectar no Ollama em "
            f"{url}. O serviço está rodando? (Tente `ollama list` no PowerShell.)"
        ) from e
    except requests.exceptions.Timeout as e:
        raise OllamaError(
            f"Ollama demorou mais de {timeout}s para responder. "
            "Modelo pode estar carregando — tente de novo em alguns segundos."
        ) from e
    except requests.exceptions.HTTPError as e:
        raise OllamaError(f"Ollama retornou HTTP {resp.status_code}: {resp.text}") from e

    try:
        raw = resp.json().get("response", "")
        parsed = json.loads(raw)
    except (ValueError, KeyError) as e:
        raise OllamaError(
            f"Resposta do Ollama não veio em JSON válido: {resp.text!r}"
        ) from e

    sinal_id = (parsed.get("sinal") or "").strip().lower()
    logger.info("Ollama escolheu: %r (texto=%r)", sinal_id, texto_usuario)

    if not sinal_id or sinal_id == "nenhum":
        return None

    for s in sinais:
        if s["id"].lower() == sinal_id:
            return s

    # O modelo respondeu um id que não existe no signs.json — trata como nenhum.
    logger.warning(
        "Ollama retornou id desconhecido %r (sinais disponíveis: %s)",
        sinal_id,
        [s["id"] for s in sinais],
    )
    return None


def healthcheck(*, url: str = OLLAMA_URL.replace("/api/generate", "/api/tags"),
                model: str = MODEL) -> dict:
    """
    Checa se o Ollama está no ar e se o modelo desejado está instalado.
    Retorna um dict com `online: bool` e `modelo_instalado: bool`.
    """
    info = {"online": False, "modelo_instalado": False, "modelos": []}
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        info["online"] = True
        modelos = [m.get("name", "") for m in resp.json().get("models", [])]
        info["modelos"] = modelos
        info["modelo_instalado"] = any(m.startswith(model) for m in modelos)
    except requests.exceptions.RequestException:
        pass
    return info
