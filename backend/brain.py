import logging
import numpy as np
import ollama
from typing import Optional, Tuple

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brain")

class MapeadorDeSinais:
    def __init__(self, model_name: str = "nomic-embed-text", threshold: float = 0.70):
        """
        Inicializa o mapeador de sinais sem banco de dados (Zero-DB).
        Pré-calcula e armazena os embeddings em memória RAM utilizando numpy.
        """
        self.model_name = model_name
        self.threshold = threshold
        
        # Mapeamento fixo de frases descritivas típicas para os códigos físicos (bytes)
        self.sinais_map = {
            # Gestos baseados no pedido do usuário e adicionais comuns
            "desligar a mão / parar motores / modo descanso / fechar": 0,
            "ligar led de teste / acender luz / ligar placa": 1,
            "fazer sinal de paz / paz e amor / vitória": 3,
            "dar tchau / acenar / tchau / olá / oi / cumprimento": 4,
            "dedo do meio / sinal ofensivo / dedo do meio levantado": 5,
            "fazer sinal de positivo / joinha / tudo bem / ok": 6,
            "sinal de eu te amo / i love you / amor em libras": 7,
        }
        
        self.cached_embeddings = []
        self.is_initialized = False
        
        # Gera os embeddings ao iniciar a classe
        self.inicializar_embeddings()

    def inicializar_embeddings(self):
        """
        Consulta a API local do Ollama para gerar os vetores das chaves descritivas
        e os armazena em RAM usando NumPy.
        """
        try:
            logger.info(f"Pré-calculando embeddings em RAM usando o modelo '{self.model_name}'...")
            self.cached_embeddings = []
            
            for descricao, codigo in self.sinais_map.items():
                # Chamada oficial da biblioteca python do ollama
                response = ollama.embeddings(model=self.model_name, prompt=descricao)
                vector = np.array(response["embedding"])
                
                # Armazena a descrição, o código do comando e o vetor gerado
                self.cached_embeddings.append((descricao, codigo, vector))
                
            self.is_initialized = True
            logger.info(f"Embeddings de {len(self.cached_embeddings)} gestos cacheados em memória com sucesso!")
        except Exception as e:
            logger.error(
                f"Falha ao gerar embeddings no startup: {e}. "
                "Certifique-se de que o Ollama está rodando ('ollama serve') e o modelo está baixado."
            )
            self.is_initialized = False

    async def processar_comando(self, texto_usuario: str) -> Tuple[Optional[int], Optional[str], float]:
        """
        Gera o vetor do texto do usuário de forma assíncrona, calcula a Similaridade de Cosseno nativa
        com NumPy e retorna o código correspondente caso ultrapasse o threshold definido.
        Retorna (codigo_sinal, descricao, similaridade).
        """
        if not texto_usuario or not texto_usuario.strip():
            logger.warning("Texto de entrada vazio.")
            return None, None, 0.0

        # Mecanismo de auto-cura: se falhou no startup, tenta gerar os embeddings agora
        if not self.is_initialized or not self.cached_embeddings:
            self.inicializar_embeddings()
            if not self.is_initialized:
                logger.error("Erro: O Ollama está inacessível e os embeddings não foram inicializados.")
                return None, None, 0.0

        try:
            # 1. Gerar o embedding da frase do usuário usando o cliente assíncrono do Ollama
            texto_limpo = texto_usuario.strip().lower()
            async_client = ollama.AsyncClient()
            response = await async_client.embeddings(model=self.model_name, prompt=texto_limpo)
            query_vector = np.array(response["embedding"])

            best_similarity = -1.0
            best_match_desc = None
            best_match_code = None

            # 2. Calcular a similaridade de cosseno contra os vetores cacheados na RAM
            for descricao, codigo, vector in self.cached_embeddings:
                # Similaridade de Cosseno = (A . B) / (||A|| * ||B||)
                dot_product = np.dot(query_vector, vector)
                norm_q = np.linalg.norm(query_vector)
                norm_v = np.linalg.norm(vector)

                if norm_q == 0 or norm_v == 0:
                    similarity = 0.0
                else:
                    similarity = float(dot_product / (norm_q * norm_v))

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_desc = descricao
                    best_match_code = codigo

            logger.info(f"Semântica: '{texto_limpo}' -> '{best_match_desc}' (Similaridade Cosseno: {best_similarity:.4f})")

            # 3. Validar contra o limite de aceitação
            if best_similarity >= self.threshold:
                logger.info(f"Comando validado: Código {best_match_code}")
                return best_match_code, best_match_desc, best_similarity
            else:
                logger.warning(
                    f"Comando descartado: Similaridade ({best_similarity:.4f}) abaixo do threshold de {self.threshold}."
                )
                return None, None, best_similarity

        except Exception as e:
            logger.error(f"Erro ao processar cálculo vetorial: {e}")
            return None, None, 0.0
