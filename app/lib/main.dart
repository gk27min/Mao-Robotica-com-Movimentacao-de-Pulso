import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:http/http.dart' as http;

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  runApp(const FalaComaMaoApp());
}

Future<bool> enviarGestoDiretoParaServidor(int comando) async {
  const String serverUrl = 'http://192.168.1.4:5000/api/gesto'; // <-- /api/gesto
  final url = Uri.parse(serverUrl);

  try {
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'comando': comando}),
    ).timeout(const Duration(seconds: 15));

    if (response.statusCode == 200) {
      print("Gesto $comando enviado com sucesso!");
      return true;
    } else {
      print("Erro no servidor (${response.statusCode}): ${response.body}");
      return false;
    }
  } catch (e) {
    print("Erro ao enviar gesto: $e");
    return false;
  }
}

class FalaComaMaoApp extends StatelessWidget {
  const FalaComaMaoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FalaComaMão',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6200EA), // Cor vibrante
          brightness: Brightness.light,
        ),
        useMaterial3: true,
      ),
      home: const MainNavigationScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

// =====================================================================
// NAVEGAÇÃO PRINCIPAL (Conversa / Biblioteca)
// =====================================================================
class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _selectedIndex = 0;

  static const List<Widget> _screens = [
    ChatScreen(),
    SignsLibraryScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _selectedIndex, children: _screens),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) => setState(() => _selectedIndex = index),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.chat_bubble_outline_rounded),
            selectedIcon: Icon(Icons.chat_bubble_rounded),
            label: 'Conversa',
          ),
          NavigationDestination(
            icon: Icon(Icons.menu_book_outlined),
            selectedIcon: Icon(Icons.menu_book_rounded),
            label: 'Biblioteca',
          ),
        ],
      ),
    );
  }
}

// Classe estrutural para as mensagens
class ChatMessage {
  String text;
  final bool isUser;
  String status; // 'none', 'analyzing', 'done', 'error'

  ChatMessage({
    required this.text,
    required this.isUser,
    this.status = 'none',
  });
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  late stt.SpeechToText _speech;
  bool _isListening = false;
  bool _isProcessing = false;
  String _recognizedText = '';

  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  final List<ChatMessage> _messages = [
    ChatMessage(text: 'Oi, Tudo Bem', isUser: false),
  ];

