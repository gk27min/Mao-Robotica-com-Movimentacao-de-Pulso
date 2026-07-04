import re
import logging
import ollama
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brain")

# Gestos disponíveis: ID → (Descrição semântica e física, palavras-chave para fallback)
GESTOS = {
    0: ("Mão totalmente fechada / Descanso", ["descanso", "parar", "fechar", "repouso", "zero", "pausa", "0", "punho", "nenhum"]),
    1: ("Apontar (Apenas indicador aberto)", ["apontar", "indicador", "ponto", "um", "1", "direção"]),
    2: ("Paz e Vitória (Indicador e médio abertos)", ["paz", "vitoria", "vitória", "peace", "victory", "dois", "2", "v"]),
    3: ("Três (Indicador, médio e anelar abertos)", ["tres", "três", "3"]),
    4: ("Quatro (Indicador, médio, anelar e mindinho abertos, polegar fechado)", ["quatro", "4", "B em libras"]),
    5: ("Mão totalmente aberta (Todos os cinco dedos estendidos)", ["abrir", "aberta", "estender", "todos", "dedos", "cinco", "5", "espalmar", "pare"]),
    6: ("Sinal Eu te amo em LIBRAS (Polegar, indicador e mindinho abertos)", ["amo", "love", "libras", "te amo", "ily"]),
    7: ("Joinha / Positivo (Apenas polegar aberto)", ["joinha", "positivo", "ok", "bom", "legal", "like", "curtir", "polegar", "cima"]),
    8: ("Dedo do meio (Apenas dedo médio aberto)", ["meio", "dedo do meio", "ofensivo", "médio", "chingamento"]),
    9: ("Hang Loose / Shaka (Polegar e mindinho abertos)", ["hanglose", "hang loose", "shaka", "surf", "telefone", "alô", "🤙"]),
    10: ("Rock and Roll (Indicador e mindinho abertos)", ["rock", "metal", "chifres", "horns", "🤘"]),
}

LLM_MODEL = "phi3"

# Bloco de texto que descreve os gestos, reutilizado no prompt do LLM
_GESTOS_PROMPT = "\n".join(
    f"  ID {gid}: {desc}" for gid, (desc, _) in GESTOS.items()
)

_PROMPT_TEMPLATE = """\
Você é um classificador de comandos matemáticos e de voz para uma mão robótica. 
Sua ÚNICA saída deve ser um único número inteiro.

Gestos disponíveis:
{gestos}

Regras de classificação matemáticas:
1. Se a entrada contiver números (mesmo escritos por extenso em português, ex: "um", "dois", "três") e operações ("mais", "menos", "vezes", "dividido"), converta-os para matemática básica e resolva a conta PRIMEIRO.
2. Exemplos de tradução matemática:
   - "um mais um" ou "quanto é um mais um" → 1+1=2 → retorne 2
   - "três menos três" → 3-3=0 → retorne 0
   - "dois mais três" → 2+3=5 → retorne 5
   - "metade de dez" → 10/2=5 → retorne 5

Regras de comandos diretos:
3. Se a entrada for apenas descritiva (ex: "faça o sinal de paz", "mão aberta"), identifique o gesto e retorne seu ID.
4. Se não for possível determinar de jeito nenhum, retorne -1.

Entrada do usuário: "{texto}"

Responda APENAS com um único número inteiro (0 a 6). Não escreva NENHUMA palavra, texto ou explicação adicional.
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
