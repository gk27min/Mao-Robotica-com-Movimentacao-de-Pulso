#include <ArduinoBLE.h>

// Criando o Serviço BLE (os UUIDs são identificadores únicos padrão)
BLEService maoService("19b10000-e8f2-537e-4f6c-d104768a1214"); 

// Criando a Característica (onde o celular vai escrever o comando)
// Usamos BLEByteCharacteristic para mandar um número simples (0 a 255)
BLEByteCharacteristic comandoCharacteristic("19b10001-e8f2-537e-4f6c-d104768a1214", BLERead | BLEWrite);

const int ledPin = LED_BUILTIN; // LED embutido no Arduino

void setup() {
  Serial.begin(9600);
  while (!Serial); // Aguarda o monitor serial abrir (opcional)

  pinMode(ledPin, OUTPUT);

  // Inicializa o módulo Bluetooth
  if (!BLE.begin()) {
    Serial.println("Falha ao iniciar o Bluetooth!");
    while (1);
  }

  // Configura o nome que vai aparecer no celular
  BLE.setLocalName("MaoRobotica");
  BLE.setAdvertisedService(maoService);

  // Adiciona a característica ao serviço e o serviço ao BLE
  maoService.addCharacteristic(comandoCharacteristic);
  BLE.addService(maoService);

  // Define um valor inicial para a característica
  comandoCharacteristic.writeValue(0);

  // Começa a transmitir o sinal BLE
  BLE.advertise();
  Serial.println("Bluetooth ativo! Aguardando conexão...");
}

void loop() {
  // Fica escutando se algum celular (Central) se conectou
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print("Conectado ao celular: ");
    Serial.println(central.address());

    // Enquanto o celular estiver conectado
    while (central.connected()) {
      
      // Verifica se o celular escreveu algo novo na característica
      if (comandoCharacteristic.written()) {
        
        // Lê o valor enviado
        byte comandoRecebido = comandoCharacteristic.value();
        
        Serial.print("Comando recebido: ");
        Serial.println(comandoRecebido);

        // Lógica simples: 1 liga o LED, 0 desliga
        if (comandoRecebido == 1) {
          digitalWrite(ledPin, HIGH);
          Serial.println("Ação: Ligando LED (ou movendo motor!)");
        } 
        else if (comandoRecebido == 0) {
          digitalWrite(ledPin, LOW);
          Serial.println("Ação: Desligando LED (ou parando motor!)");
        }
      }
    }
    
    // Quando o celular desconectar
    Serial.print("Desconectado do celular: ");
    Serial.println(central.address());
  }
}
