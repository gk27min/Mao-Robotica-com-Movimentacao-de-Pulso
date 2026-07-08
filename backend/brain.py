import re
import logging
import ollama
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brain")

# Gestos disponíveis: ID → (Descrição semântica e física, palavras-chave para fallback)
GESTOS = {
    # ==========================================
    # BLOCO 1: ESTÁTICOS (Pulso Fixo) -> 0 a 17
    # ==========================================
    0: ("CM - 000: Mão totalmente fechada", ["fechar", "punho", "zero", "fechada"]),
    1: ("CM - 001: Dedo indicador", ["apontar", "indicador", "ponto", "direção"]),
    2: ("CM - 002: Indicador e médio", ["paz", "vitoria", "vitória", "peace", "victory"]),
    3: ("CM - 003: Indicador, médio e anelar", ["tres", "três"]),
    4: ("CM - 004: Indicador, médio, anelar e mindinho", ["quatro"]),
    5: ("CM - 005: Todos os dedos", ["abrir", "aberta", "estender", "todos", "dedos", "cinco", "espalmar", "pare", "descanso", "repouso", "posição inicial"]),
    6: ("CM - 006: Polegar, indicador e mindinho", ["amo", "love", "te amo", "ily"]),
    7: ("CM - 007: Polegar", ["joinha", "positivo", "bom", "legal", "like", "curtir", "polegar", "valeu"]),
    8: ("CM - 008: Dedo médio", ["dedo do meio", "ofensivo", "médio", "xingamento"]),
    9: ("CM - 009: Polegar e mindinho", ["hanglose", "hang loose", "shaka", "surf", "surfista", "telefone", "alô"]),
    10: ("CM - 010: Indicador e mindinho", ["rock", "metal", "chifres", "horns"]),
    11: ("CM - 011: Mindinho", ["letra i", "libras i", "mindinho"]),
    12: ("CM - 012: Polegar e indicador", ["letra l", "libras l", "loser", "faz o l"]),
    13: ("CM - 013: Médio, anelar e mindinho", ["ok", "certo", "tudo certo", "concordo", "beleza", "perfeito"]),
    14: ("CM - 014: Letra C em LIBRAS (Dedos curvados)", ["letra c", "libras c"]),
    15: ("CM - 015: Letra A em LIBRAS", ["letra a", "libras a"]),
    16: ("CM - 016: Letra O em LIBRAS (Dedos formando um círculo)", ["letra o", "libras o", "zero libras"]),
    17: ("CM - 017: Base para Letra H (Indicador e médio estendidos, polegar lateral)", ["base h"]),

    # ==========================================
    # BLOCO 1.1: ESTÁTICOS COM MOV. DE DEDOS -> 18 a 20
    # ==========================================
    18: ("CM - 018: Sinal de Água (Indicador batendo repetidas vezes)", ["agua", "água", "sede", "beber"]),
    19: ("CM - 019: Sinal de Aspas (Indicador e médio dobrando repetidas vezes)", ["aspas", "citação", "quote", "entre aspas"]),
    20: ("CM - 020: Reservado para futuros", ["reservado"]),

    # ==========================================
    # BLOCO 2: DINÂMICOS (Com oscilação do pulso) -> 100 a 120
    # ==========================================
    100: ("CM - 100: Mão totalmente fechada com oscilação", ["bater", "soco", "bater na porta"]),
    101: ("CM - 101: Dedo indicador com oscilação (Sinal de Não)", ["nao", "não", "negativo", "recusa", "discordo", "rejeitar"]),
    102: ("CM - 102: Indicador e médio com oscilação", ["observar", "olhar"]),
    103: ("CM - 103: Indicador, médio e anelar com oscilação", ["tres balançando"]),
    104: ("CM - 104: Indicador, médio, anelar e mindinho com oscilação", ["quatro balançando"]),
    105: ("CM - 105: Todos os dedos com oscilação (Aceno)", ["aceno", "acenar", "tchau", "oi", "olá", "ola", "hello", "wave", "saudação", "cumprimentar", "e ai", "e aí"]),
    106: ("CM - 106: Polegar, indicador e mindinho com oscilação", ["te amo balançando", "ily com movimento"]),
    107: ("CM - 107: Polegar com oscilação", ["joinha balançando", "positivo balançando"]),
    108: ("CM - 108: Dedo médio com oscilação", ["médio balançando"]),
    109: ("CM - 109: Polegar e mindinho com oscilação", ["shaka balançando", "telefone balançando"]),
    110: ("CM - 110: Indicador e mindinho com oscilação", ["rock balançando"]),
    111: ("CM - 111: Mindinho com oscilação", ["mindinho balançando"]),
    112: ("CM - 112: Polegar e indicador com oscilação", ["letra l balançando"]),
    113: ("CM - 113: Médio, anelar e mindinho com oscilação", ["ok balançando"]),
    114: ("CM - 114: Letra C com oscilação do pulso", ["c balançando"]),
    115: ("CM - 115: Letra A com oscilação do pulso", ["a balançando"]),
    116: ("CM - 116: Letra O com oscilação do pulso", ["o balançando"]),
    117: ("CM - 117: Letra H em LIBRAS (Base do H com rotação do pulso)", ["letra h", "libras h"]),
    118: ("CM - 118: Sinal de Água com oscilação do pulso", ["agua balançando"]),
    119: ("CM - 119: Sinal de Aspas com oscilação do pulso", ["aspas balançando"]),
    120: ("CM - 120: Reservado com oscilação", ["reservado balançando"]),
}
LLM_MODEL = "llama3.1"