  @override
  void initState() {
    super.initState();
    _speech = stt.SpeechToText();
    _textController.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  

  void _processFinalText(String text) {
    if (text.isEmpty) return;

    // 1. Adiciona a mensagem do usuário e a resposta provisória do robô
    setState(() {
      _messages.add(ChatMessage(text: text, isUser: true));
      _messages.add(ChatMessage(
        text: 'Analisando...',
        isUser: false,
        status: 'analyzing',
      ));
      _recognizedText = ''; // Limpa o buffer de reconhecimento
    });
    _scrollToBottom();

    // 2. Chama a API passando o índice exato da mensagem do robô que deve ser atualizada
    final robotMessageIndex = _messages.length - 1;
    enviarComandoParaServidor(text, robotMessageIndex);
  }

  void _sendTextMessage() {
    if (_isProcessing) return;
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    _textController.clear();
    _isProcessing = true;
    _processFinalText(text);
  }

  void _cancelListening() {
    HapticFeedback.lightImpact();
    _speech.cancel();
    setState(() {
      _isListening = false;
      _recognizedText = '';
    });
  }

  void _listen() async {
    // Bloqueia interações se já estiver processando
    if (_isProcessing) return;

    if (!_isListening) {
      bool available = await _speech.initialize(
        onStatus: (val) {
          if (val == 'done' || val == 'notListening') {
            setState(() => _isListening = false);
            // Removido disparo manual. A responsabilidade agora é apenas do finalResult.
          }
        },
        onError: (val) {
          print('onError: $val');
          setState(() => _isListening = false);
        },
      );

      if (available) {
        HapticFeedback.lightImpact();
        setState(() {
          _isListening = true;
          _recognizedText = '';
        });
        _speech.listen(
          onResult: (val) {
            setState(() {
              _recognizedText = val.recognizedWords;
            });
            // Trava de segurança: somente dispara se for finalResult E não estiver processando
            if (val.finalResult && !_isProcessing) {
              setState(() => _isListening = false);
              _isProcessing = true; // Trava o envio duplo
              _processFinalText(val.recognizedWords);
            }
          },
        );
      }
    } else {
      HapticFeedback.mediumImpact();
      setState(() => _isListening = false);
      _speech.stop();
      // Removido disparo manual. A responsabilidade agora é apenas do finalResult.
    }
  }

  // Endereço IP do servidor Python na rede local.
  static const String _serverUrl = 'http://192.168.1.4:5000/api/comando';

  Future<void> enviarComandoParaServidor(String texto, int messageIndex) async {
    final url = Uri.parse(_serverUrl);

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'texto': texto}),
      ).timeout(const Duration(seconds: 60));

      if (!mounted) return;

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final sucesso = data['sucesso'] as bool;
        final detalhes = data['detalhes'] as String;
        final gestureName = data['comando_detectado'] as String?;

        setState(() {
          _isProcessing = false;
          if (sucesso && gestureName != null) {
            // Mostra primeiro que a mão está atuando; o texto final substitui em seguida.
            _messages[messageIndex].text = 'Mão executando o gesto: ${gestureName.toUpperCase()}...';
            _messages[messageIndex].status = 'acting';
          } else {
            _messages[messageIndex].text = sucesso ? detalhes : 'Não reconheci. $detalhes';
            _messages[messageIndex].status = sucesso ? 'done' : 'error';
          }
        });
        _scrollToBottom();

        if (sucesso && gestureName != null) {
          _finishHandActing(messageIndex, detalhes);
        } else if (!sucesso) {
          HapticFeedback.vibrate();
        }
      } else {
        setState(() {
          _messages[messageIndex].text = 'Erro no servidor (${response.statusCode}).';
          _messages[messageIndex].status = 'error';
          _isProcessing = false;
        });
        HapticFeedback.vibrate();
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _messages[messageIndex].text = 'Servidor inacessível. Verifique a conexão.';
        _messages[messageIndex].status = 'error';
        _isProcessing = false;
      });
      HapticFeedback.vibrate();
    }
  }

  void _finishHandActing(int messageIndex, String detalhes) {
    HapticFeedback.mediumImpact();
    // O servidor confirma apenas o envio do comando via Bluetooth, não o término do
    // movimento físico — sem telemetria do Arduino, a duração aqui é uma estimativa de UX.
    Future.delayed(const Duration(seconds: 3), () {
      if (!mounted) return;
      if (_messages[messageIndex].status != 'acting') return;
      setState(() {
        _messages[messageIndex].text = detalhes;
        _messages[messageIndex].status = 'done';
      });
      _scrollToBottom();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FB),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        surfaceTintColor: Colors.transparent,
        shadowColor: Colors.black12,
        title: Row(
          children: [
            const CircleAvatar(
              backgroundImage: AssetImage('assets/icon.jpg'),
              backgroundColor: Colors.transparent,
            ),
            const SizedBox(width: 12),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'FalaComaMão',
                  style: TextStyle(
                    color: Colors.black87,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Online',
                  style: TextStyle(
                    color: Colors.green,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ],
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1.0),
          child: Container(
            color: Colors.grey[200],
            height: 1.0,
          ),
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length + ((_isListening || _recognizedText.isNotEmpty) ? 1 : 0),
              itemBuilder: (context, index) {
                // Mensagens renderizadas do histórico
                if (index < _messages.length) {
                  final msg = _messages[index];
                  return ChatBubble(
                    message: msg.text,
                    isMe: msg.isUser,
                    status: msg.status,
                  );
                } else {
                  // A última bolha é flutuante (tempo real) para o que o usuário está falando
                  if (_isListening && _recognizedText.isEmpty) {
                    return const ChatBubble(
                      child: TypingIndicator(),
                      isMe: true,
                    );
                  } else {
                    return ChatBubble(
                      message: _recognizedText,
                      isMe: true,
                    );
                  }
                }
              },
            ),
          ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 4, 12, 12),
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 200),
                child: _isListening ? _buildRecordingBar() : _buildComposerBar(),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildComposerBar() {
    final hasText = _textController.text.trim().isNotEmpty;
    return Row(
      key: const ValueKey('composer'),
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Expanded(
          child: Container(
            constraints: const BoxConstraints(minHeight: 48, maxHeight: 120),
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(28),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: TextField(
              controller: _textController,
              minLines: 1,
              maxLines: 4,
              enabled: !_isProcessing,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                hintText: 'Digite uma mensagem',
                border: InputBorder.none,
                isCollapsed: true,
              ),
              onSubmitted: (_) => _sendTextMessage(),
            ),
          ),
        ),
        const SizedBox(width: 8),
        GestureDetector(
          onTap: _isProcessing ? null : (hasText ? _sendTextMessage : _listen),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                colors: _isProcessing
                    ? [Colors.grey.shade400, Colors.grey.shade500]
                    : [Theme.of(context).colorScheme.primary, const Color(0xFF8E24AA)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              boxShadow: [
                BoxShadow(
                  color: Theme.of(context).colorScheme.primary.withOpacity(0.35),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Icon(
              hasText ? Icons.send_rounded : Icons.mic_rounded,
              color: Colors.white,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildRecordingBar() {
    return Container(
      key: const ValueKey('recording'),
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(28),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.delete_outline_rounded, color: Colors.black45),
            onPressed: _cancelListening,
            tooltip: 'Cancelar',
          ),
          Expanded(
            child: _recognizedText.isEmpty
                ? const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 8),
                    child: WaveformIndicator(),
                  )
                : Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    child: Text(
                      _recognizedText,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(color: Colors.black87),
                    ),
                  ),
          ),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 4),
            child: Text('Ouvindo...', style: TextStyle(color: Colors.black45, fontSize: 12)),
          ),
          GestureDetector(
            onTap: _listen,
            child: Container(
              width: 44,
              height: 44,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(colors: [Colors.redAccent, Colors.deepOrange]),
              ),
              child: const Icon(Icons.stop_rounded, color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }
}

class ChatBubble extends StatelessWidget {
  final String? message;
  final Widget? child;
  final bool isMe;
  final String status;

  const ChatBubble({
    super.key,
    this.message,
    this.child,
    required this.isMe,
    this.status = 'none',
  });

  @override
  Widget build(BuildContext context) {
    final textStyle = TextStyle(
      color: isMe ? Colors.white : Colors.black87,
      fontSize: 15,
      height: 1.3,
    );

    // Constrói o conteúdo do balão com base no status da resposta do robô
    Widget content;
    if (child != null) {
      content = child!;
    } else {
      if (status == 'analyzing') {
        content = Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: Color(0xFF8E24AA), // Cor vibrante igual ao tema principal
              ),
            ),
            const SizedBox(width: 12),
            Flexible(child: Text(message ?? '', style: textStyle)),
          ],
        );
      } else if (status == 'acting') {
        content = Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.back_hand, size: 18, color: Color(0xFF8E24AA)),
            const SizedBox(width: 10),
            Flexible(child: Text(message ?? '', style: textStyle)),
          ],
        );
      } else if (status == 'done') {
        content = Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Flexible(child: Text(message ?? '', style: textStyle)),
            const SizedBox(width: 6),
            const Icon(Icons.check_circle_rounded, size: 16, color: Colors.green),
          ],
        );
      } else if (status == 'error') {
        content = Row(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Icon(Icons.error_outline_rounded, size: 18, color: Colors.redAccent),
            const SizedBox(width: 8),
            Flexible(child: Text(message ?? '', style: textStyle)),
          ],
        );
      } else {
        content = Text(message ?? '', style: textStyle);
      }
    }

    return Align(
      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
          minHeight: 48,
        ),
        decoration: BoxDecoration(
          gradient: isMe
              ? LinearGradient(
                  colors: [
                    Theme.of(context).colorScheme.primary,
                    const Color(0xFF8E24AA),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                )
              : null,
          color: isMe ? null : (status == 'error' ? const Color(0xFFFFF3F3) : Colors.white),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(24),
            topRight: const Radius.circular(24),
            bottomLeft: Radius.circular(isMe ? 24 : 4),
            bottomRight: Radius.circular(isMe ? 4 : 24),
          ),
          border: status == 'error' ? Border.all(color: Colors.redAccent.withOpacity(0.3)) : null,
          boxShadow: [
            BoxShadow(
              color: isMe
                  ? Theme.of(context).colorScheme.primary.withOpacity(0.2)
                  : Colors.black.withOpacity(0.05),
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: content,
      ),
    );
  }
}

