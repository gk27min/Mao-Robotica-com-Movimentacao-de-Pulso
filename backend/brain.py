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

LLM_MODEL = "llama3.1"

# Bloco de texto que descreve os gestos, reutilizado no prompt do LLM
_GESTOS_PROMPT = "\n".join(
    f"  ID {gid}: {desc}" for gid, (desc, _) in GESTOS.items()
)

_PROMPT_TEMPLATE = """\
Você é o controlador lógico de uma mão robótica de LIBRAS.
Sua ÚNICA saída deve ser uma sequência de números inteiros separados por vírgula. 
NUNCA escreva justificativas, introduções, textos ou formatação extra. APENAS NÚMEROS.

GESTOS DISPONÍVEIS (ID: Descrição):
{gestos}

REGRAS DE PROCESSAMENTO LÓGICO:
1. COMANDOS DIRETOS: Identifique a intenção do usuário e retorne o ID do gesto (ex: "oi", "abrir a mão", "descanso").
2. CÁLCULOS E PERGUNTAS: Descubra a resposta numérica real primeiro. 
   - Se o resultado for 5 ou menor, retorne o ID numérico diretamente.
   - Se o resultado for MAIOR que 5, decomponha o valor repetindo o número 5 somado ao resto (ex: 12 deve virar 5,5,2).
3. PROTEÇÃO CONTRA ERROS: Se a pergunta for impossível, não tiver resposta numérica ou não fizer sentido lógico, retorne EXATAMENTE 15 (Sinal de Não).

EXEMPLOS ESTRITOS (Siga este exato formato):
Entrada: "Oi"
Saída: 11

Entrada: "Abre a mão"
Saída: 5

Entrada: "Coloque a mão em descanso"
Saída: 5

Entrada: "Quanto é 1 + 1?"
Saída: 2

Entrada: "Quantos meses tem um ano?"
Saída: 5,5,2

Entrada: "Quantos dias tem uma semana?"
Saída: 5,2

Entrada: "Qual é a capital do Brasil?"
Saída: 15

Entrada: "Dê um salto mortal"
Saída: 15

Entrada: "{texto}"
Saída: """


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