# Bloco de texto que descreve os gestos, reutilizado no prompt do LLM
_GESTOS_PROMPT = "\n".join(
    f"  ID {gid}: {desc}" for gid, (desc, _) in GESTOS.items()
)

_PROMPT_TEMPLATE = """\
Você é o controlador de uma mão robótica de LIBRAS.
Sua tarefa: dada a frase do usuário, escolher O ÚNICO gesto da lista abaixo
que melhor representa o que a frase quer dizer.

Sua ÚNICA saída permitida é uma destas duas formas:
  - "GESTO: <ID>"  (usando um ID que EXISTE na lista abaixo)
  - "NENHUM"       (quando nada na lista se encaixa na frase)
PROIBIDO escrever qualquer outra coisa, explicação ou texto extra.

GESTOS DISPONÍVEIS (ID: Descrição):
{gestos}

EXEMPLOS (siga exatamente este formato):
Entrada: "Oi"
Saída: GESTO: 105

Entrada: "Tchau, até mais"
Saída: GESTO: 105

Entrada: "Abre a mão"
Saída: GESTO: 5

Entrada: "Fecha a mão"
Saída: GESTO: 0

Entrada: "Manda um joinha"
Saída: GESTO: 7

Entrada: "Te amo"
Saída: GESTO: 6

Entrada: "Faz o sinal de paz"
Saída: GESTO: 2

Entrada: "Não"
Saída: GESTO: 101

Entrada: "asdfghjkl"
Saída: NENHUM

Entrada: "{texto}"
Saída: """


class MapeadorDeSinais:
    def __init__(self, llm_model: str = LLM_MODEL):
        self.llm_model = llm_model
        logger.info(f"MapeadorDeSinais iniciado com modelo '{self.llm_model}'.")

    async def _classificar_com_llm(self, texto: str) -> Optional[int]:
        prompt = _PROMPT_TEMPLATE.format(gestos=_GESTOS_PROMPT, texto=texto)
        try:
            client = ollama.AsyncClient()
            response = await client.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    "temperature": 0.0,
                    "top_p": 0.1,
                    "num_predict": 10,  # basta pra "GESTO: NNN" ou "NENHUM"
                },
            )

            raw = response["response"].strip().upper()
            logger.info(f"LLM bruto: '{raw}'")

            # O modelo explicitamente não encontrou gesto
            if "NENHUM" in raw:
                return None

            # Extrai o ID e valida contra a tabela real
            match = re.search(r"GESTO:\s*(\d+)", raw)
            if match:
                gid = int(match.group(1))
                if gid in GESTOS:          # <- aceita a biblioteca inteira (0-20, 100-120)
                    return gid
                logger.warning(f"LLM retornou ID {gid} fora da tabela GESTOS.")

        except Exception as e:
            logger.error(f"Erro ao chamar LLM: {e}")
        return None

    def _classificar_por_keywords(self, texto: str) -> Optional[int]:
        """Fallback por palavras-chave (correspondência por palavra inteira)."""
        texto_lower = texto.lower()
        for gid, (_, keywords) in GESTOS.items():
            for kw in keywords:
                # Ignora keywords de 1 caractere: "i", "a", "o" casariam dentro
                # de qualquer palavra ("oi", "a mão") e geram falsos positivos.
                if len(kw) < 2:
                    continue
                # \b garante palavra/expressão inteira, não substring solta.
                if re.search(rf"\b{re.escape(kw)}\b", texto_lower):
                    logger.info(f"Keyword '{kw}' → gesto {gid}")
                    return gid
        return None

    async def processar_comando(self, texto_usuario: str) -> Tuple[Optional[list], Optional[str], float]:
        """
        Retorna (lista_de_ids, descricao, confianca).
        A lista sempre tem no máximo 1 gesto (1 sinal por frase).
        """
        if not texto_usuario or not texto_usuario.strip():
            return None, None, 0.0

        texto = texto_usuario.strip()

        # Estágio 1: LLM
        gid = await self._classificar_com_llm(texto)
        if gid is not None:
            desc = GESTOS[gid][0]
            logger.info(f"LLM → gesto {gid}: '{desc}'")
            return [gid], desc, 1.0

        # Estágio 2: fallback por palavras-chave
        logger.warning("LLM não retornou gesto. Tentando fallback por keywords.")
        gid_fallback = self._classificar_por_keywords(texto)
        if gid_fallback is not None:
            desc = GESTOS[gid_fallback][0]
            return [gid_fallback], desc, 0.75

        logger.warning(f"Nenhum gesto reconhecido para: '{texto}'")
        return None, None, 0.0