class TypingIndicator extends StatefulWidget {
  const TypingIndicator({super.key});

  @override
  State<TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<TypingIndicator> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(3, (index) {
          return AnimatedBuilder(
            animation: _controller,
            builder: (context, child) {
              final delay = index * 0.2;
              var val = (_controller.value - delay) % 1.0;
              if (val < 0) val += 1.0;

              final offset = (val < 0.5)
                  ? Curves.easeInOut.transform(val * 2)
                  : Curves.easeInOut.transform((1 - val) * 2);

              return Transform.translate(
                offset: Offset(0, -6 * offset),
                child: child,
              );
            },
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 3),
              width: 8,
              height: 8,
              decoration: const BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
              ),
            ),
          );
        }),
      ),
    );
  }
}

// Indicador de forma de onda animado, usado na barra de gravação de áudio.
class WaveformIndicator extends StatefulWidget {
  const WaveformIndicator({super.key});

  @override
  State<WaveformIndicator> createState() => _WaveformIndicatorState();
}

class _WaveformIndicatorState extends State<WaveformIndicator> with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 24,
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: List.generate(5, (i) {
          return AnimatedBuilder(
            animation: _controller,
            builder: (context, child) {
              final t = (_controller.value + i * 0.18) % 1.0;
              final height = 6 + 14 * (0.5 + 0.5 * math.sin(t * 2 * math.pi));
              return Container(
                margin: const EdgeInsets.symmetric(horizontal: 2),
                width: 4,
                height: height,
                decoration: BoxDecoration(
                  color: const Color(0xFF8E24AA),
                  borderRadius: BorderRadius.circular(2),
                ),
              );
            },
          );
        }),
      ),
    );
  }
}

