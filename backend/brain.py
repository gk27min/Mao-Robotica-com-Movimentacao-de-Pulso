import re
import logging
import ollama
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brain")

# Gestos disponíveis: ID → (Descrição semântica e física, palavras-chave para fallback)
GESTOS = {
    0: ("Mão totalmente fechada / Punho", ["fechar", "punho", "zero", "0", "fechada"]),
    1: ("Apontar (Apenas indicador aberto)", ["apontar", "indicador", "ponto", "um", "1", "direção"]),
    2: ("Paz e Vitória (Indicador e médio abertos)", ["paz", "vitoria", "vitória", "peace", "victory", "dois", "2", "v"]),
    3: ("Três (Indicador, médio e anelar abertos)", ["tres", "três", "3"]),
    4: ("Quatro (Indicador, médio, anelar e mindinho abertos, polegar fechado)", ["quatro", "4", "B em libras"]),
    5: ("Mão totalmente aberta / Descanso", ["abrir", "aberta", "estender", "todos", "dedos", "cinco", "5", "espalmar", "pare", "descanso", "repouso", "posição inicial"]),
    6: ("Sinal Eu te amo em LIBRAS (Polegar, indicador e mindinho abertos)", ["amo", "love", "libras", "te amo", "ily"]),
    7: ("Joinha / Positivo (Apenas polegar aberto)", ["joinha", "positivo", "bom", "legal", "like", "curtir", "polegar", "cima"]),
    8: ("Dedo do meio (Apenas dedo médio aberto)", ["meio", "dedo do meio", "ofensivo", "médio", "xingamento"]),
    9: ("Hang Loose / Shaka (Polegar e mindinho abertos)", ["hanglose", "hang loose", "shaka", "surf", "surfista", "telefone", "alô", "🤙"]),
    10: ("Rock and Roll (Indicador e mindinho abertos)", ["rock", "metal", "chifres", "horns", "🤘"]),
    11: ("Aceno (Mão aberta com oscilação do pulso)", ["aceno", "acenar", "tchau", "oi", "olá", "hello", "wave", "saudação", "cumprimentar"]),
    12: ("Letra I em LIBRAS (Apenas mindinho estendido)", ["i", "letra i", "libras i", "mindinho"]),
    13: ("Letra L em LIBRAS (Polegar e indicador formando um L)", ["l", "letra l", "libras l", "loser", "faz o l"]),
    14: ("Sinal de OK", ["ok", "certo", "tudo certo", "concordo", "beleza", "perfeito"]),
    15: ("Sinal de Não (Dedo indicador estendido com oscilação de pulso)", ["nao", "não", "negativo", "recusa", "discordo", "rejeitar"]),
    16: ("Sinal de Água em LIBRAS (Indicador batendo repetidas vezes)", ["agua", "água", "sede", "beber", "libras agua"])
}

LLM_MODEL = "phi3"

# Bloco de texto que descreve os gestos, reutilizado no prompt do LLM
_GESTOS_PROMPT = "\n".join(
    f"  ID {gid}: {desc}" for gid, (desc, _) in GESTOS.items()
)

_PROMPT_TEMPLATE = """\
Você é o cérebro lógico de uma mão robótica de LIBRAS. 
Sua ÚNICA saída deve ser uma sequência de números inteiros separados por vírgula (ex: 2 ou 5,5,2). Não escreva NENHUM texto adicional, justificativa ou formatação.

Gestos disponíveis (ID: Descrição):
{gestos}

REGRAS DE PROCESSAMENTO:
1. COMANDOS DIRETOS: Se a entrada descrever um gesto explicitamente (ex: "faça o sinal de paz", "letra L"), retorne o ID correspondente.
2. PERGUNTAS OBJETIVAS E CONHECIMENTOS GERAIS: Se a entrada for uma pergunta com resposta numérica (ex: "quantas rodas tem um carro?", "qual a raiz quadrada de 9?"), descubra a resposta lógica/matemática PRIMEIRO.
3. DECOMPOSIÇÃO DE NÚMEROS (IMPORTANTE): Se a resposta numérica for MAIOR que 5, você DEVE decompor o valor usando o gesto 5 repetidas vezes, somado ao resto.
   - Exemplo A: Resposta 12 -> Retorne: 5,5,2
   - Exemplo B: Resposta 7 -> Retorne: 5,2
   - Exemplo C: Resposta 15 -> Retorne: 5,5,5
   - Exemplo D: "duas vezes três" -> Resposta 6 -> Retorne: 5,1
4. NÚMEROS ATÉ 5: Se a resposta for 5 ou menor, retorne apenas o número (ex: "dois mais dois" -> Retorne: 4).
5. CASO INVÁLIDO: Se a pergunta for impossível de responder ou não se encaixar em gestos/números, retorne -1.

Entrada do usuário: "{texto}"
Saída esperada (apenas números e vírgulas):
"""


class MapeadorDeSinais:
    def __init__(self, llm_model: str = LLM_MODEL):
        self.llm_model = llm_model
        logger.info(f"MapeadorDeSinais iniciado com modelo '{self.llm_model}'.")

    async def _classificar_com_llm(self, texto: str) -> Optional[list]:
        """Pede ao LLM uma sequência de IDs (0-16). Retorna uma lista de inteiros."""
        prompt = _PROMPT_TEMPLATE.format(gestos=_GESTOS_PROMPT, texto=texto)
        try:
            client = ollama.AsyncClient()
            response = await client.generate(model=self.llm_model, prompt=prompt)
            raw = response["response"].strip()
            logger.info(f"LLM bruto: '{raw}'")

            # Acha todos os números na resposta (ex: de "5, 5, 2" extrai ['5', '5', '2'])
            numeros = re.findall(r"-?\d+", raw)
            if numeros:
                # Converte para int e filtra apenas os IDs válidos do seu projeto (0 a 16)
                gids = [int(n) for n in numeros if -1 <= int(n) <= 16]
                if gids:
                    return gids # Agora retorna uma lista!
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

    async def processar_comando(self, texto_usuario: str) -> Tuple[Optional[list], Optional[str], float]:
        """
        Retorna (lista_de_ids, descricao_combinada, confianca).
        """
        if not texto_usuario or not texto_usuario.strip():
            return None, None, 0.0

        texto = texto_usuario.strip()

        # Estágio 1: LLM
        gids = await self._classificar_com_llm(texto)
        if gids:
            # Pega a descrição de cada número na lista e junta tudo
            descricoes = [GESTOS[g][0] for g in gids if g in GESTOS]
            desc_combinada = " + ".join(descricoes)
            logger.info(f"LLM → sequência {gids}: '{desc_combinada}'")
            return gids, desc_combinada, 1.0

        # Estágio 2: fallback por palavras-chave
        logger.warning("LLM falhou ou retornou vazio. Tentando fallback por keywords.")
        gid_fallback = self._classificar_por_keywords(texto)
        if gid_fallback is not None:
            desc = GESTOS[gid_fallback][0]
            # Retorna como uma lista de 1 item para manter a compatibilidade
            return [gid_fallback], desc, 0.75

        logger.warning(f"Nenhum gesto reconhecido para: '{texto}'")
        return None, None, 0.0
