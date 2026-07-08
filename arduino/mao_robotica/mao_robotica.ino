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

void executarComando(byte comando) {
  // O comando 120 cabe num 'byte' sem problemas (limite é 255)
  byte base = comando % 100;
  bool oscilar = comando >= 100;

  Serial.print("Executando base: ");
  Serial.print(base);
  Serial.print(" | Oscilar pulso: ");
  Serial.println(oscilar ? "SIM" : "NAO");

  // 1. Resolve a configuração física dos dedos
  if (base <= 17) {
    configurarDedos(base);
    delay(500); // Tempo para os motores estáticos chegarem na posição
  } else if (base == 18) {
    libras_agua();
  } else if (base == 19) {
    aspas();
  }

  delay(1200);      // Aguarda um tempo de leitura confortável

  // 2. Resolve o movimento do pulso
  if (oscilar) {
    oscilarPulso();
  } else {
    pulso.write(140); // Fixa o pulso na posição de descanso
    delay(1500);      // Aguarda um tempo de leitura confortável
  }

  delay(1000);      // Aguarda um tempo de leitura confortável
  // 3. Ao finalizar a ação, volta à posição de descanso
  abrirMao();
}

void configurarDedos(byte base) {
  // ESTADO PADRÃO: MÃO TOTALMENTE FECHADA (Comando 0)
  // ---
  // Lógica Invertida (Hardware):
  // Mindinho, Anelar, Meio -> Fechado = 180 | Aberto = 0
  // Indicador -> Fechado = 0 | Aberto = 180
  // ---
  int min = 180;
  int ane = 180;
  int mei = 180;
  int ind = 0;
  int pol = 0; 

  // Muta os ângulos apenas para os dedos que precisam abrir/dobrar
  switch (base) {
    case 1:  ind = 180; break; // Indicador
    case 2:  ind = 180; mei = 0; break; // Paz
    case 3:  ind = 180; mei = 0; ane = 0; break; // Três
    case 4:  ind = 180; mei = 0; ane = 0; min = 0; break; // Quatro
    case 5:  ind = 180; mei = 0; ane = 0; min = 0; pol = 180; break; // Cinco / Mão Aberta
    case 6:  ind = 180; min = 0; pol = 180; break; // Eu te amo
    case 7:  pol = 180; break; // Joinha
    case 8:  mei = 0; break; // Dedo do meio
    case 9:  min = 0; pol = 180; break; // Shaka
    case 10: ind = 180; min = 0; break; // Rock
    case 11: min = 0; break; // Letra I
    case 12: ind = 180; pol = 180; break; // Letra L
    case 13: mei = 0; ane = 0; min = 0; break; // OK (Pol e Ind fechados, tocando)
    case 14: min = 80; ane = 100; mei = 140; ind = 70; pol = 120; break; // Letra C
    case 15: pol = 80; break; // Letra A (Punho fechado, polegar relaxado na lateral)
    case 16: min = 100; ane = 120; mei = 150; ind = 0; pol = 25; break; // Letra O
    case 17: mei = 0; ind = 180; pol = 80; break; // Base H
  }

  // Envia todos os comandos de uma vez
  mindinho.write(min);
  anelar.write(ane);
  meio.write(mei);
  indicador.write(ind);
  polegar.write(pol);
}
void abrirMao() {
  configurarDedos(5); // CM-005 é a mão espalmada
  pulso.write(140);
}

void moverSuave(Servo &s, int alvo, int passo, int atraso) {
  int atual = s.read();              // ultimo angulo comandado
  // Exibe "Atual: " e depois o valor da variável
  //Serial.print("Atual: ");
  //Serial.println(atual);

// Exibe "Alvo: " e depois o valor da variável
  //Serial.print("Alvo: ");
  //Serial.println(alvo);
  
  if (atual < alvo) {
    for (int a = atual; a <= alvo; a += passo) { s.write(a); delay(atraso); }
  } else {
    for (int a = atual; a >= alvo; a -= passo) { s.write(a); delay(atraso); }
  }
  s.write(alvo);
}

void oscilarPulso() {
  for (int i = 0; i < 2; i++) {
    moverSuave(pulso, 0,  2, 30);   // sobe suave
    moverSuave(pulso, 140, 2, 30);   // desce suave
  }
}

// ==========================================
// MOVIMENTOS COM REPETIÇÃO NOS DEDOS
// ==========================================

void libras_agua() {
  mindinho.write(180); 
  anelar.write(180);
  meio.write(180);
  polegar.write(180);
  pulso.write(140);
  delay(300);
  
  // Indicador batendo repetidas vezes
  for (int i = 0; i < 4; i++) {
    indicador.write(0);
    delay(600);
    indicador.write(180);
    delay(600);
  }
}

void aspas() {
  mindinho.write(180); 
  anelar.write(180);
  polegar.write(0);
  pulso.write(120);

  // Médio e Indicador dobram ao mesmo tempo
  for(int i = 0; i < 2; i++) {
    meio.write(0);       // Aberto
    indicador.write(180); // Aberto
    delay(700);
    meio.write(180);     // Fechado
    indicador.write(0);   // Fechado
    delay(1000);
  }
}