class SignsLibraryScreen extends StatelessWidget {
  const SignsLibraryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    // Lista 100% atualizada e espelhada com o backend e o Arduino (0 a 19 e 100 a 119)
    final List<Map<String, dynamic>> configuracoesMao = [
      // --- BLOCO 1: ESTÁTICOS (Pulso Fixo) ---
      {'comando': 0, 'titulo': 'CM - 000', 'descricao': 'Mão totalmente fechada'},
      {'comando': 1, 'titulo': 'CM - 001', 'descricao': 'Dedo indicador'},
      {'comando': 2, 'titulo': 'CM - 002', 'descricao': 'Indicador e médio'},
      {'comando': 3, 'titulo': 'CM - 003', 'descricao': 'Indicador, médio e anelar'},
      {'comando': 4, 'titulo': 'CM - 004', 'descricao': 'Indicador a mindinho'},
      {'comando': 5, 'titulo': 'CM - 005', 'descricao': 'Todos os dedos'},
      {'comando': 6, 'titulo': 'CM - 006', 'descricao': 'Polegar, indicador e mindinho'},
      {'comando': 7, 'titulo': 'CM - 007', 'descricao': 'Polegar'},
      {'comando': 8, 'titulo': 'CM - 008', 'descricao': 'Dedo médio'},
      {'comando': 9, 'titulo': 'CM - 009', 'descricao': 'Polegar e mindinho'},
      {'comando': 10, 'titulo': 'CM - 010', 'descricao': 'Indicador e mindinho'},
      {'comando': 11, 'titulo': 'CM - 011', 'descricao': 'Mindinho'},
      {'comando': 12, 'titulo': 'CM - 012', 'descricao': 'Polegar e indicador'},
      {'comando': 13, 'titulo': 'CM - 013', 'descricao': 'Médio, anelar e mindinho'},
      {'comando': 14, 'titulo': 'CM - 014', 'descricao': 'Letra C (Dedos curvados)'},
      {'comando': 15, 'titulo': 'CM - 015', 'descricao': 'Letra A (Polegar lateral)'},
      {'comando': 16, 'titulo': 'CM - 016', 'descricao': 'Letra O (Círculo)'},
      {'comando': 17, 'titulo': 'CM - 017', 'descricao': 'Base para Letra H'},
      
      // --- BLOCO 1.1: ESTÁTICOS COM MOVIMENTO DE DEDO ---
      {'comando': 18, 'titulo': 'CM - 018', 'descricao': 'Sinal de Água (Indicador batendo)'},
      {'comando': 19, 'titulo': 'CM - 019', 'descricao': 'Sinal de Aspas (Indicador e médio dobrando)'},

      // --- BLOCO 2: DINÂMICOS (Com oscilação do pulso) ---
      {'comando': 100, 'titulo': 'CM - 100', 'descricao': 'Mão fechada'},
      {'comando': 101, 'titulo': 'CM - 101', 'descricao': 'Indicador (Não)'},
      {'comando': 102, 'titulo': 'CM - 102', 'descricao': 'Indicador e médio'},
      {'comando': 103, 'titulo': 'CM - 103', 'descricao': 'Três dedos'},
      {'comando': 104, 'titulo': 'CM - 104', 'descricao': 'Quatro dedos'},
      {'comando': 105, 'titulo': 'CM - 105', 'descricao': 'Mão aberta (Aceno)'},
      {'comando': 106, 'titulo': 'CM - 106', 'descricao': 'Te amo balançando'},
      {'comando': 107, 'titulo': 'CM - 107', 'descricao': 'Polegar'},
      {'comando': 108, 'titulo': 'CM - 108', 'descricao': 'Dedo médio'},
      {'comando': 109, 'titulo': 'CM - 109', 'descricao': 'Shaka balançando'},
      {'comando': 110, 'titulo': 'CM - 110', 'descricao': 'Rock balançando'},
      {'comando': 111, 'titulo': 'CM - 111', 'descricao': 'Mindinho'},
      {'comando': 112, 'titulo': 'CM - 112', 'descricao': 'Polegar e indicador'},
      {'comando': 113, 'titulo': 'CM - 113', 'descricao': 'Médio, anelar, mindinho balançando'},
      {'comando': 114, 'titulo': 'CM - 114', 'descricao': 'Letra C balançando'},
      {'comando': 115, 'titulo': 'CM - 115', 'descricao': 'Letra A balançando'},
      {'comando': 116, 'titulo': 'CM - 116', 'descricao': 'Letra O balançando'},
      {'comando': 117, 'titulo': 'CM - 117', 'descricao': 'Letra H (Base com rotação)'},
      {'comando': 118, 'titulo': 'CM - 118', 'descricao': 'Sinal de Água do pulso'},
      {'comando': 119, 'titulo': 'CM - 119', 'descricao': 'Sinal de Aspas do pulso'},
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Biblioteca de Gestos'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Colors.white,
      ),
      body: GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
          maxCrossAxisExtent: 200,    
          crossAxisSpacing: 16,
          mainAxisSpacing: 16,
          childAspectRatio: 0.85, 
        ),
        itemCount: configuracoesMao.length,
        itemBuilder: (context, index) {
          final cm = configuracoesMao[index];
          
          return InkWell(
            onTap: () async {
              final messenger = ScaffoldMessenger.of(context); // captura antes do await
              final titulo = cm['titulo'] as String;

              messenger.showSnackBar(
                SnackBar(content: Text('Enviando $titulo...')),
              );

              final ok = await enviarGestoDiretoParaServidor(cm['comando'] as int);

              messenger.hideCurrentSnackBar();
              messenger.showSnackBar(
                SnackBar(
                  content: Text(ok ? '$titulo enviado!' : 'Falha ao enviar $titulo'),
                  backgroundColor: ok ? Colors.green : Colors.red,
                ),
              );
            },
            child: Card(
              elevation: 2, 
              color: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: BorderSide(color: Colors.grey.shade200, width: 1), 
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    HandGestureIcon(
                      gestureLevel: cm['comando'] as int, 
                      size: 80,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      cm['titulo'] as String,
                      style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      cm['descricao'] as String,
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.grey.shade600, fontSize: 11),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class RegisterSignScreen extends StatelessWidget {
  const RegisterSignScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Cadastrar Sinal'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Colors.white,
      ),
      body: const Center(
        child: Text('Formulário de cadastro', style: TextStyle(fontSize: 18)),
      ),
    );
  }
}

