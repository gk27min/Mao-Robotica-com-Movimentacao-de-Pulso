import logging
import uvicorn
from typing import Optional
from contextlib import asynccontextmanager  # 1. ADICIONADO AQUI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importação dos módulos internos
from brain import MapeadorDeSinais
from bluetooth_sender import enviar_comando_bluetooth, conectar_bluetooth, desconectar_bluetooth

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

# 2. COLOQUE A FUNÇÃO LIFESPAN AQUI (Substituindo os antigos @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # O que acontece no startup:
    await conectar_bluetooth()
    yield
    # O que acontece no shutdown:
    await desconectar_bluetooth()

# 3. PASSAR O LIFESPAN DENTRO DO FASTAPI
app = FastAPI(
    title="LIBRAS-BOT Backend",
    description="Servidor intermediário em Python (FalaComaMão) para processamento de voz e ponte BLE.",
    version="1.0.0",
    lifespan=lifespan  # ADICIONADO AQUI
)

# Configuração de CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialização do Mapeador de Sinais (Zero-DB)
mapeador = MapeadorDeSinais()

# =====================================================================
# MODELOS DE DADOS (Pydantic)
# =====================================================================
class ComandoRequest(BaseModel):
    texto: str

class ComandoResponse(BaseModel):
    sucesso: bool
    texto_original: str
    comando_detectado: Optional[str] = None
    codigo: Optional[int] = None
    confianca: float
    detalhes: str

# =====================================================================
# ENDPOINTS
# =====================================================================
@app.get("/")
def read_root():
    return {"status": "online", "servico": "LIBRAS-BOT Backend"}

@app.post("/api/comando", response_model=ComandoResponse)
async def processar_comando(requisicao: ComandoRequest):
    texto = requisicao.texto
    logger.info(f"Requisição recebida com texto de voz: '{texto}'")
    
    # 1. Camada de Processamento: Similaridade de Cosseno com Numpy + Ollama
    codigo, descricao, similaridade = await mapeador.processar_comando(texto)
    
    if codigo is None:
        detalhes = f"Comando descartado (Similaridade de cosseno: {similaridade:.4f} abaixo do limiar)."
        logger.warning(detalhes)
        return ComandoResponse(
            sucesso=False,
            texto_original=texto,
            comando_detectado=None,
            codigo=None,
            confianca=similaridade,
            detalhes=detalhes
        )
    
    logger.info(f"Comando compreendido e mapeado: {descricao} (Código: {codigo})")

    # 2. Camada de Comunicação: Bluetooth LE
    envio_sucesso = await enviar_comando_bluetooth(codigo)
    
    if not envio_sucesso:
        detalhes = f"Comando '{descricao}' mapeado, mas falhou ao enviar por Bluetooth para a mão robótica."
        logger.error(detalhes)
        return ComandoResponse(
            sucesso=False,
            texto_original=texto,
            comando_detectado=descricao,
            codigo=codigo,
            confianca=similaridade,
            detalhes=detalhes
        )

    # 3. Retorno com Sucesso
    detalhes = f"Comando '{descricao}' mapeado e enviado com sucesso para a mão robótica via Bluetooth."
    logger.info(detalhes)
    return ComandoResponse(
        sucesso=True,
        texto_original=texto,
        comando_detectado=descricao,
        codigo=codigo,
        confianca=similaridade,
        detalhes=detalhes
    )

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)