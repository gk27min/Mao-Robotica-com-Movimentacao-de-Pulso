# LIBRAS-BOT — Mão Robótica com IA e Movimentação de Pulso

Projeto de pesquisa desenvolvido para a disciplina de **Projeto Integrado II (PIC2)** do curso de **Engenharia de Computação** na **Universidade Federal do Espírito Santo (UFES)**.

O sistema controla uma mão robótica de 6 graus de liberdade (5 dedos + pulso) por meio de comandos de voz ou texto em linguagem natural, processados por uma IA local (Ollama) que orquestra sequências de gestos físicos via Bluetooth BLE.

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Dependências e Pré-requisitos](#3-dependências-e-pré-requisitos)
4. [Instalação e Execução](#4-instalação-e-execução)
   - [4.1 Backend Python](#41-backend-python)
   - [4.2 Hardware Arduino](#42-hardware-arduino)
   - [4.3 Frontend Flutter](#43-frontend-flutter)
5. [Configuração de Permissões Mobile](#5-configuração-de-permissões-mobile)
6. [Executando o Sistema Completo](#6-executando-o-sistema-completo)
7. [Protocolo de Comunicação BLE](#7-protocolo-de-comunicação-ble)
8. [Estrutura de Pastas](#8-estrutura-de-pastas)

---

## 1. Visão Geral

O **LIBRAS-BOT / FalaComaMão** é uma interface de comunicação assistiva que converte fala ou texto em gestos físicos executados por uma mão robótica impressa em 3D.

O fluxo principal é:

1. O usuário fala ou digita um comando no aplicativo Flutter (ex: *"mostre paz"*, *"quanto é 3 mais 4?"*).
2. O texto é enviado via HTTP para um servidor Python local.
3. Um modelo de linguagem (LLM) rodando localmente via **Ollama** interpreta o comando e planeja uma **sequência de gestos**, que pode combinar gestos pré-cadastrados e movimentos angulares diretos gerados pela IA.
4. O servidor envia cada gesto para a mão robótica via **Bluetooth BLE**, um de cada vez, com intervalo para os servos concluírem o movimento.

**Capacidades do sistema:**
- 17 gestos pré-cadastrados (numerais de 0 a 9, sinais de LIBRAS, expressões universais)
- **Modo Marionete**: a IA pode gerar ângulos arbitrários para cada um dos 6 servos
- Orquestração de sequências (ex: número 49 → gesto "4" → gesto "9")
- Suporte a expressões matemáticas, comandos emocionais e vocabulário de LIBRAS

---

## 2. Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│  SMARTPHONE (Android)                                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  App Flutter (FalaComaMão)                               │  │
│  │  • Captura voz via Speech-to-Text                        │  │
│  │  • Aceita entrada de texto (modo teclado)                │  │
│  │  • Chat UI com histórico de comandos                     │  │
│  └──────────────┬───────────────────────────────────────────┘  │
│                 │  HTTP POST /api/comando                       │
│                 │  {"texto": "..."}                             │
└─────────────────┼───────────────────────────────────────────────┘
                  │ (rede Wi-Fi local)
┌─────────────────▼───────────────────────────────────────────────┐
│  COMPUTADOR / SERVIDOR LOCAL                                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Python Backend (FastAPI — backend/server.py)            │  │
│  │                                                          │  │
│  │  brain.py ──► Ollama (phi3)                              │  │
│  │    • Classifica intenção                                 │  │
│  │    • Retorna sequência de comandos BLE                   │  │
│  │    • JSON: {resposta_texto, sequencia_gestos}            │  │
│  │                                                          │  │
│  │  bluetooth_sender.py                                     │  │
│  │    • Loop sobre sequencia_gestos                         │  │
│  │    • Envia cada comando via Bleak (BLE)                  │  │
│  │    • Aguarda 2s entre comandos                           │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │  BLE GATT Write                       │
│                         │  UUID: 19b10001-e8f2-...             │
└─────────────────────────┼───────────────────────────────────────┘
                          │ (Bluetooth BLE)
┌─────────────────────────▼───────────────────────────────────────┐
│  HARDWARE                                                       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Arduino Nano 33 BLE (mao_robotica_ble.ino)             │  │
│  │  • Recebe string via BLE (até 32 bytes)                  │  │
│  │  • Faz parsing do protocolo <G:ID> ou <R:...>           │  │
│  │  • Aciona 6 servos (dedos + pulso)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

> **Importante:** O Bluetooth BLE é controlado pelo **computador** (via biblioteca Python `bleak`), não pelo smartphone. O app Flutter se comunica apenas via HTTP com o backend Python.

---

## 3. Dependências e Pré-requisitos

Certifique-se de que os seguintes programas estão instalados antes de começar:

| Ferramenta | Versão mínima | Para quê |
|---|---|---|
| **Python** | 3.10+ | Backend, LLM, BLE |
| **Ollama** | Qualquer estável | Servidor LLM local |
| **Flutter SDK** | 3.11+ | App mobile |
| **Android SDK** | API 26+ | Build do app Android |
| **Arduino IDE** | 2.x | Upload do firmware |
| **Bluetooth 4.0+** | — | Interface BLE do computador |

### Verificando as instalações

```bash
python3 --version
ollama --version
flutter --version
```

---

## 4. Instalação e Execução

### 4.1 Backend Python

O backend principal fica em `backend/`. Ele usa **FastAPI** para receber comandos do app e **Bleak** para enviar os gestos via BLE para o Arduino.

#### Passo 1 — Criar e ativar o ambiente virtual

```bash
cd backend/
python3 -m venv .venv
source .venv/bin/activate
```

> No Windows: `.venv\Scripts\activate`

#### Passo 2 — Instalar as dependências

```bash
pip install -r requirements.txt
```

As principais bibliotecas instaladas são:

| Pacote | Função |
|---|---|
| `fastapi` + `uvicorn` | Servidor HTTP assíncrono |
| `ollama` | Cliente para o modelo LLM local |
| `bleak` | Comunicação Bluetooth BLE com o Arduino |
| `pydantic` | Validação dos modelos de dados da API |
| `httpx` | Cliente HTTP assíncrono (dependência interna) |

#### Passo 3 — Instalar e iniciar o Ollama

Instale o Ollama caso ainda não tenha:

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh
```

Inicie o servidor do Ollama e baixe o modelo utilizado pelo projeto:

```bash
# Em um terminal separado (ou em background)
ollama serve

# Em outro terminal, baixe o modelo (necessário apenas uma vez)
ollama pull phi3
```

> O modelo `phi3` é definido em `backend/brain.py` na constante `LLM_MODEL`. Você pode substituí-lo por outro modelo Ollama compatível (ex: `llama3.2`, `mistral`).

#### Passo 4 — Configurar o endereço MAC do Arduino

Abra `backend/bluetooth_sender.py` e atualize a constante com o endereço MAC do seu Arduino:

```python
# backend/bluetooth_sender.py
ARDUINO_MAC_ADDRESS = "b4:3a:45:b4:48:11"  # ← substitua pelo MAC do seu dispositivo
```

Para descobrir o MAC do seu Arduino, use o Monitor Serial do Arduino IDE após o upload do firmware — ele imprime o endereço ao iniciar.

#### Passo 5 — Iniciar o servidor

```bash
# Com o ambiente virtual ativado e dentro da pasta backend/
python server.py
```

O servidor ficará disponível em `http://0.0.0.0:5000`. Você verá no terminal:

```
INFO:     Started server process [...]
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

---

### 4.2 Hardware Arduino

O firmware fica em `arduino/mao_robotica_ble/`.

#### Passo 1 — Instalar as bibliotecas na Arduino IDE

Abra a **Arduino IDE 2.x**, vá em **Tools → Manage Libraries...** e instale:

| Biblioteca | Versão testada |
|---|---|
| `ArduinoBLE` | 1.3.x |
| `Servo` | (incluída no core do Arduino) |

#### Passo 2 — Instalar o core do Arduino Nano 33 BLE

Vá em **Tools → Board → Boards Manager**, pesquise por `Arduino Mbed OS Nano Boards` e instale.

Selecione a placa em **Tools → Board → Arduino Nano 33 BLE**.

#### Passo 3 — Verificar os pinos dos servos

Os pinos estão definidos em `arduino/mao_robotica_ble/configuracoes.h`:

```cpp
#define PINO_POLEGAR     12
#define PINO_INDICADOR   11
#define PINO_MEDIO       10
#define PINO_ANELAR       9
#define PINO_MINDINHO     8
#define PINO_PULSO        7
```

Certifique-se de que os servos físicos estão conectados nesses pinos.

#### Passo 4 — Fazer o upload do firmware

1. Conecte o Arduino via USB.
2. Selecione a porta correta em **Tools → Port**.
3. Abra o arquivo `arduino/mao_robotica_ble/mao_robotica_ble.ino`.
4. Clique em **Upload** (→).
5. Abra o **Monitor Serial** (baud: 9600) e confirme que aparece:

```
BLE ativo. Aguardando conexao...
```

---

### 4.3 Frontend Flutter

O app fica em `app/`.

#### Passo 1 — Instalar o Flutter SDK

Siga o guia oficial para Linux/macOS/Windows: [flutter.dev/docs/get-started/install](https://flutter.dev/docs/get-started/install)

Verifique a instalação:

```bash
flutter doctor
```

Todos os itens relevantes devem estar marcados com `✓`.

#### Passo 2 — Configurar o IP do servidor

**Este passo é obrigatório ao rodar em um dispositivo físico.** O app precisa do IP da máquina onde o backend Python está rodando na rede local.

Descubra o IP do seu computador:

```bash
# Linux/macOS
ip a | grep "inet " | grep -v 127
# ou
hostname -I
```

Abra `app/lib/main.dart` e atualize a constante:

```dart
// app/lib/main.dart — linha ~160
static const String _serverUrl = 'http://SEU_IP_AQUI:5000/api/comando';
// Exemplo: 'http://192.168.1.105:5000/api/comando'
```

> O smartphone e o computador **devem estar na mesma rede Wi-Fi** para que a comunicação funcione.

#### Passo 3 — Instalar as dependências

```bash
cd app/
flutter pub get
```

As principais dependências do `pubspec.yaml` são:

| Pacote | Versão | Função |
|---|---|---|
| `speech_to_text` | ^7.0.0 | Reconhecimento de voz (STT) |
| `http` | ^1.1.0 | Requisições HTTP para o backend |
| `cupertino_icons` | ^1.0.8 | Ícones iOS |

#### Passo 4 — Ativar o modo desenvolvedor no Android e executar

**No celular:**
1. Vá em **Configurações → Sobre o telefone → Informações do software**.
2. Toque **7 vezes** em **Número de compilação** para ativar o Modo Desenvolvedor.
3. Em **Opções do Desenvolvedor**, ative a **Depuração USB**.
4. Conecte o celular ao computador via USB e mude o modo de conexão para **Transferência de Arquivos (MTP)**.
5. Permita a depuração USB quando o aviso aparecer no celular.

**No computador:**

```bash
# Verifique se o dispositivo é reconhecido
flutter devices

# Compile e instale o app no dispositivo
flutter run
```

Para gerar um APK de distribuição:

```bash
flutter build apk --release
# O APK estará em: build/app/outputs/flutter-apk/app-release.apk
```

---

## 5. Configuração de Permissões Mobile

### Android — Permissões necessárias

O arquivo `app/android/app/src/main/AndroidManifest.xml` já contém as permissões necessárias para o funcionamento atual do app:

```xml
<!-- Microfone: obrigatório para o Speech-to-Text funcionar -->
<uses-permission android:name="android.permission.RECORD_AUDIO" />

<!-- Rede: necessário para as requisições HTTP ao backend Python -->
<uses-permission android:name="android.permission.INTERNET" />
```

### Por que não há permissão de Bluetooth no app?

O Bluetooth BLE **não é usado pelo app Flutter**. Essa comunicação é feita exclusivamente pelo **backend Python** (rodando no computador), que usa a biblioteca `bleak` para se conectar ao Arduino. O smartphone se comunica apenas via HTTP com o backend.

Portanto, **não é necessário adicionar permissões de Bluetooth ao AndroidManifest.xml** para a arquitetura atual.

### Permissões concedidas em tempo de execução

Na primeira vez que o usuário tocar no botão de microfone, o Android exibirá um diálogo solicitando permissão de acesso ao microfone. **Essa permissão deve ser concedida** para o Speech-to-Text funcionar.

Se a permissão for negada, o botão de microfone ficará sem resposta. Para reativá-la:
> **Configurações do celular → Apps → FalaComaMão → Permissões → Microfone → Permitir**

### Se a arquitetura mudar para BLE direto no app

Caso no futuro o app Flutter passe a se conectar diretamente ao Arduino (sem passar pelo backend Python), será necessário adicionar ao `AndroidManifest.xml`:

```xml
<!-- Para Android 12+ (API >= 31) -->
<uses-permission android:name="android.permission.BLUETOOTH_SCAN"
    android:usesPermissionFlags="neverForLocation" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />

<!-- Para Android 11 e anteriores (API < 31) -->
<uses-permission android:name="android.permission.BLUETOOTH"
    android:maxSdkVersion="30" />
<uses-permission android:name="android.permission.BLUETOOTH_ADMIN"
    android:maxSdkVersion="30" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
```

---

## 6. Executando o Sistema Completo

Ordem recomendada para iniciar todos os componentes:

```bash
# Terminal 1 — LLM local
ollama serve

# Terminal 2 — Backend Python (com .venv ativado)
cd backend/
source .venv/bin/activate
python server.py

# Arduino — já deve estar ligado e com o firmware carregado
# O LED do Arduino pisca ao aguardar conexão BLE

# Terminal 3 (ou IDE) — App Flutter
cd app/
flutter run
```

**Checklist antes de usar:**

- [ ] Ollama está rodando (`ollama serve`) e o modelo `phi3` está disponível
- [ ] Backend Python está ouvindo na porta 5000
- [ ] Arduino está ligado e o Monitor Serial confirma `BLE ativo`
- [ ] O IP em `main.dart` aponta para o computador correto
- [ ] Celular e computador estão na mesma rede Wi-Fi
- [ ] Permissão de microfone foi concedida no celular

---

## 7. Protocolo de Comunicação BLE

O backend envia strings codificadas em UTF-8 pela característica GATT. O Arduino faz o parsing ao receber o caractere `>`.

### Gesto pré-cadastrado (`<G:ID>`)

Executa um dos 17 gestos da tabela interna do Arduino.

```
<G:3>   → Gesto ID 3 (Número Três)
<G:14>  → Gesto ID 14 (Sinal de OK)
```

### Modo Marionete (`<R:ang1,ang2,ang3,ang4,ang5,ang_pulso>`)

Controle angular direto. Os ângulos são enviados na ordem: **mindinho, anelar, meio, indicador, polegar, pulso**.

```
<R:0,0,180,180,180,90>   → Três dedos centrais abertos, polegar e mindinho fechados
<R:180,0,0,0,180,120>    → Polegar e mindinho abertos (Hang Loose), pulso inclinado
```

**Limites:** ângulos de 0° a 180°. Pulso com posição de repouso em 120°.

### Exemplo de sequência retornada pela LLM

Para o comando *"quanto é 5 mais 2?"*, a IA retorna:

```json
{
  "resposta_texto": "Cinco mais dois é sete. Vou mostrar: cinco, pausa, dois.",
  "sequencia_gestos": ["<G:5>", "<G:0>", "<G:2>"]
}
```

O servidor envia `<G:5>`, aguarda 2 segundos, envia `<G:0>`, aguarda 2 segundos, envia `<G:2>`.

---

## 8. Estrutura de Pastas

```
Mao-Robotica-com-Movimentacao-de-Pulso/
│
├── app/                          # Frontend Flutter
│   ├── lib/
│   │   └── main.dart             # Toda a lógica do app (chat UI, STT, HTTP)
│   ├── android/
│   │   └── app/src/main/
│   │       └── AndroidManifest.xml
│   └── pubspec.yaml
│
├── backend/                      # Backend principal (FastAPI + Ollama + BLE)
│   ├── server.py                 # Servidor FastAPI, rota /api/comando
│   ├── brain.py                  # Mapeador LLM: texto → sequência de gestos
│   ├── bluetooth_sender.py       # Envio BLE via Bleak
│   └── requirements.txt
│
├── server/                       # Backend alternativo (Flask — em desenvolvimento)
│   ├── app.py                    # CRUD de sinais + rota de comando
│   ├── ollama_client.py          # Cliente Ollama para o Flask
│   └── requirements.txt
│
├── arduino/
│   └── mao_robotica_ble/         # Firmware ativo
│       ├── mao_robotica_ble.ino  # Loop principal + parsing do protocolo
│       ├── controle_motores.h    # Tabela de 17 gestos + funções de servo
│       └── configuracoes.h       # Pinos, UUIDs BLE, NUM_GESTOS
│
└── README.md
```

---

## Especificações do Hardware

| Componente | Especificação |
|---|---|
| Microcontrolador | Arduino Nano 33 BLE |
| Atuadores | 6× Servo MG995 |
| Estrutura | Impressão 3D em PETG |
| Transmissão | Fio de nylon (tração dos dedos) |
| BLE Name | `MaoRobotica` |
| BLE Service UUID | `19b10000-e8f2-537e-4f6c-d104768a1214` |
| BLE Characteristic UUID | `19b10001-e8f2-537e-4f6c-d104768a1214` |

---

*Projeto desenvolvido por alunos de Engenharia de Computação — UFES, 2025.*
