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
Sua ÚNICA saída permitida é usar um dos prefixos abaixo seguido de um número. 
PROIBIDO escrever justificativas ou textos.

GESTOS DISPONÍVEIS (ID: Descrição):
{gestos}

REGRAS DE CLASSIFICAÇÃO:
1. COMANDOS DIRETOS: Se o usuário pedir um gesto específico, retorne "GESTO: [ID]".
2. PERGUNTAS E MATEMÁTICA: Descubra a resposta numérica real e retorne "VALOR: [RESULTADO]".
3. PROTEÇÃO: Se a pergunta não tiver resposta numérica ou for impossível, retorne "GESTO: 15" (Sinal de Não).

EXEMPLOS OBRIGATÓRIOS:
Entrada: "Oi"
Saída: GESTO: 11

Entrada: "Abre a mão"
Saída: GESTO: 5

Entrada: "Quanto é 3x5?"
Saída: VALOR: 15

Entrada: "Quantos meses tem um ano?"
Saída: VALOR: 12

Entrada: "Qual é a capital da França?"
Saída: GESTO: 15

Entrada: "{texto}"
Saída: """


class MapeadorDeSinais:
    def __init__(self, llm_model: str = LLM_MODEL):
        self.llm_model = llm_model
        logger.info(f"MapeadorDeSinais iniciado com modelo '{self.llm_model}'.")

    async def _classificar_com_llm(self, texto: str) -> Optional[list]:
        prompt = _PROMPT_TEMPLATE.format(gestos=_GESTOS_PROMPT, texto=texto)
        try:
            client = ollama.AsyncClient()
            response = await client.generate(
                model=self.llm_model, 
                prompt=prompt,
                options={
                    "temperature": 0.0,
                    "top_p": 0.1,
                    "num_predict": 20 # Aumentado um pouco para caber a palavra "VALOR: X"
                }
            )
            
            # Deixa tudo maiúsculo para facilitar a busca
            raw = response["response"].strip().upper()
            logger.info(f"LLM bruto: '{raw}'")

            # CASO 1: A IA identificou que é um comando direto de GESTO
            if "GESTO:" in raw:
                match = re.search(r"GESTO:\s*(\d+)", raw)
                if match:
                    gid = int(match.group(1))
                    if 0 <= gid <= 16:
                        return [gid]
            
            # CASO 2: A IA identificou que é uma resposta matemática/conhecimento
            elif "VALOR:" in raw:
                match = re.search(r"VALOR:\s*(\d+)", raw)
                if match:
                    valor = int(match.group(1))
                    
                    if valor == 0:
                        return [0]
                    
                    # --- DECOMPOSIÇÃO FEITA PELO PYTHON (100% à prova de falhas) ---
                    sequencia = []
                    while valor > 5:
                        sequencia.append(5)
                        valor -= 5
                    
                    if valor > 0:
                        sequencia.append(valor)
                        
                    return sequencia
            
            # Fallback de segurança se a IA não mandar o formato certo
            elif raw.strip() == "15":
                return [15]

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
