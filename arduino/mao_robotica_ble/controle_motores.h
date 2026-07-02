#pragma once
#include <Servo.h>
#include "configuracoes.h"

// Objetos dos servos (polegar, indicador, médio, anelar, mindinho, pulso)
Servo servoPolegar;
Servo servoIndicador;
Servo servoMedio;
Servo servoAnelar;
Servo servoMindinho;
Servo servoPulso;

void inicializarServos() {
  servoPolegar.attach(PINO_POLEGAR);
  servoIndicador.attach(PINO_INDICADOR);
  servoMedio.attach(PINO_MEDIO);
  servoAnelar.attach(PINO_ANELAR);
  servoMindinho.attach(PINO_MINDINHO);
  servoPulso.attach(PINO_PULSO);
}

// Ângulos calibrados na mão física (mesmos valores validados no sketch de
// teste via Serial). A direção aberto/fechado não é a mesma para todos os
// dedos — depende de como o fio foi montado em cada servo.

void abrirMao() {
  servoMindinho.write(0);
  servoAnelar.write(0);
  servoMedio.write(0);
  servoIndicador.write(180);
  servoPolegar.write(180);
  servoPulso.write(140);
}

void cinco() {
  abrirMao();
}

void fecharMao() {
  servoMindinho.write(180);
  servoAnelar.write(180);
  servoMedio.write(180);
  servoIndicador.write(0);
  servoPolegar.write(0);
  delay(5000);
  abrirMao();
}

void um() {
  servoMindinho.write(180);
  servoAnelar.write(180);
  servoMedio.write(180);
  servoIndicador.write(180);
  servoPolegar.write(0);
  delay(1000);
  abrirMao();
}

void dois() {
  servoMindinho.write(180);
  servoAnelar.write(180);
  servoMedio.write(0);
  servoIndicador.write(180);
  servoPolegar.write(0);
  delay(1000);
  abrirMao();
}

void tres() {
  servoMindinho.write(180);
  servoAnelar.write(0);
  servoMedio.write(0);
  servoIndicador.write(180);
  servoPolegar.write(0);
  delay(1000);
  abrirMao();
}

void quatro() {
  servoMindinho.write(0);
  servoAnelar.write(0);
  servoMedio.write(0);
  servoIndicador.write(180);
  servoPolegar.write(0);
  delay(1000);
  abrirMao();
}

void eu_te_amo() {
  servoMindinho.write(0);
  servoAnelar.write(180);
  servoMedio.write(180);
  servoIndicador.write(180);
  servoPolegar.write(180);
  delay(1000);
  abrirMao();
}

void joia() {
  servoMindinho.write(180);
  servoAnelar.write(180);
  servoMedio.write(180);
  servoIndicador.write(0);
  servoPolegar.write(180);
  delay(1000);
  abrirMao();
}

void dedo_meio() {
  servoMindinho.write(180);
  servoAnelar.write(180);
  servoMedio.write(0);
  servoIndicador.write(0);
  servoPolegar.write(0);
  delay(1000);
  abrirMao();
}

void surfista() {
  servoMindinho.write(0);
  servoAnelar.write(180);
  servoMedio.write(180);
  servoIndicador.write(0);
  servoPolegar.write(180);
  delay(300);
  for (int i = 0; i < 3; i++) {
    servoPulso.write(30);
    delay(400);
    servoPulso.write(180);
    delay(400);
  }
  delay(1000);
  abrirMao();
}

void rock() {
  servoMindinho.write(0);
  servoAnelar.write(180);
  servoMedio.write(180);
  servoIndicador.write(180);
  servoPolegar.write(0);
  delay(1000);
  abrirMao();
}

void aceno() {
  abrirMao();
  delay(300);
  for (int i = 0; i < 4; i++) {
    servoPulso.write(30);
    delay(400);
    servoPulso.write(180);
    delay(400);
  }
  delay(1000);
  abrirMao();
}

void libras_I() {
  servoMindinho.write(0);
  servoAnelar.write(180);
  servoMedio.write(180);
  servoIndicador.write(0);
  servoPolegar.write(0);
  delay(1000);
  abrirMao();
}

void libras_L() {
  servoMindinho.write(180);
  servoAnelar.write(180);
  servoMedio.write(180);
  servoIndicador.write(180);
  servoPolegar.write(180);
  delay(1000);
  abrirMao();
}

void ok() {
  servoMindinho.write(0);
  servoAnelar.write(0);
  servoMedio.write(0);
  servoIndicador.write(0);
  servoPolegar.write(0);
  delay(1000);
  abrirMao();
}

void nao() {
  servoMindinho.write(180);
  servoAnelar.write(180);
  servoMedio.write(180);
  servoIndicador.write(180);
  servoPolegar.write(0);
  delay(300);
  for (int i = 0; i < 3; i++) {
    servoPulso.write(30);
    delay(400);
    servoPulso.write(180);
    delay(400);
  }
  delay(1000);
  abrirMao();
}

void libras_agua() {
  servoMindinho.write(180);
  servoAnelar.write(180);
  servoMedio.write(180);
  servoPolegar.write(180);
  delay(300);
  for (int i = 0; i < 4; i++) {
    servoIndicador.write(0);
    delay(700);
    servoIndicador.write(180);
    delay(700);
  }
  delay(1000);
  abrirMao();
}

void executarGesto(int id) {
  switch (id) {
    case 0:  fecharMao();   break;
    case 1:  um();          break;
    case 2:  dois();        break;
    case 3:  tres();        break;
    case 4:  quatro();      break;
    case 5:  cinco();       break;
    case 6:  eu_te_amo();   break;
    case 7:  joia();        break;
    case 8:  dedo_meio();   break;
    case 9:  surfista();    break;
    case 10: rock();        break;
    case 11: aceno();       break;
    case 12: libras_I();    break;
    case 13: libras_L();    break;
    case 14: ok();          break;
    case 15: nao();         break;
    case 16: libras_agua(); break;
    default: break;
  }
}
