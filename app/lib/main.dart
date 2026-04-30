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
  String _recognizedText = '';
  
  final List<ChatMessage> _messages = [
    ChatMessage(text: 'Fale com a mão', isUser: false),
  ];

  @override
  void initState() {
    super.initState();
    _speech = stt.SpeechToText();
  }

  void _processFinalText(String text) {
    if (text.isEmpty) return;
    
    // 1. Adiciona a mensagem do usuário e a resposta provisória do robô
    setState(() {
      _messages.add(ChatMessage(text: text, isUser: true));
      _messages.add(ChatMessage(
        text: 'Analisando o áudio...', 
        isUser: false, 
        status: 'analyzing',
      ));
      _recognizedText = ''; // Limpa o buffer de reconhecimento
    });
    
    // 2. Chama a API passando o índice exato da mensagem do robô que deve ser atualizada
    final robotMessageIndex = _messages.length - 1;
    enviarComandoParaServidor(text, robotMessageIndex);
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

  Future<void> enviarComandoParaServidor(String texto, int messageIndex) async {
    print('=================================');
    print('Enviando comando para o servidor HTTP: $texto');
    print('=================================');
    
    final url = Uri.parse('http://192.168.1.100:5000/api/comando');
    try {
      final response = await http.post(
        url,
        body: {'comando': texto},
      ).timeout(const Duration(seconds: 1)); // Timeout minúsculo já que a API não existe
      print('Resposta do servidor: ${response.statusCode}');
    } catch (e) {
      print('Erro de rede (esperado, API offline): $e');
    }

    // SIMULAÇÃO DO TEMPO DE PROCESSAMENTO/MOVIMENTO DA MÃO (3 SEGUNDOS)
    await Future.delayed(const Duration(seconds: 3));

    // Ao terminar, atualiza o status do robô para "agindo"
    if (mounted) {
      setState(() {
        _messages[messageIndex].text = 'Executando movimento...';
        _messages[messageIndex].status = 'acting';
        _isProcessing = false; // Libera o sistema para uma nova fala
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
          Padding(
            padding: const EdgeInsets.only(bottom: 40.0, top: 20.0),
            child: Center(
              child: GestureDetector(
                onTap: _listen,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  width: _isListening ? 110 : 100,
                  height: _isListening ? 110 : 100,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: _isListening 
                          ? [Colors.redAccent, Colors.deepOrange]
                          : [
                              Theme.of(context).colorScheme.primary,
                              const Color(0xFF8E24AA),
                            ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: (_isListening ? Colors.redAccent : Theme.of(context).colorScheme.primary)
                            .withOpacity(0.5),
                        blurRadius: _isListening ? 25 : 15,
                        spreadRadius: _isListening ? 5 : 0,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  child: Icon(
                    _isListening ? Icons.mic_off : Icons.mic, 
                    color: Colors.white,
                    size: 50,
                  ),
                ),
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
            const SizedBox(height: 12),
            const Center(
              child: Icon(
                Icons.back_hand, // Placeholder animado no futuro
                size: 48, 
                color: Color(0xFF6200EA),
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
