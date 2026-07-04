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
    ChatMessage(text: 'Fale ou digite para conversar com a mão', isUser: false),
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
  static const String _serverUrl = 'http://172.21.31.245:5000/api/comando';

  Future<void> enviarComandoParaServidor(String texto, int messageIndex) async {
    final url = Uri.parse(_serverUrl);

    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'texto': texto}),
      ).timeout(const Duration(seconds: 10));

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
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sinais Registrados'),
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => const RegisterSignScreen()),
          );
        },
        icon: const Icon(Icons.add),
        label: const Text('Cadastrar Sinal'),
      ),
      body: const Center(
        child: Text('Biblioteca de gestos', style: TextStyle(fontSize: 18)),
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
