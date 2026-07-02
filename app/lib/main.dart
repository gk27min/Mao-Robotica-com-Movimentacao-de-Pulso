import 'dart:convert';
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
      home: const ChatScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

// Classe estrutural para as mensagens
class ChatMessage {
  String text;
  final bool isUser;
  String status; // 'none', 'analyzing', 'acting'

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
  bool _hasText = false;
  String _recognizedText = '';

  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  final List<ChatMessage> _messages = [
    ChatMessage(text: 'Fale com a mão', isUser: false),
  ];

  @override
  void initState() {
    super.initState();
    _speech = stt.SpeechToText();
    _textController.addListener(() {
      final hasText = _textController.text.trim().isNotEmpty;
      if (hasText != _hasText) setState(() => _hasText = hasText);
    });
  }

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _processFinalText(String text) {
    if (text.isEmpty) return;

    setState(() {
      _messages.add(ChatMessage(text: text, isUser: true));
      _messages.add(ChatMessage(
        text: 'Analisando...',
        isUser: false,
        status: 'analyzing',
      ));
      _recognizedText = '';
    });

    _scrollToBottom();

    final robotMessageIndex = _messages.length - 1;
    enviarComandoParaServidor(text, robotMessageIndex);
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
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
      setState(() => _isListening = false);
      _speech.stop();
      // Removido disparo manual. A responsabilidade agora é apenas do finalResult.
    }
  }

  void _sendTypedText() {
    if (_isProcessing) return;
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    _textController.clear();
    _isProcessing = true;
    _processFinalText(text);
  }

  Widget _buildActionButton({
    Key? key,
    required VoidCallback? onTap,
    required IconData icon,
    required bool isListening,
  }) {
    final bool disabled = onTap == null;
    return GestureDetector(
      key: key,
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          gradient: disabled
              ? null
              : LinearGradient(
                  colors: isListening
                      ? [Colors.redAccent, Colors.deepOrange]
                      : [
                          Theme.of(context).colorScheme.primary,
                          const Color(0xFF8E24AA),
                        ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
          color: disabled ? Colors.grey[300] : null,
          shape: BoxShape.circle,
          boxShadow: disabled
              ? []
              : [
                  BoxShadow(
                    color: (isListening
                            ? Colors.redAccent
                            : Theme.of(context).colorScheme.primary)
                        .withOpacity(isListening ? 0.5 : 0.3),
                    blurRadius: isListening ? 16 : 8,
                    spreadRadius: isListening ? 2 : 0,
                    offset: const Offset(0, 3),
                  ),
                ],
        ),
        child: Icon(
          icon,
          color: disabled ? Colors.grey[600] : Colors.white,
          size: 22,
        ),
      ),
    );
  }

  // Endereço IP do servidor Python na rede local.
  static const String _serverUrl = 'http://192.168.18.201:5000/api/comando';

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
        final respostaTexto = (data['resposta_texto'] as String?)?.isNotEmpty == true
            ? data['resposta_texto'] as String
            : data['detalhes'] as String? ?? 'Comando processado.';

        setState(() {
          _messages[messageIndex].text = sucesso
              ? respostaTexto
              : 'Não reconheci o comando. Tente novamente.';
          _messages[messageIndex].status = sucesso ? 'acting' : 'none';
          _isProcessing = false;
        });
        _scrollToBottom();
      } else {
        setState(() {
          _messages[messageIndex].text =
              'Erro no servidor (${response.statusCode}). Tente novamente.';
          _messages[messageIndex].status = 'none';
          _isProcessing = false;
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _messages[messageIndex].text =
            'Não foi possível conectar ao servidor. Verifique se o backend está rodando.';
        _messages[messageIndex].status = 'none';
        _isProcessing = false;
      });
    }
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
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert, color: Colors.black87),
            onSelected: (String value) {
              if (value == 'biblioteca') {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const SignsLibraryScreen()),
                );
              } else if (value == 'cadastrar') {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (context) => const RegisterSignScreen()),
                );
              }
            },
            itemBuilder: (BuildContext context) => <PopupMenuEntry<String>>[
              const PopupMenuItem<String>(
                value: 'biblioteca',
                child: Text('Ver Sinais Registrados'),
              ),
              const PopupMenuItem<String>(
                value: 'cadastrar',
                child: Text('Cadastrar Novo Sinal'),
              ),
            ],
          ),
        ],
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
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.06),
                  blurRadius: 8,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: SafeArea(
              top: false,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Expanded(
                    child: Container(
                      constraints: const BoxConstraints(maxHeight: 120),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF0F2F5),
                        borderRadius: BorderRadius.circular(24),
                      ),
                      child: TextField(
                        controller: _textController,
                        enabled: !_isProcessing && !_isListening,
                        maxLines: null,
                        keyboardType: TextInputType.multiline,
                        textCapitalization: TextCapitalization.sentences,
                        style: const TextStyle(fontSize: 15),
                        decoration: const InputDecoration(
                          hintText: 'Digite ou fale um comando...',
                          hintStyle: TextStyle(color: Colors.black38, fontSize: 15),
                          contentPadding: EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                          border: InputBorder.none,
                        ),
                        onSubmitted: (_) => _sendTypedText(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  AnimatedSwitcher(
                    duration: const Duration(milliseconds: 200),
                    transitionBuilder: (child, animation) =>
                        ScaleTransition(scale: animation, child: child),
                    child: _hasText
                        ? _buildActionButton(
                            key: const ValueKey('send'),
                            onTap: _sendTypedText,
                            icon: Icons.send_rounded,
                            isListening: false,
                          )
                        : _buildActionButton(
                            key: const ValueKey('mic'),
                            onTap: _isProcessing ? null : _listen,
                            icon: _isListening ? Icons.mic_off : Icons.mic,
                            isListening: _isListening,
                          ),
                  ),
                ],
              ),
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

    // Constrói o conteúdo do balão com base no status do robô
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
        content = Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(message ?? '', style: textStyle),
            const SizedBox(height: 8),
            Text(
              '(Observe a mão)',
              style: TextStyle(
                color: isMe ? Colors.white70 : Colors.black38,
                fontSize: 12,
                fontStyle: FontStyle.italic,
              ),
            ),
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
          color: isMe ? null : Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(24),
            topRight: const Radius.circular(24),
            bottomLeft: Radius.circular(isMe ? 24 : 4),
            bottomRight: Radius.circular(isMe ? 4 : 24),
          ),
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
