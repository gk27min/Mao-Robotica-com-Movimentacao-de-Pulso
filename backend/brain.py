import json
import logging
import ollama
from typing import Optional, Tuple, List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brain")

# Gestos disponíveis: ID → (descrição curta, palavras-chave para fallback)
GESTOS = {
    0: ("Mão fechada / Zero",      ["zero", "0", "fechar", "punho", "nada", "vazio", "nulo"]),
    1: ("Número Um",               ["um", "1", "primeiro", "unico", "apontar", "atenção", "foco", "destaque"]),
    2: ("Número Dois / Paz",       ["dois", "2", "segundo", "duas", "paz", "vitoria", "peace", "duplo", "vencer"]),
    3: ("Número Três",             ["tres", "três", "3", "terceiro", "triplo"]),
    4: ("Número Quatro",           ["quatro", "4", "quarto", "quadruplo"]),
    5: ("Número Cinco / Aberta",   ["cinco", "5", "quinto", "abrir", "aberta", "pare", "stop", "todos", "espalmado", "alto"]),
    6: ("Eu te amo (LIBRAS)",      ["amo", "amor", "love", "apaixonado", "carinho", "te amo", "romance", "coracao"]),
    7: ("Joia / Positivo / Sim",   ["joia", "positivo", "sim", "concordo", "legal", "bom", "certo", "like", "beleza", "aprovado", "correto", "exato"]),
    8: ("Dedo do meio / Raiva",    ["xingamento", "ofensa", "raiva", "bravo", "irritado", "odio", "insulto", "ruim"]),
    9: ("Surfista / Hang Loose",   ["surfista", "hang loose", "tranquilo", "suave", "shaka", "praia", "relaxa", "de boa", "calma"]),
    10: ("Rock / Chifres",         ["rock", "metal", "heavy metal", "chifre", "festa", "irado", "show", "empolgado", "musica"]),
    11: ("Aceno / Tchau / Oi",     ["tchau", "ola", "olá", "oi", "saudacao", "despedida", "adeus", "acenar", "bem-vindo", "chegada", "partida"]),
    12: ("Letra I (LIBRAS)",       ["letra i", "i", "vogal i", "i em libras", "mim", "eu"]),
    13: ("Letra L (LIBRAS)",       ["letra l", "l", "consoante l", "l em libras", "perdedor", "loser"]),
    14: ("Sinal de OK",            ["ok", "perfeito", "excelente", "maravilha", "combinado", "tudo bem", "certissimo", "pronto"]),
    15: ("Não / Negativo",         ["nao", "não", "negativo", "errado", "discordo", "recusa", "proibido", "rejeitado", "nunca", "jamais", "incorreto"]),
    16: ("Água (LIBRAS)",          ["agua", "água", "beber", "sede", "liquido", "hidratação", "tomar", "copo"])
}

LLM_MODEL = "phi3"

# Bloco de texto que descreve os gestos, reutilizado no prompt do LLM
_GESTOS_PROMPT = "\n".join(
    f"  ID {gid}: {desc}" for gid, (desc, _) in GESTOS.items()
)

