#include <ArduinoBLE.h>

// UUIDs configurados no seu backend Python
BLEService botService("19b10000-e8f2-537e-4f6c-d104768a1214");
BLEByteCharacteristic comandoCharacteristic("19b10001-e8f2-537e-4f6c-d104768a1214", BLERead | BLEWrite);

void setup() {
  Serial.begin(9600);
  while (!Serial); // Aguarda você abrir o Serial Monitor

  if (!BLE.begin()) {
    Serial.println("Falha ao iniciar o módulo BLE!");
    while (1);
  }

  BLE.setLocalName("LIBRAS-BOT");
  BLE.setAdvertisedService(botService);
  botService.addCharacteristic(comandoCharacteristic);
  BLE.addService(botService);
  
  comandoCharacteristic.writeValue(0);
  BLE.advertise();

  Serial.println("Bluetooth Ativo! Aguardando conexões...");
  Serial.print("MAC Address da placa: ");
  Serial.println(BLE.address());
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Conectado ao backend! MAC do PC: ");
    Serial.println(central.address());

    while (central.connected()) {
      if (comandoCharacteristic.written()) {
        int comando = comandoCharacteristic.value();
        Serial.print("Comando recebido do Python: ");
        Serial.println(comando);
      }
    }
    Serial.println("Backend desconectado.");
  }
}
