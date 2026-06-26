import asyncio
import logging
from bleak import BleakClient

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bluetooth_sender")

# =====================================================================
# CONFIGURAÇÃO DO HARDWARE (MICROCONTROLADOR)
# =====================================================================
# ATENÇÃO: Substitua pelo MAC Address do seu microcontrolador.
# No Linux/Windows, use o formato "XX:XX:XX:XX:XX:XX".
# No macOS, use o UUID do dispositivo retornado pela varredura BLE.
DEVICE_ADDRESS = "XX:XX:XX:XX:XX:XX"

# UUIDs extraídos do firmware do Arduino (mao_robotica_ble.ino)
SERVICO_UUID = "19b10000-e8f2-537e-4f6c-d104768a1214"
CARACTERISTICA_UUID = "19b10001-e8f2-537e-4f6c-d104768a1214"
# =====================================================================

async def enviar_comando_bluetooth(codigo: int) -> bool:
    """
    Função assíncrona para conectar e enviar o código via Bluetooth Low Energy (BLE).
    Retorna True se enviado com sucesso, False em caso de falha.
    """
    # Se o endereço de teste ainda estiver configurado, simulamos o envio com sucesso
    if DEVICE_ADDRESS == "XX:XX:XX:XX:XX:XX":
        logger.warning(
            "MÓDO SIMULADO: O endereço MAC do Bluetooth está configurado como padrão ('XX:XX:XX:XX:XX:XX'). "
            f"Simulando envio do comando {codigo} com sucesso."
        )
        return True

    logger.info(f"Tentando conectar ao dispositivo BLE no endereço: {DEVICE_ADDRESS}...")
    
    try:
        # Estabelece conexão com o BleakClient
        # Definimos um timeout de 5 segundos para evitar que o endpoint FastAPI trave por muito tempo
        async with BleakClient(DEVICE_ADDRESS, timeout=5.0) as client:
            if client.is_connected:
                logger.info(f"Conectado ao dispositivo: {DEVICE_ADDRESS}")
                
                # Converte o código (int) para um único byte (bytes de tamanho 1)
                dado_para_enviar = bytes([codigo])
                
                logger.info(f"Enviando byte {codigo} para a característica {CARACTERISTICA_UUID}")
                
                # Escreve o comando na característica correspondente no Arduino
                await client.write_gatt_char(CARACTERISTICA_UUID, dado_para_enviar)
                logger.info("Dado enviado via Bluetooth com sucesso!")
                return True
            else:
                logger.error("Não foi possível estabelecer conexão com o dispositivo BLE.")
                return False

    except Exception as e:
        logger.error(
            f"Erro de conexão/comunicação com a mão robótica via Bluetooth ({DEVICE_ADDRESS}): {e}. "
            "Certifique-se de que o microcontrolador está ligado e com o firmware BLE ativo."
        )
        return False
