import asyncio
import logging
import os
from bleak import BleakClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bluetooth_sender")

# Leia o endereço MAC do dispositivo via variável de ambiente ou edite diretamente.
# Linux/Windows: formato "XX:XX:XX:XX:XX:XX"
# macOS: UUID retornado pela varredura BLE
DEVICE_ADDRESS = os.environ.get("BLE_DEVICE_ADDRESS", "XX:XX:XX:XX:XX:XX")

# UUIDs devem ser idênticos ao firmware (configuracoes.h)
SERVICO_UUID        = "19b10000-e8f2-537e-4f6c-d104768a1214"
CARACTERISTICA_UUID = "19b10001-e8f2-537e-4f6c-d104768a1214"

async def enviar_comando_bluetooth(codigo: int) -> bool:
    """
    Conecta ao Arduino via BLE e escreve o byte do gesto na característica.
    Retorna True em caso de sucesso, False em caso de falha.
    """
    if DEVICE_ADDRESS == "XX:XX:XX:XX:XX:XX":
        logger.error(
            "DEVICE_ADDRESS não configurado. "
            "Defina a variável de ambiente BLE_DEVICE_ADDRESS com o MAC do Arduino "
            "antes de iniciar o servidor."
        )
        return False

    logger.info(f"Conectando ao dispositivo BLE: {DEVICE_ADDRESS}")

    try:
        async with BleakClient(DEVICE_ADDRESS, timeout=5.0) as client:
            if not client.is_connected:
                logger.error("Falha na conexão BLE.")
                return False

            dado = bytes([codigo])
            await client.write_gatt_char(CARACTERISTICA_UUID, dado)
            logger.info(f"Byte {codigo} enviado para {CARACTERISTICA_UUID}")
            return True

    except Exception as e:
        logger.error(
            f"Erro BLE ({DEVICE_ADDRESS}): {e}. "
            "Verifique se o Arduino está ligado e com o firmware BLE ativo."
        )
        return False
