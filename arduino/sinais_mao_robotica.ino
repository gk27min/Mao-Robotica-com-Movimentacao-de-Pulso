#include <Servo.h>

Servo mindinho;
Servo anelar;
Servo meio;
Servo indicador;
Servo polegar;
Servo pulso;

void setup() {
  Serial.begin(9600);

  mindinho.attach(8);
  anelar.attach(9);
  meio.attach(10);
  indicador.attach(11);
  polegar.attach(12);
  pulso.attach(7);

  // Começa com a mão aberta
  abrirMao();

  Serial.println("Digite um numero de 0 a 10:");
  Serial.println("0 = Mao fechada");
  Serial.println("1 = Um");
  Serial.println("2 = Dois");
  Serial.println("3 = Tres");
  Serial.println("4 = Quatro");
  Serial.println("5 = Cinco / Mao aberta");
  Serial.println("6 = Eu te amo");
  Serial.println("7 = Joia");
  Serial.println("8 = Dedo meio");
  Serial.println("9 = Surfista");
  Serial.println("10 = Rock");
  Serial.println("11 = Aceno");
  Serial.println("12 = I em Libras");
  Serial.println("13 = L em Libras");
  Serial.println("14 = ok");
  Serial.println("15 = nao");
  Serial.println("16 = agua");
  Serial.println("17 = Aspas");
  Serial.println("18 = C em Libras");
  Serial.println("19 = H em Libras");
  Serial.println("20 = A em Libras");
  Serial.println("21 = O em Libras");

}

void loop() {
  if (Serial.available() > 0) {
    int comando = Serial.parseInt();

    // Limpa o restante do buffer do Serial
    while (Serial.available() > 0) {
      Serial.read();
    }

    executarComando(comando);
  }
}

void executarComando(int comando) {
  switch (comando) {
    case 0:
      fecharMao();
      Serial.println("Mao fechada");
      break;

    case 1:
      um();
      Serial.println("Um");
      break;

    case 2:
      dois();
      Serial.println("Dois");
      break;

    case 3:
      tres();
      Serial.println("Tres");
      break;

    case 4:
      quatro();
      Serial.println("Quatro");
      break;

    case 5:
      cinco();
      Serial.println("Cinco ou Mao Aberta");
      break;

    case 6:
      eu_te_amo();
      Serial.println("Eu Te Amo");
      break;

    case 7:
      joia();
      Serial.println("Joia");
      break;

    case 8:
      dedo_meio();
      Serial.println("Xingamento");
      break;

    case 9:
      surfista();
      Serial.println("Surfista");
      break;

    case 10:
      rock();
      Serial.println("Rock");
      break;

    case 11:
      aceno();
      Serial.println("Aceno");
      break;

    case 12:
      libras_I();
      Serial.println("I em Libras");
      break;

    case 13:
      libras_L();
      Serial.println("L em Libras");
      break;

    case 14:
      ok();
      Serial.println("ok");
      break;

    case 15:
      nao();
      Serial.println("nao");
      break;

    case 16:
      libras_agua();
      Serial.println("agua");
      break;
    
    case 17:
      aspas();
      Serial.println("Aspas");
      break;

    case 18:
      libras_C();
      Serial.println("C em Libras");
      break;

    case 19:
      libras_H();
      Serial.println("H em Libras");
      break;

    case 20:
      libras_A();
      Serial.println("A em Libras");
      break;

    case 21:
      libras_O();
      Serial.println("O em Libras");
      break;
    
    default:
      erro();
      Serial.println("Comando invalido. Digite um numero de 0 a 21.");
      break;
  }
}

// Função para abrir a mão
void abrirMao() {
  cinco();
}

// Função para fechar a mão
void fecharMao() {
  mindinho.write(180);
  anelar.write(180);
  meio.write(180);
  indicador.write(0);
  polegar.write(0);
  // pulso.write(100);

  delay(5000);
  abrirMao();
}

void um() {
  mindinho.write(180);
  anelar.write(180);
  meio.write(180);
  indicador.write(180);
  polegar.write(0);
  // pulso.write(100);

  delay(2000);
  abrirMao();
}

void dois() {
  mindinho.write(180);
  anelar.write(180);
  meio.write(0);
  indicador.write(180);
  polegar.write(0);
  // pulso.write(100);

  delay(2000);
  abrirMao();
}

void tres() {
  mindinho.write(180);
  anelar.write(0);
  meio.write(0);
  indicador.write(180);
  polegar.write(0);
  // pulso.write(100);

  delay(2000);
  abrirMao();
}

void quatro() {
  mindinho.write(0);
  anelar.write(0);
  meio.write(0);
  indicador.write(180);
  polegar.write(0);
  // pulso.write(100);

  delay(2000);
  abrirMao();
}

void cinco() {
  mindinho.write(0);
  anelar.write(0);
  meio.write(0);
  indicador.write(180);
  polegar.write(180);
  pulso.write(140);

  delay(2000);
}