// Transformado em StatefulWidget para suportar o Loop de animação dos dedos
class HandGestureIcon extends StatefulWidget {
  final int gestureLevel;
  final double size;

  const HandGestureIcon({
    super.key,
    required this.gestureLevel,
    this.size = 100.0,
  });

  @override
  State<HandGestureIcon> createState() => _HandGestureIconState();
}

class _HandGestureIconState extends State<HandGestureIcon> with SingleTickerProviderStateMixin {
  late AnimationController _fingerController;

  @override
  void initState() {
    super.initState();
    // Controlador de animação que vai e volta (looping infinito)
    _fingerController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _fingerController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final activeColor = Theme.of(context).colorScheme.primary;
    final inactiveColor = Colors.grey.shade300; 

    final int baseGesture = widget.gestureLevel % 100;
    final bool hasWristMovement = widget.gestureLevel >= 100;

    // Estados dos dedos: 0 = Fechado, 1 = Aberto, 2 = Curvado (metade), 3 = Batendo (loop)
    int ind = 0, mei = 0, ane = 0, min = 0, pol = 0;

    switch (baseGesture) {
      case 1:  ind = 1; break;
      case 2:  ind = 1; mei = 1; break;
      case 3:  ind = 1; mei = 1; ane = 1; break;
      case 4:  ind = 1; mei = 1; ane = 1; min = 1; break;
      case 5:  ind = 1; mei = 1; ane = 1; min = 1; pol = 1; break;
      case 6:  ind = 1; min = 1; pol = 1; break;
      case 7:  pol = 1; break;
      case 8:  mei = 1; break;
      case 9:  min = 1; pol = 1; break;
      case 10: ind = 1; min = 1; break;
      case 11: min = 1; break;
      case 12: ind = 1; pol = 1; break;
      case 13: mei = 1; ane = 1; min = 1; break;
      case 14: ind = 2; mei = 2; ane = 2; min = 2; pol = 2; break; // Letra C (Curvados)
      case 15: pol = 2; break; // Letra A (Apenas polegar lateral relaxado)
      case 16: ind = 0; mei = 2; ane = 2; min = 2; pol = 2; break; // Letra O (Círculo)
      case 17: ind = 1; pol = 2; break; // Base H (Indicador aberto, polegar metade)
      case 18: ind = 3; break; // Água (Indicador batendo repetidamente)
      case 19: ind = 3; mei = 3; break; // Aspas (Indicador e médio batendo)
    }

    final fw = widget.size * 0.13; 
    final palmWidth = widget.size * 0.55;
    final palmHeight = widget.size * 0.50;

    return SizedBox(
      width: widget.size,
      height: widget.size,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          // Polegar
          Positioned(
            bottom: widget.size * 0.18,
            right: widget.size * 0.15, 
            child: Transform.rotate(
              angle: 0.78, 
              alignment: Alignment.bottomLeft,
              child: _buildRoboticFinger(pol, activeColor, inactiveColor, fw, widget.size * 0.35),
            ),
          ),

          // Chassi da Mão
          Positioned(
            bottom: widget.size * 0.05,
            left: widget.size * 0.20,
            child: Container(
              width: palmWidth,
              height: palmHeight,
              decoration: BoxDecoration(
                color: activeColor,
                borderRadius: BorderRadius.circular(widget.size * 0.1),
              ),
            ),
          ),

          // Os 4 dedos superiores
          Positioned(
            bottom: widget.size * 0.52, 
            left: widget.size * 0.20,
            child: SizedBox(
              width: palmWidth,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  _buildRoboticFinger(min, activeColor, inactiveColor, fw, widget.size * 0.40),
                  _buildRoboticFinger(ane, activeColor, inactiveColor, fw, widget.size * 0.45),
                  _buildRoboticFinger(mei, activeColor, inactiveColor, fw, widget.size * 0.50),
                  _buildRoboticFinger(ind, activeColor, inactiveColor, fw, widget.size * 0.40),
                ],
              ),
            ),
          ),

