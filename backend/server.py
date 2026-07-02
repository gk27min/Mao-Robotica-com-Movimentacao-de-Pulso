import asyncio
import logging
import uvicorn
from typing import Optional, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Importação dos módulos internos
from brain import MapeadorDeSinais
from bluetooth_sender import enviar_comando_bluetooth

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

app = FastAPI(
    title="LIBRAS-BOT Backend",
    description="Servidor intermediário em Python (FalaComaMão) para processamento de voz e ponte BLE.",
    version="1.0.0"
)

# Configuração de CORS (Cross-Origin Resource Sharing)
# Permite que o aplicativo móvel Flutter conecte sem restrições
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
    codigos: Optional[List[str]] = None
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

    # 1. Camada de Processamento: LLM + fallback por keywords
    sequencia, resposta_texto, confianca = await mapeador.processar_comando(texto)

    if not sequencia:
        detalhes = resposta_texto or f"Nenhum gesto reconhecido para: '{texto}'"
        logger.warning(detalhes)
        return ComandoResponse(
            sucesso=False,
            texto_original=texto,
            comando_detectado=None,
            codigos=None,
            confianca=confianca,
            detalhes=detalhes
        )

    logger.info(f"Sequência de gestos a executar: {sequencia}")

    # 2. Camada de Comunicação: envia cada comando da sequência via Bluetooth LE
    gestos_enviados = []
    for i, comando in enumerate(sequencia):
        envio_sucesso = await enviar_comando_bluetooth(comando)
        if envio_sucesso:
            gestos_enviados.append(comando)
            logger.info(f"Comando {comando!r} enviado ({i + 1}/{len(sequencia)})")
        else:
            logger.error(f"Falha ao enviar {comando!r} ({i + 1}/{len(sequencia)})")
        # Aguarda entre comandos para os servos concluírem o movimento
        if i < len(sequencia) - 1:
            await asyncio.sleep(2.0)

    if not gestos_enviados:
        detalhes = f"Sequência mapeada, mas falhou ao enviar por Bluetooth."
        logger.error(detalhes)
        return ComandoResponse(
            sucesso=False,
            texto_original=texto,
            comando_detectado=str(sequencia),
            codigos=sequencia,
            confianca=confianca,
            detalhes=detalhes
        )

    # 3. Retorno com Sucesso
    detalhes = resposta_texto or f"{len(gestos_enviados)} comando(s) executado(s) com sucesso."
    logger.info(detalhes)
    return ComandoResponse(
        sucesso=True,
        texto_original=texto,
        comando_detectado=str(gestos_enviados),
        codigos=gestos_enviados,
        confianca=confianca,
        detalhes=detalhes
    )

if __name__ == "__main__":
    # Roda o uvicorn na porta 5000 em modo reload para facilitar o desenvolvimento
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)
