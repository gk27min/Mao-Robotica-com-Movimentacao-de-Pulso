import asyncio
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
        return False

# Pequeno bloco para testar o envio isoladamente sem precisar ligar o servidor FastAPI
if __name__ == "__main__":
    # Vamos simular o envio do comando 3 (Sinal de Paz)
    asyncio.run(enviar_comando_bluetooth(3))