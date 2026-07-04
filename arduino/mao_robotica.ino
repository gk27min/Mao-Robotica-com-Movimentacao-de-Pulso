#include <ArduinoBLE.h>
#include <Servo.h>

// --- Configuração do Bluetooth (BLE) ---
BLEService maoService("19b10000-e8f2-537e-4f6c-d104768a1214");
BLEByteCharacteristic comandoCharacteristic("19b10001-e8f2-537e-4f6c-d104768a1214", BLERead | BLEWrite);

// --- Configuração dos Servomotores ---
Servo mindinho;
Servo anelar;
Servo meio;
Servo indicador;
Servo polegar;
Servo pulso;

void setup()
{
  Serial.begin(9600);

  // Opcional: Aguarda o monitor serial abrir para debugar
  // while (!Serial);

  // Anexando os servos aos pinos digitais do Arduino
  pulso.attach(7);
  mindinho.attach(8);
  anelar.attach(9);
  meio.attach(10);
  indicador.attach(11);
  polegar.attach(12);

  // Começa com a mão aberta
  abrirMao();

  // --- Inicialização do BLE ---
  if (!BLE.begin())
  {
    Serial.println("Falha ao iniciar o Bluetooth!");
    while (1)
      ;
  }

  BLE.setLocalName("MaoRobotica");
  BLE.setAdvertisedService(maoService);

  maoService.addCharacteristic(comandoCharacteristic);
  BLE.addService(maoService);

  // Valor inicial da característica
  comandoCharacteristic.writeValue(5); // Começa no 5 (Mão aberta)

  BLE.advertise();
  Serial.println("Bluetooth ativo! Aguardando o backend conectar...");
}

void loop()
{
  // Fica escutando se o backend se conectou
  BLEDevice central = BLE.central();

  if (central)
  {
    Serial.print("Backend conectado! Endereço MAC: ");
    Serial.println(central.address());

    // Enquanto o backend estiver conectado
    while (central.connected())
    {

      // Verifica se o backend Python enviou um novo gesto
      if (comandoCharacteristic.written())
      {

        byte comandoRecebido = comandoCharacteristic.value();

        Serial.print("Comando recebido do backend: ");
        Serial.println(comandoRecebido);

        // Repassa o número recebido para a sua função de controle dos servos
        executarComando(comandoRecebido);
      }

      // Pequeno atraso para manter a estabilidade da conexão de rádio BLE
      delay(10);
    }

    Serial.print("Backend desconectado: ");
    Serial.println(central.address());
    Serial.println("Aguardando nova conexão...");
  }
}

// ==========================================
// FUNÇÕES DE CONTROLE DOS MOTORES (LIBRAS)
// ==========================================

void executarComando(int comando)
{
  switch (comando)
  {
  case 0:
    Serial.println("Executando: Mao fechada");
    fecharMao();
    break;
  case 1:
    Serial.println("Executando: Um");
    um();
    break;
  case 2:
    Serial.println("Executando: Dois");
    dois();
    break;
  case 3:
    Serial.println("Executando: Tres");
    tres();
    break;
  case 4:
    Serial.println("Executando: Quatro");
    quatro();
    break;
  case 5:
    Serial.println("Executando: Cinco ou Mao Aberta");
    cinco();
    break;
  case 6:
    Serial.println("Executando: Eu Te Amo");
    eu_te_amo();
    break;
  case 7:
    Serial.println("Executando: Joia");
    joia();
    break;
  case 8:
    Serial.println("Executando: Dedo meio");
    dedo_meio();
    break;
  case 9:
    Serial.println("Executando: Surfista");
    surfista();
    break;
  case 10:
    Serial.println("Executando: Rock");
    rock();
    break;
  case 11:
    Serial.println("Executando: Aceno");
    aceno();
    break;
  case 12:
    Serial.println("Executando: I em Libras");
    libras_I();
    break;
  case 13:
    Serial.println("Executando: L em Libras");
    libras_L();
    break;
  case 14:
    Serial.println("Executando: ok");
    ok();
    break;
  case 15:
    Serial.println("Executando: nao");
    nao();
    break;
  case 16:
    Serial.println("Executando: agua");
    libras_agua();
    break;
  default:
    Serial.println("Comando invalido recebido do backend.");
    break;
  }
}

