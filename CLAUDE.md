# Projeto: Mão Robótica com Movimentação de Pulso

## Arquitetura

- **app/**: Aplicativo desenvolvido em Dart/Flutter.
- **backend/ / server/**: Servidor e API desenvolvidos em Python.
- **arduino/**: Firmware em C++ para controle dos motores/sensores no Arduino.

## Diretrizes de Desenvolvimento

- Sempre verifique o impacto de mudanças no firmware (C++) em relação aos payloads esperados pelo servidor Python e pelo app Dart.
- Mantenha o padrão de comunicação documentado.
