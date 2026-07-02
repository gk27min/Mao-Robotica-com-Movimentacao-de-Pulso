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
// IDs devem corresponder ao dicionário GESTOS em backend/brain.py
const int POSICOES_GESTOS[NUM_GESTOS][NUM_SERVOS] = {
  //  Pol   Ind   Med   Ane   Min   Pul
  {    0,    0,    0,    0,    0,   90 },  //  0: Mão fechada / Zero
  {    0,  180,    0,    0,    0,   90 },  //  1: Número Um
  {    0,  180,  180,    0,    0,   90 },  //  2: Número Dois / Paz
  {    0,  180,  180,  180,    0,   90 },  //  3: Número Três
  {    0,  180,  180,  180,  180,   90 },  //  4: Número Quatro
  {  180,  180,  180,  180,  180,   90 },  //  5: Número Cinco / Mão Aberta
  {  180,  180,    0,    0,  180,   90 },  //  6: Eu te amo (LIBRAS)
  {  180,    0,    0,    0,    0,   90 },  //  7: Joia / Positivo / Sim
  {    0,    0,  180,    0,    0,   90 },  //  8: Dedo do meio / Raiva
  {  180,    0,    0,    0,  180,   90 },  //  9: Surfista / Hang Loose
  {    0,  180,    0,    0,  180,   90 },  // 10: Rock / Chifres
  {  180,  180,  180,  180,  180,   45 },  // 11: Aceno / Tchau / Oi
  {    0,    0,    0,    0,  180,   90 },  // 12: Letra I (LIBRAS) — só mindinho
  {  180,  180,    0,    0,    0,   90 },  // 13: Letra L (LIBRAS) — polegar + indicador
  {  180,    0,  180,  180,  180,   90 },  // 14: Sinal de OK (approx: 3 dedos + polegar, indicador fechado)
  {    0,  180,    0,    0,    0,   45 },  // 15: Não / Negativo — indicador + pulso inclinado
  {    0,  180,  180,  180,    0,   90 },  // 16: Água (LIBRAS) — índice + médio + anelar
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