          // Indicador de Movimento do Pulso
          if (hasWristMovement)
            Positioned(
              top: -widget.size * 0.15,
              right: -widget.size * 0.15,
              child: Icon(
                Icons.autorenew_rounded, 
                color: activeColor, 
                size: widget.size * 0.30,
              ),
            ),
        ],
      ),
    );
  }

  // O desenho de cada dedo agora reage aos 4 estados
  Widget _buildRoboticFinger(int state, Color activeColor, Color inactiveColor, double width, double maxHeight) {
    return AnimatedBuilder(
      animation: _fingerController,
      builder: (context, child) {
        double currentHeight = maxHeight * 0.25; // Altura base (Fechado)
        Color currentColor = inactiveColor;

        if (state == 1) {
          // Totalmente Aberto
          currentHeight = maxHeight;
          currentColor = activeColor;
        } else if (state == 2) {
          // Curvado (Metade da altura) - Efeito de pintura pela metade
          currentHeight = maxHeight * 0.55; 
          currentColor = activeColor;
        } else if (state == 3) {
          // Batendo (Loop que varia a altura do dedo para cima e para baixo)
          // Varia de 25% (fechado) a 100% (aberto)
          currentHeight = maxHeight * (0.25 + (0.75 * _fingerController.value));
          // Faz a cor acender e apagar durante a batida
          currentColor = Color.lerp(inactiveColor, activeColor, _fingerController.value) ?? activeColor;
        }

        return Container(
          width: width,
          height: currentHeight, 
          decoration: BoxDecoration(
            color: currentColor,
            borderRadius: BorderRadius.circular(width / 2),
            border: Border.all(
              color: Colors.white,
              width: 1.5,
            ),
          ),
        );
      }
    );
  }
}