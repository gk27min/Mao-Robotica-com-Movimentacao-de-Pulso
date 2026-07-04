import logging
import uvicorn
import asyncio
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
    
    # 1. 'codigos' agora recebe uma LISTA
    codigos, descricao, similaridade = await mapeador.processar_comando(texto)
    
    if not codigos: # Se a lista estiver vazia
        detalhes = "Comando não compreendido pela IA."
        return ComandoResponse(sucesso=False, texto_original=texto, confianca=0.0, detalhes=detalhes)
    
    logger.info(f"Comandos compreendidos: {descricao} (Códigos: {codigos})")

    # 2. Camada de Comunicação: Envia a sequência com delay
    for cod in codigos:
        if cod == -1:
            logger.warning("Sinal de erro/inválido ignorado na sequência.")
            continue
            
        envio_sucesso = await enviar_comando_bluetooth(cod)
        
        if not envio_sucesso:
            # Se falhar no meio da sequência, aborta o resto
            detalhes = f"Falha ao enviar o código {cod} via Bluetooth."
            logger.error(detalhes)
            return ComandoResponse(
                sucesso=False, texto_original=texto, comando_detectado=descricao, confianca=similaridade, detalhes=detalhes
            )
            
        # Pausa vital para o Arduino executar o movimento físico (4 segundos)
        # Usar asyncio.sleep previne que o servidor inteiro trave durante a pausa
        await asyncio.sleep(4) 

    # 3. Retorno com Sucesso
    detalhes = f"Sequência '{descricao}' enviada com sucesso."
    return ComandoResponse(
        sucesso=True, texto_original=texto, comando_detectado=descricao, confianca=similaridade, detalhes=detalhes
    )

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)