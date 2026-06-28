import asyncio
<<<<<<< HEAD
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
=======
from bleak import BleakClient

# Endereço MAC exato da sua placa
ARDUINO_MAC_ADDRESS = "b4:3a:45:b4:48:11"

# UUID da Característica de Escrita (igual ao do código C++)
CHARACTERISTIC_UUID = "19b10001-e8f2-537e-4f6c-d104768a1214"

# Como você está com a placa, desligamos a simulação
SIMULAR_HARDWARE = False

async def enviar_comando_bluetooth(codigo: int) -> bool:
    if SIMULAR_HARDWARE:
        print(f"[SIMULAÇÃO] Código {codigo} 'enviado' para o Arduino.")
        await asyncio.sleep(1)
        return True

    print(f"Procurando LIBRAS-BOT no endereço {ARDUINO_MAC_ADDRESS}...")
    try:
        # Aumentei o timeout para 10s para garantir a primeira conexão
        async with BleakClient(ARDUINO_MAC_ADDRESS, timeout=10.0) as client:
            if client.is_connected:
                print("Conectado fisicamente! Transmitindo comando...")
                # O bleak exige que o envio seja em formato de bytes
                await client.write_gatt_char(CHARACTERISTIC_UUID, bytes([codigo]))
                print(f"Comando {codigo} entregue com sucesso!")
                return True
    except Exception as e:
        print(f"Erro na comunicação Bluetooth: {e}")
>>>>>>> b195f6ff25a21d0972ff2c4cbd60c936136ac35f
        return False

# Pequeno bloco para testar o envio isoladamente sem precisar ligar o servidor FastAPI
if __name__ == "__main__":
    # Vamos simular o envio do comando 3 (Sinal de Paz)
    asyncio.run(enviar_comando_bluetooth(3))