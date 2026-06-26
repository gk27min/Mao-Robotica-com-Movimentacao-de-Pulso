# Mão Robótica com Movimentação de Pulso - LIBRAS-BOT

Projeto desenvolvido para a disciplina de **Projeto Integrado II (PIC2)**, do curso de **Engenharia de Computação** na **Universidade Federal do Espírito Santo (UFES)**[cite: 7, 8, 121].

## 🛠️ Especificações do Protótipo
* **Funcionalidades:** 5 dedos funcionais e sistema de rotação de pulso.
* **Diferencial:** Baixo custo comparado a soluções da indústria e foco em comunicação e acessibilidade.
* **Materiais:** Impressão 3D em PETG, uso de fio de nylon para tração e parafusos.

## 💻 Arquitetura do Sistema

### Software e Integração
* **Mobile (Interface):** Desenvolvido em **Flutter (Dart)** com interface de chatbot multiplataforma em tempo real.
* **Voz (STT):** Captura e transcrição de áudio via pacotes nativos do Flutter (Speech-to-Text).
* **Inteligência Artificial:** Uso de **Ollama (LLM Local)** para orquestração de modelos de linguagem e interpretação de intenções[cite: 109]. Utiliza **Prompt Engineering** para mapear a linguagem natural em comandos técnicos de ângulos e dedos específicos.
* **Backend e Integração:** Servidor intermediário em **Python** para processar a lógica pesada e comunicar com o Arduino via porta serial, utilizando protocolo HTTP/JSON para as requisições.

### Hardware e Controle de Baixo Nível
* **Microcontrolador:** Arduino Uno R4 WIFI.
* **Atuadores:** 6 servomotores MG995 coordenados simultaneamente.
* **Firmware:** Programação em **C++** para gestão da lógica de movimento, temporização e controle PWM para os motores, utilizando a biblioteca `Servo.h`.

---

## ⚙️ Configuração do Ambiente de Desenvolvimento (Linux/Ubuntu)

Este guia consolida todos os passos necessários para configurar o ambiente Flutter e as ferramentas Android.

### 1. Instalação Automática via Terminal
Copie e cole o bloco abaixo no seu terminal para instalar as dependências de sistema e os SDKs iniciais:

```bash
# Atualizar repositórios e instalar ferramentas essenciais
sudo apt update
sudo apt install -y curl git unzip xz-utils zip libglu1-mesa mesa-utils

# Instalar Flutter e Android Studio via Snap
sudo snap install flutter --classic
sudo snap install android-studio --classic
```

### 2. Configuração Manual do Android Studio
Como certas ferramentas dependem de interface gráfica, siga estes passos:
1. Abra o Android Studio rodando `android-studio` no terminal.
2. No assistente inicial, escolha a instalação **Standard**.
3. Na tela de boas-vindas, clique em **More Actions** e selecione **SDK Manager**.
4. Vá na aba **SDK Tools**.
5. Marque a caixa **Android SDK Command-line Tools (latest)**.
6. Clique em **Apply** e aguarde o término da instalação.

### 3. Finalização das Licenças
Após instalar o `cmdline-tools` acima, execute este comando no terminal para aceitar os termos do Google:

```bash
# Pressione 'y' e Enter para todos os contratos que aparecerem
flutter doctor --android-licenses

# Por fim, verifique se todos os itens estão com o check verde
flutter doctor
```
### 4. Executando o Aplicativo no Celular Físico (Flutter)
Como o aplicativo depende de gravação de áudio em tempo real, o uso de emuladores no Linux não é recomendado devido a incompatibilidades de hardware (KVM/Microfone). Utilize um smartphone Android físico.

**No Celular:**
1. Vá em **Configurações > Sobre o telefone > Informações do software**.
2. Toque 7 vezes em **Número de compilação** para ativar o Modo Desenvolvedor.
3. Volte nas Configurações, entre em **Opções do Desenvolvedor** e ative a **Depuração USB**.
4. Conecte o celular ao computador via cabo USB.
5. Mude o modo de conexão no celular de "Apenas carregamento" para **Transferência de Arquivos (MTP)**.
6. Permita a conexão quando o aviso "Permitir depuração USB?" aparecer na tela do celular.

**No Computador:**
1. Navegue até a pasta do aplicativo Flutter no terminal.
2. Atualize o IP do servidor Python dentro do código do Flutter (se necessário).
3. Verifique se o computador reconheceu o seu celular:
   ```bash
   flutter devices
   ```
4. Instale e rode o aplicativo:
   ```bash
   flutter run
   ```
