#include <ArduinoBLE.h>
#include "configuracoes.h"
#include "controle_motores.h"

BLEService maoService(UUID_SERVICO);
BLEByteCharacteristic comandoCharacteristic(UUID_CARACTERISTICA, BLERead | BLEWrite);

void setup() {
  Serial.begin(9600);

  inicializarServos();
  executarGesto(0); // Posição inicial: descanso

  if (!BLE.begin()) {
    Serial.println("Falha ao iniciar o Bluetooth!");
    while (1);
  }

  BLE.setLocalName(NOME_BLE);
  BLE.setAdvertisedService(maoService);
  maoService.addCharacteristic(comandoCharacteristic);
  BLE.addService(maoService);
  comandoCharacteristic.writeValue(0);
  BLE.advertise();

  Serial.println("BLE ativo. Aguardando conexao...");
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Conectado: ");
    Serial.println(central.address());

    while (central.connected()) {
      if (comandoCharacteristic.written()) {
        byte id = comandoCharacteristic.value();
        Serial.print("Comando recebido: ");
        Serial.println(id);

        if (id < NUM_GESTOS) {
          executarGesto(id);
          Serial.print("Gesto executado: ");
          Serial.println(id);
        } else {
          Serial.println("ID desconhecido. Ignorado.");
        }
      }
    }

    Serial.print("Desconectado: ");
    Serial.println(central.address());
    executarGesto(0); // Volta ao descanso ao desconectar
  }
}