_PROMPT_TEMPLATE = """\
Você é o cérebro de inteligência artificial do LIBRAS-BOT, uma mão robótica física.
Você DEVE responder APENAS com um objeto JSON válido.

Sua resposta pode enviar uma lista de ações para a mão usando DOIS protocolos:
1. Gestos Padrão (G): Use quando a intenção do usuário corresponder aos gestos cadastrados no banco de dados. Formato: "<G:ID>"
2. Modo Marionete (R): Use APENAS para movimentos anatômicos específicos não cadastrados solicitados pelo usuário. Formato: "<R:ang1,ang2,ang3,ang4,ang5,ang_pulso>". 

LÓGICA MECÂNICA DOS MOTORES (Regra estrita para o Modo R):
A ordem do array é: [mindinho, anelar, meio, indicador, polegar, pulso].
Os dedos possuem mecânicas invertidas:
- Mindinho, Anelar e Meio: Contraído/Fechado = 180 | Esticado/Aberto = 0.
- Indicador e Polegar: Contraído/Fechado = 0 | Esticado/Aberto = 180.
- Pulso: Varia de 0 a 180 (o centro/repouso é 120).

Gestos disponíveis no banco de dados:
{gestos}

REGRAS DE COMPOSIÇÃO NUMÉRICA E MATEMÁTICA:
- Você NUNCA deve inventar gestos para números usando o Modo R. Use apenas os numerais do banco de dados (1 a 5) e o 0 (mão fechada/descanso).
- Para dígitos de 6 a 9, use uma representação aditiva em base 5. Mostre o 5, faça a Mão Fechada (0) como transição, e depois mostre o resto.
  * Exemplo para 7: ["<G:5>", "<G:0>", "<G:2>"]
  * Exemplo para 9: ["<G:5>", "<G:0>", "<G:4>"]
- Se a resposta for um número composto pequeno (ex: 10 ou 12), some os valores.
  * Exemplo para 10: ["<G:5>", "<G:0>", "<G:5>"]
  * Exemplo para 12: ["<G:5>", "<G:0>", "<G:5>", "<G:0>", "<G:2>"]

Entrada do usuário: "{texto}"

Responda APENAS com este JSON puro (sem markdown ```json):
{{
  "resposta_texto": "Sua resposta natural em texto para o app",
  "sequencia_gestos": ["comando1", "comando2"]
}}
"""


class MapeadorDeSinais:
    def __init__(self, llm_model: str = LLM_MODEL):
        self.llm_model = llm_model
        logger.info(f"MapeadorDeSinais iniciado com modelo '{self.llm_model}'.")

    @staticmethod
    def _cmd_valido(cmd: object) -> bool:
        """Valida se um item da sequencia_gestos tem o formato correto."""
        if not isinstance(cmd, str):
            return False
        if cmd.startswith('<G:') and cmd.endswith('>'):
            try:
                gid = int(cmd[3:-1])
                return 0 <= gid < len(GESTOS)
            except ValueError:
                return False
        if cmd.startswith('<R:') and cmd.endswith('>'):
            partes = cmd[3:-1].split(',')
            return len(partes) == 6 and all(p.strip().lstrip('-').isdigit() for p in partes)
        return False

    async def _classificar_com_llm(self, texto: str) -> Optional[Dict]:
        """Pede ao LLM uma sequência de comandos formatados. Retorna None em caso de falha."""
        prompt = _PROMPT_TEMPLATE.format(gestos=_GESTOS_PROMPT, texto=texto)
        raw = ""
        try:
            client = ollama.AsyncClient()
            response = await client.generate(model=self.llm_model, prompt=prompt, format='json')
            raw = response["response"].strip()
            logger.info(f"LLM bruto: '{raw}'")

            data = json.loads(raw)
            sequencia = data.get("sequencia_gestos", [])
            resposta_texto = data.get("resposta_texto", "")

            cmds_validos = [cmd for cmd in sequencia if self._cmd_valido(cmd)]
            if cmds_validos:
                return {"resposta_texto": resposta_texto, "sequencia_gestos": cmds_validos}

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Erro ao parsear JSON do LLM: {e}. Resposta bruta: '{raw}'")
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

    async def processar_comando(self, texto_usuario: str) -> Tuple[Optional[List[str]], Optional[str], float]:
        """
        Retorna (sequencia_gestos, resposta_texto, confianca).
        confianca = 1.0 (LLM), 0.75 (keyword), 0.0 (falha).
        """
        if not texto_usuario or not texto_usuario.strip():
            return None, None, 0.0

        texto = texto_usuario.strip()

        # Estágio 1: LLM
        resultado = await self._classificar_com_llm(texto)
        if resultado is not None:
            sequencia = resultado["sequencia_gestos"]
            resposta_texto = resultado["resposta_texto"]
            logger.info(f"LLM → sequência {sequencia}: '{resposta_texto}'")
            return sequencia, resposta_texto, 1.0

        # Estágio 2: fallback por palavras-chave
        logger.warning("LLM falhou. Tentando fallback por keywords.")
        gid = self._classificar_por_keywords(texto)
        if gid is not None:
            desc = GESTOS[gid][0]
            return [f"<G:{gid}>"], desc, 0.75

        logger.warning(f"Nenhum gesto reconhecido para: '{texto}'")
        return None, None, 0.0
