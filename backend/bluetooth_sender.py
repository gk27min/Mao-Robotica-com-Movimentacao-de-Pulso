from bleak import BleakClient
import asyncio

MAC_ADDRESS = "b4:3a:45:b4:48:11"
UUID_COMANDO = "19b10001-e8f2-537e-4f6c-d104768a1214"
ble_client = None

# Mude para False quando for testar com o Arduino físico!
MOCK_BLE = True

async def conectar_bluetooth():
    """Função chamada quando o servidor liga para abrir a conexão."""
    global ble_client
    
    if MOCK_BLE:
        print("SIMULAÇÃO ATIVA: Fingindo conexão com o Arduino (Mock Mode).")
        return
    
    print(f"Tentando conectar ao MAO-BOT em {MAC_ADDRESS}...")
    ble_client = BleakClient(MAC_ADDRESS)
    try:
        await ble_client.connect()
        if ble_client.is_connected:
            print("Conectado ao MAO-BOT com sucesso! Mantendo conexão ativa.")
    except Exception as e:
        print(f"Aviso: Não foi possível conectar na inicialização. Erro: {e}")

async def desconectar_bluetooth():
    """Função chamada quando o servidor desliga para liberar o rádio do PC."""
    global ble_client
    if MOCK_BLE:
        return
    if ble_client and ble_client.is_connected:
        await ble_client.disconnect()
        print("Desconectado do MAO-BOT.")

async def enviar_comando_bluetooth(comando: int):
    """Função que o server.py chama para enviar o número do gesto."""
    global ble_client
    
    if MOCK_BLE:
        print(f"SIMULAÇÃO: Comando {comando} transmitido para a mão!")
        return True
    
    # Sistema de Autocura (Auto-reconnect)
    if not ble_client or not ble_client.is_connected:
        print("Bluetooth offline. Tentando reconectar agora...")
        try:
            if not ble_client:
                ble_client = BleakClient(MAC_ADDRESS)
            await ble_client.connect()
            print("Reconexão bem-sucedida!")
        except Exception as e:
            print(f"Falha na reconexão: {e}")
            return False # Retorna falso para o server.py saber que falhou
            
    # Transmissão do Comando
    try:
        await ble_client.write_gatt_char(UUID_COMANDO, bytearray([comando]))
        print(f"Comando {comando} transmitido!")
        return True
    except Exception as e:
        print(f"Falha na transmissão: {e}")
        return False