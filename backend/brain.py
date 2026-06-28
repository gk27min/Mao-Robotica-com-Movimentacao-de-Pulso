import re
import logging
import ollama
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brain")

# Gestos disponíveis: ID → (descrição curta, palavras-chave para fallback)
GESTOS = {
    0: ("Descanso / mão fechada",       ["descanso", "parar", "fechar", "repouso", "zero", "pausa"]),
    1: ("Mão aberta",                   ["abrir", "aberta", "estender", "todos", "dedos"]),
    2: ("Apontar / indicador",          ["apontar", "indicador", "ponto"]),
    3: ("Paz / Vitória",                ["paz", "vitoria", "vitória", "peace", "victory"]),
    4: ("Tchau / Cumprimento",          ["tchau", "ola", "olá", "acenar", "cumprimento"]),
    5: ("Joinha / Positivo",            ["joinha", "positivo", "polegar", "like", "ok"]),
    6: ("Eu te amo (LIBRAS)",           ["amo", "love", "libras", "ite"]),
}

LLM_MODEL = "gpt-oss:latest"

# Bloco de texto que descreve os gestos, reutilizado no prompt do LLM
_GESTOS_PROMPT = "\n".join(
    f"  ID {gid}: {desc}" for gid, (desc, _) in GESTOS.items()
)

_PROMPT_TEMPLATE = """\
Você é um classificador de comandos para uma mão robótica. Sua única saída deve ser um único número inteiro.

Gestos disponíveis:
{gestos}

Regras de classificação:
1. Se a entrada for uma expressão matemática, resolva-a PRIMEIRO.
   - Se o resultado for um ID válido (0-6), retorne esse ID diretamente.
   - Se o resultado estiver fora do intervalo, retorne o ID cujo gesto seja semanticamente mais próximo do número.
   - Exemplos: "quanto é 3 - 3?" → 3-3=0 → retorne 0
               "quanto é 2 + 1?" → 2+1=3 → retorne 3
               "metade de 10"    → 5 → retorne 5
2. Se a entrada for um comando de voz ou descrição, identifique o gesto correspondente e retorne seu ID.
3. Se não for possível determinar com confiança, retorne -1.

Entrada do usuário: "{texto}"

Responda APENAS com um único número inteiro (0 a 6, ou -1). Sem explicações, sem texto adicional.\
"""


class MapeadorDeSinais:
    def __init__(self, llm_model: str = LLM_MODEL):
        self.llm_model = llm_model
        logger.info(f"MapeadorDeSinais iniciado com modelo '{self.llm_model}'.")

    async def _classificar_com_llm(self, texto: str) -> Optional[int]:
        """Pede ao LLM um ID de gesto (0–6). Retorna None em caso de falha ou -1."""
        prompt = _PROMPT_TEMPLATE.format(gestos=_GESTOS_PROMPT, texto=texto)
        try:
            client = ollama.AsyncClient()
            response = await client.generate(model=self.llm_model, prompt=prompt)
            raw = response["response"].strip()
            logger.info(f"LLM bruto: '{raw}'")

            match = re.search(r"-?\d+", raw)
            if match:
                gid = int(match.group())
                if 0 <= gid <= 6:
                    return gid
        except Exception as e:
            logger.error(f"Erro ao chamar LLM: {e}")
        return None

    def _classificar_por_keywords(self, texto: str) -> Optional[int]:
        """Fallback simples por palavras-chave caso o LLM falhe."""
        texto_lower = texto.lower()
        for gid, (_, keywords) in GESTOS.items():
            if any(kw in texto_lower for kw in keywords):
                logger.info(f"Keyword match: gesto {gid}")
                return gid
        return None

    async def processar_comando(self, texto_usuario: str) -> Tuple[Optional[int], Optional[str], float]:
        """
        Retorna (id_gesto, descricao, confianca).
        confianca = 1.0 (LLM), 0.75 (keyword), 0.0 (falha).
        """
        if not texto_usuario or not texto_usuario.strip():
            return None, None, 0.0

        texto = texto_usuario.strip()

        # Estágio 1: LLM
        gid = await self._classificar_com_llm(texto)
        if gid is not None:
            desc = GESTOS[gid][0]
            logger.info(f"LLM → gesto {gid}: '{desc}'")
            return gid, desc, 1.0

        # Estágio 2: fallback por palavras-chave
        logger.warning("LLM falhou ou retornou -1. Tentando fallback por keywords.")
        gid = self._classificar_por_keywords(texto)
        if gid is not None:
            desc = GESTOS[gid][0]
            return gid, desc, 0.75

        logger.warning(f"Nenhum gesto reconhecido para: '{texto}'")
        return None, None, 0.0