void eu_te_amo() {
  mindinho.write(0);
  anelar.write(180);
  meio.write(180);
  indicador.write(180);
  polegar.write(180);
  // pulso.write(100);

  delay(2000);
  abrirMao();
}

void joia() {
  mindinho.write(180);
  anelar.write(180);
  meio.write(180);
  indicador.write(0);
  polegar.write(180);
  // pulso.write(100);

  delay(2000);
  abrirMao();
}

void dedo_meio() {
  mindinho.write(180);
  anelar.write(180);
  meio.write(0);
  indicador.write(0);
  polegar.write(0);
  // pulso.write(100);

  delay(2000);
  abrirMao();
}

void surfista() {
  mindinho.write(0);
  anelar.write(180);
  meio.write(180);
  indicador.write(0);
  polegar.write(180);
  delay(300);
  for (int i = 0; i < 3; i++) {
    pulso.write(30);
    delay(400);
    pulso.write(180);
    delay(400);
  }

  delay(2000);
  abrirMao();
}

void rock() {
  mindinho.write(0);
  anelar.write(180);
  meio.write(180);
  indicador.write(180);
  polegar.write(0);
  // pulso.write(100);

  delay(2000);
  abrirMao();
}

void aceno() {
  // Mão aberta, pulso oscila 4 vezes
  abrirMao();
  delay(300);
  for (int i = 0; i < 4; i++) {
    pulso.write(30);
    delay(400);
    pulso.write(180);
    delay(400);
  }

  delay(2000);
  abrirMao();
}

void libras_I() {
  mindinho.write(0);
  anelar.write(180);
  meio.write(180);
  indicador.write(0);
  polegar.write(0);

  delay(2000);
  abrirMao();
}

void libras_L() {
  mindinho.write(180);
  anelar.write(180);
  meio.write(180);
  indicador.write(180);
  polegar.write(180);

  delay(2000);
  abrirMao();
}

void ok() {
  mindinho.write(0);
  anelar.write(0);
  meio.write(0);
  indicador.write(0);
  polegar.write(0);

  delay(2000);
  abrirMao();
}

void nao() {
  mindinho.write(180);
  anelar.write(180);
  meio.write(180);
  indicador.write(180);
  polegar.write(0);
  delay(300);
  for (int i = 0; i < 3; i++) {
    pulso.write(30);
    delay(400);
    pulso.write(180);
    delay(400);
  }
 
  delay(2000);
  abrirMao();
}

void libras_agua() {
  mindinho.write(180);
  anelar.write(180);
  meio.write(180);
  polegar.write(180);
  delay(300);
  // indicador bate repetidas vezes
  for (int i = 0; i < 4; i++) {
    indicador.write(0);
    delay(700);
    indicador.write(180);
    delay(700);
  }

  delay(2000);
  abrirMao();
}

void aspas() {
  mindinho.write(180);
  anelar.write(180);
  meio.write(0);
  indicador.write(180);
  polegar.write(0);
  pulso.write(120);
  delay(1200);
  meio.write(180);
  indicador.write(0);
  delay(1200);
  meio.write(0);
  indicador.write(180);
  delay(1200);
  meio.write(180);
  indicador.write(0);
  delay(1200);
  meio.write(0);
  indicador.write(180);
  delay(2000);
  abrirMao();
}

void libras_C() {
  mindinho.write(80);
  anelar.write(100);
  meio.write(140);
  indicador.write(70);
  polegar.write(120);
  delay(2000);
  abrirMao();
}

void libras_H() {
  mindinho.write(180);
  anelar.write(180);
  meio.write(0);
  indicador.write(180);
  polegar.write(80);
  delay(1200);
  pulso.write(50);
  delay(1600);
  Serial.println("Chegeui aqui no H");
  pulso.write(180);
  delay(2000);
  Serial.println("Chegeui aqui 2 no H");
  abrirMao();
}

void libras_A() {
  mindinho.write(180);
  anelar.write(180);
  meio.write(0);
  indicador.write(180);
  polegar.write(80);
  delay(2000);
  abrirMao();
}

void libras_O() {
  mindinho.write(100);
  anelar.write(120);
  meio.write(150);
  indicador.write(0);
  polegar.write(25);

  delay(2000);
  abrirMao();
}

void erro(){
    // Tremor da mao
  for (int i = 0; i < 8; i++) {

    pulso.write(80);
    delay(300);

    if(i == 0){
      indicador.write(0);
      delay(100);
    }else if(i == 1){
      indicador.write(180);
      meio.write(180);
      delay(100);
    }else if(i == 2){
      meio.write(0);
      anelar.write(180);
      delay(100);
    }else if(i == 3){
      anelar.write(0);
      mindinho.write(180);
      delay(100);
    }else if(i == 4){
      mindinho.write(0);
      polegar.write(0);
      delay(100);
    }else if(i == 5){
      polegar.write(180);
      delay(100);
    }else if(i == 6){
      polegar.write(50);
      delay(100);
    }else if(i == 7){
      mindinho.write(50);
      delay(100);
    }
    pulso.write(145);
    delay(300);
  }


  delay(2000);
  // Volta ao normal
  abrirMao();
}