import asyncio
import logging
from bleak import BleakClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bluetooth_sender")

# Endereço MAC exato da sua placa LIBRAS-BOT
ARDUINO_MAC_ADDRESS = "b4:3a:45:b4:48:11"

# UUID da Característica de Escrita (igual ao do código C++)
CHARACTERISTIC_UUID = "19b10001-e8f2-537e-4f6c-d104768a1214"

async def enviar_comando_bluetooth(comando: str) -> bool:
    """
    Envia um comando formatado para o Arduino via BLE.
    Formatos aceitos:
      <G:ID>               — executa gesto pré-cadastrado (ex: "<G:3>")
      <R:m,a,me,i,p,pul>  — modo marionete com ângulos diretos (ex: "<R:180,0,180,180,180,120>")
    """
    logger.info(f"Conectando em {ARDUINO_MAC_ADDRESS} para enviar: {comando!r}")
    try:
        async with BleakClient(ARDUINO_MAC_ADDRESS, timeout=10.0) as client:
            if client.is_connected:
                await client.write_gatt_char(CHARACTERISTIC_UUID, comando.encode('utf-8'))
                logger.info(f"Comando entregue: {comando!r}")
                return True
    except Exception as e:
        logger.error(f"Erro Bluetooth: {e}. Verifique se o Arduino está ligado.")

    return False

# Bloco para testar o envio isoladamente
if __name__ == "__main__":
    asyncio.run(enviar_comando_bluetooth("<G:3>"))   # Gesto de Paz
    # asyncio.run(enviar_comando_bluetooth("<R:180,0,180,180,180,120>"))  # Marionete