// --- Funções de Gestos Específicos ---

void abrirMao()
{
  cinco();
}

void fecharMao()
{
  mindinho.write(180);
  anelar.write(180);
  meio.write(180);
  indicador.write(0);
  polegar.write(0);
  // pulso.write(100);

  delay(5000);
  abrirMao();
}

void um()
{
  mindinho.write(180);
  anelar.write(180);
  meio.write(180);
  indicador.write(180);
  polegar.write(0);

  delay(1000);
  abrirMao();
}

void dois()
{
  mindinho.write(180);
  anelar.write(180);
  meio.write(0);
  indicador.write(180);
  polegar.write(0);

  delay(1000);
  abrirMao();
}

void tres()
{
  mindinho.write(180);
  anelar.write(0);
  meio.write(0);
  indicador.write(180);
  polegar.write(0);

  delay(1000);
  abrirMao();
}

void quatro()
{
  mindinho.write(0);
  anelar.write(0);
  meio.write(0);
  indicador.write(180);
  polegar.write(0);

  delay(1000);
  abrirMao();
}

void cinco()
{
  mindinho.write(0);
  anelar.write(0);
  meio.write(0);
  indicador.write(180);
  polegar.write(180);
  pulso.write(140);

  delay(1000);
  // Não chamar abrirMao() aqui para não criar loop infinito (abrirMao chama cinco)
}

void eu_te_amo()
{
  mindinho.write(0);
  anelar.write(180);
  meio.write(180);
  indicador.write(180);
  polegar.write(180);

  delay(1000);
  abrirMao();
}

void joia()
{
  mindinho.write(180);
  anelar.write(180);
  meio.write(180);
  indicador.write(0);
  polegar.write(180);

  delay(1000);
  abrirMao();
}

void dedo_meio()
{
  mindinho.write(180);
  anelar.write(180);
  meio.write(0);
  indicador.write(0);
  polegar.write(0);

  delay(1000);
  abrirMao();
}

void surfista()
{
  mindinho.write(0);
  anelar.write(180);
  meio.write(180);
  indicador.write(0);
  polegar.write(180);
  delay(300);
  for (int i = 0; i < 3; i++)
  {
    pulso.write(30);
    delay(400);
    pulso.write(180);
    delay(400);
  }

  delay(1000);
  abrirMao();
}

void rock()
{
  mindinho.write(0);
  anelar.write(180);
  meio.write(180);
  indicador.write(180);
  polegar.write(0);

  delay(1000);
  abrirMao();
}

void aceno()
{
  abrirMao();
  delay(300);
  for (int i = 0; i < 4; i++)
  {
    pulso.write(30);
    delay(400);
    pulso.write(180);
    delay(400);
  }

  delay(1000);
  abrirMao();
}

void libras_I()
{
  mindinho.write(0);
  anelar.write(180);
  meio.write(180);
  indicador.write(0);
  polegar.write(0);

  delay(1000);
  abrirMao();
}

void libras_L()
{
  mindinho.write(180);
  anelar.write(180);
  meio.write(180);
  indicador.write(180);
  polegar.write(180);

  delay(1000);
  abrirMao();
}

void ok()
{
  mindinho.write(0);
  anelar.write(0);
  meio.write(0);
  indicador.write(0);
  polegar.write(0);

  delay(1000);
  abrirMao();
}

void nao()
{
  mindinho.write(180);
  anelar.write(180);
  meio.write(180);
  indicador.write(180);
  polegar.write(0);
  delay(300);
  for (int i = 0; i < 3; i++)
  {
    pulso.write(30);
    delay(400);
    pulso.write(180);
    delay(400);
  }

  delay(1000);
  abrirMao();
}

void libras_agua()
{
  mindinho.write(180);
  anelar.write(180);
  meio.write(180);
  polegar.write(180);
  delay(300);
  for (int i = 0; i < 4; i++)
  {
    indicador.write(0);
    delay(700);
    indicador.write(180);
    delay(700);
  }

  delay(1000);
  abrirMao();
}