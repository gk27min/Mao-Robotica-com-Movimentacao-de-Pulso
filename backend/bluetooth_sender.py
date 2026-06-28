import asyncio
import logging
from bleak import BleakClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bluetooth_sender")

# Endereço MAC exato da sua placa LIBRAS-BOT
ARDUINO_MAC_ADDRESS = "b4:3a:45:b4:48:11"

# UUID da Característica de Escrita (igual ao do código C++)
CHARACTERISTIC_UUID = "19b10001-e8f2-537e-4f6c-d104768a1214"

async def enviar_comando_bluetooth(codigo: int) -> bool:
    logger.info(f"Procurando LIBRAS-BOT no endereço {ARDUINO_MAC_ADDRESS}...")
    try:
        # Timeout de 10s para garantir a primeira conexão física
        async with BleakClient(ARDUINO_MAC_ADDRESS, timeout=10.0) as client:
            if client.is_connected:
                logger.info("Conectado fisicamente! Transmitindo comando...")
                # O bleak exige que o envio seja em formato de bytes
                await client.write_gatt_char(CHARACTERISTIC_UUID, bytes([codigo]))
                logger.info(f"Comando {codigo} entregue com sucesso!")
                return True
    except Exception as e:
        logger.error(f"Erro na comunicação Bluetooth: {e}. Verifique se o Arduino está ligado.")
        
    return False

# Pequeno bloco para testar o envio isoladamente
if __name__ == "__main__":
    # Testando o envio do comando 3 (Sinal de Paz)
    asyncio.run(enviar_comando_bluetooth(3))