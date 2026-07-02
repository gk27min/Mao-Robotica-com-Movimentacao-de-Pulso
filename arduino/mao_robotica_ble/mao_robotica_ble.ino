#include <ArduinoBLE.h>
#include "configuracoes.h"
#include "controle_motores.h"

BLEService maoService(UUID_SERVICO);
BLECharacteristic comandoCharacteristic(UUID_CARACTERISTICA, BLERead | BLEWrite, 32);

void processarComando(char* cmd) {
  char* inicio = strchr(cmd, '<');
  char* fim    = strchr(cmd, '>');

  if (!inicio || !fim || fim <= inicio) {
    Serial.println("Pacote invalido.");
    return;
  }

  char conteudo[32];
  int len = fim - inicio - 1;
  if (len <= 0 || len >= (int)sizeof(conteudo)) {
    Serial.println("Pacote fora do tamanho esperado.");
    return;
  }
  strncpy(conteudo, inicio + 1, len);
  conteudo[len] = '\0';

  char prefixo = conteudo[0];
  if (conteudo[1] != ':') {
    Serial.println("Formato invalido: esperado 'X:...'");
    return;
  }
  char* valor = conteudo + 2;

  if (prefixo == 'G') {
    int id = atoi(valor);
    Serial.print("Gesto recebido: ");
    Serial.println(id);
    if (id >= 0 && id < NUM_GESTOS) {
      executarGesto(id);
    } else {
      Serial.println("ID fora do intervalo. Ignorado.");
    }

  } else if (prefixo == 'R') {
    // Ordem esperada: mindinho, anelar, meio, indicador, polegar, pulso
    int angulos[NUM_SERVOS];
    int i = 0;
    char* token = strtok(valor, ",");
    while (token != NULL && i < NUM_SERVOS) {
      angulos[i++] = atoi(token);
      token = strtok(NULL, ",");
    }
    if (i == NUM_SERVOS) {
      servoMindinho.write(angulos[0]);
      servoAnelar.write(angulos[1]);
      servoMedio.write(angulos[2]);
      servoIndicador.write(angulos[3]);
      servoPolegar.write(angulos[4]);
      servoPulso.write(angulos[5]);
      Serial.println("Modo Marionete aplicado.");
    } else {
      Serial.print("Marionete: esperava ");
      Serial.print(NUM_SERVOS);
      Serial.print(" valores, recebeu ");
      Serial.println(i);
    }

  } else {
    Serial.print("Prefixo desconhecido: ");
    Serial.println(prefixo);
  }
}

void setup() {
  Serial.begin(9600);
  while (!Serial && millis() < 3000);

  if (!BLE.begin()) {
    Serial.println("Falha ao iniciar o Bluetooth! No UNO R4 WiFi isso geralmente indica que o "
                    "firmware do modulo NORA-W36 e/ou a biblioteca ArduinoBLE estao desatualizados "
                    "(Arduino IDE: Tools > Firmware & Certificates Updater).");
    pinMode(LED_BUILTIN, OUTPUT);
    while (1) {
      digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
      delay(200);
    }
  }

  BLE.setLocalName(NOME_BLE);
  BLE.setAdvertisedService(maoService);
  maoService.addCharacteristic(comandoCharacteristic);
  BLE.addService(maoService);
  BLE.advertise();

  inicializarServos();
  abrirMao();

  Serial.print("BLE ativo. Endereco: ");
  Serial.println(BLE.address());
  Serial.println("Aguardando conexao...");
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Conectado: ");
    Serial.println(central.address());

    while (central.connected()) {
      if (comandoCharacteristic.written()) {
        char buf[33] = {0};
        int len = comandoCharacteristic.valueLength();
        if (len > 32) len = 32;
        memcpy(buf, comandoCharacteristic.value(), len);
        processarComando(buf);
      }
    }

    Serial.print("Desconectado: ");
    Serial.println(central.address());
    executarGesto(0);
  }
}
