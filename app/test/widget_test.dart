import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:app/main.dart';

void main() {
  testWidgets('Chat UI smoke test', (WidgetTester tester) async {
    // Para testes de widgets não lidarem com chamadas reais do method channel do plugin de voz,
    // apenas validamos que a UI carrega a estrutura principal.
    await tester.pumpWidget(const FalaComaMaoApp());
    expect(find.text('FalaComaMão'), findsWidgets);
    expect(find.byType(CircleAvatar), findsOneWidget);
  });
}
