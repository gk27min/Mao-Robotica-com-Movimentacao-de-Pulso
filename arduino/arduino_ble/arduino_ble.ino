#include <ArduinoBLE.h>
#include <Servo.h>

// UUIDs configurados no seu backend Python
BLEService botService("19b10000-e8f2-537e-4f6c-d104768a1214");
BLEByteCharacteristic comandoCharacteristic("19b10001-e8f2-537e-4f6c-d104768a1214", BLERead | BLEWrite);

// Servos
Servo mindinho;
Servo anelar;
Servo meio;
Servo indicador;
Servo polegar;
Servo pulso;

void setup() {
  Serial.begin(9600);
  
  pulso.attach(7);
  mindinho.attach(8);
  anelar.attach(9);
  meio.attach(10);
  indicador.attach(11);
  polegar.attach(12);
  
  if (!BLE.begin()) {
    Serial.println("Falha ao iniciar o módulo BLE!");
    while (1);
  }

  BLE.setLocalName("MAO-BOT");
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
  abrirmao();
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Conectado ao backend! MAC do PC: ");
    Serial.println(central.address());

    // Fica neste loop enquanto o Python mantiver a conexão aberta
    while (central.connected()) {
      if (comandoCharacteristic.written()) {
        int comando = comandoCharacteristic.value();
        Serial.print("Comando recebido do Python: ");
        Serial.println(comando);
        
        // Envia o comando para a função de controle dos motores
        executarMovimento(comando);
      }
    }
    Serial.println("Backend desconectado. Voltando a aguardar conexões...");
  }
}

// Função dedicada para controlar os motores da mão robótica
void executarMovimento(int comando) {
  switch (comando) {
    case 0:
      Serial.println("Ação: Descanso / mão fechada");
      mindinho.write(180);
      anelar.write(180);
      meio.write(180);
      indicador.write(0);
      polegar.write(0);
      break;
      
    case 1:
      Serial.println("Ação: Apontar / indicador");
        mindinho.write(180);
        anelar.write(180);
        meio.write(180);
        indicador.write(180);
        polegar.write(0);   
      break;
      
    case 2:
      Serial.println("Ação: Paz / Vitória");
        mindinho.write(180);
        anelar.write(180);
        meio.write(0);
        indicador.write(180);
        polegar.write(0);
      break;
      
    case 3:
      Serial.println("Ação: Três");
      mindinho.write(180);
      anelar.write(0);
      meio.write(0);
      indicador.write(180);
      polegar.write(0);
      break;
      
    case 4:
      Serial.println("Ação: Quatro");
        mindinho.write(0);
        anelar.write(0);
        meio.write(0);
        indicador.write(180);
        polegar.write(0);
      break;
      
    case 5:
      Serial.println("Ação: Mão aberta");
        mindinho.write(0);
        anelar.write(0);
        meio.write(0);
        indicador.write(180);
        polegar.write(180);
      break;
      
    case 6:
      Serial.println("Ação: Eu te amo (LIBRAS)");
        mindinho.write(0);
        anelar.write(180);
        meio.write(180);
        indicador.write(180);
        polegar.write(180);
      break;
      
    case 7:
      Serial.println("Ação: Joinha");
        mindinho.write(180);
        anelar.write(180);
        meio.write(180);
        indicador.write(0);
        polegar.write(180);
      break;
      
    case 8:
      Serial.println("Ação: Dedo do meio");
        mindinho.write(180);
        anelar.write(180);
        meio.write(0);
        indicador.write(0);
        polegar.write(0);
      break;
      
    case 9:
      Serial.println("Ação: HangLose");
        mindinho.write(0);
        anelar.write(180);
        meio.write(180);
        indicador.write(0);
        polegar.write(180);
        // pulso.write(0);
        // delay(600);
        // pulso.write(180);
        // delay(600);
        // pulso.write(120);

      break;
      
    case 10:
      Serial.println("Ação: Rock");
        mindinho.write(0);
        anelar.write(180);
        meio.write(180);
        indicador.write(180);
        polegar.write(0);
      break;
      
    default:
      Serial.print("Comando não reconhecido: ");
      Serial.println(comando);
      break;
  }
}

void abrirmao() {
  mindinho.write(0);
  anelar.write(0);
  meio.write(0);
  indicador.write(180);
  polegar.write(180);
  pulso.write(100);
}