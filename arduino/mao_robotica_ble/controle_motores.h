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

// Posições por gesto: { polegar, indicador, médio, anelar, mindinho, pulso }
// 0 = fechado/recolhido, 180 = aberto/estendido
const int POSICOES_GESTOS[NUM_GESTOS][NUM_SERVOS] = {
  //  Pol   Ind   Med   Ane   Min   Pul
  {    0,    0,    0,    0,    0,   90 },  // 0: Descanso (mão fechada)
  {  180,  180,  180,  180,  180,   90 },  // 1: Mão aberta
  {    0,  180,    0,    0,    0,   90 },  // 2: Apontar (só indicador)
  {    0,  180,  180,    0,    0,   90 },  // 3: Paz / Vitória
  {  180,  180,  180,  180,  180,   45 },  // 4: Tchau (mão aberta, pulso inclinado)
  {  180,    0,    0,    0,    0,   90 },  // 5: Joinha (só polegar)
  {  180,  180,    0,    0,  180,   90 },  // 6: Eu te amo (polegar + indicador + mindinho)
};

void inicializarServos() {
  servoPolegar.attach(PINO_POLEGAR);
  servoIndicador.attach(PINO_INDICADOR);
  servoMedio.attach(PINO_MEDIO);
  servoAnelar.attach(PINO_ANELAR);
  servoMindinho.attach(PINO_MINDINHO);
  servoPulso.attach(PINO_PULSO);
}

void executarGesto(int id) {
  if (id < 0 || id >= NUM_GESTOS) return;

  servoPolegar.write(POSICOES_GESTOS[id][0]);
  servoIndicador.write(POSICOES_GESTOS[id][1]);
  servoMedio.write(POSICOES_GESTOS[id][2]);
  servoAnelar.write(POSICOES_GESTOS[id][3]);
  servoMindinho.write(POSICOES_GESTOS[id][4]);
  servoPulso.write(POSICOES_GESTOS[id][5]);
}
