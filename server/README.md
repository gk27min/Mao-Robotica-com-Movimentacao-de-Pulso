# Backend Python — FalaComaMão / LIBRAS-BOT

Servidor intermediário que conecta o app Flutter, o **Ollama** (LLM local) e,
nas próximas etapas, o **Arduino R4 WiFi** via Bluetooth Low Energy.

## Arquitetura desta etapa (1)

```
  Flutter (texto NLP)
        │  HTTP POST /api/comando
        ▼
   app.py  ─────────────► ollama_client.py ──► Ollama (llama3.1:8b)
        │                                          │
        │◄─────── sinal escolhido + ângulos ───────┘
        │
        └── (etapa 4) BLE ──► Arduino R4 ──► servos
```

## Estrutura

| Arquivo               | Função                                                              |
|-----------------------|---------------------------------------------------------------------|
| `app.py`              | Servidor Flask + endpoints REST                                     |
| `ollama_client.py`    | Cliente da API Ollama com prompt de classificação de intenção       |
| `signs.json`          | Sinais cadastrados (id, nome, descrição, sinônimos, ângulos)        |
| `test_ollama.py`      | REPL pra testar o cérebro sem precisar do Flutter nem do Arduino    |
| `requirements.txt`    | Dependências Python                                                 |

## Pré-requisitos

1. **Python 3.10+** (verifique com `python --version` no PowerShell).
2. **Ollama** rodando em `http://localhost:11434` com `llama3.1:8b` puxado:
   ```powershell
   ollama list      # deve aparecer llama3.1:8b
   ```

## Instalação

Abra o PowerShell na pasta `server/` e rode:

```powershell
# (Opcional, mas recomendado) crie um ambiente virtual:
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instale as dependências:
pip install -r requirements.txt
```

> Se aparecer erro de execução de script no `Activate.ps1`, rode antes:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

## Teste rápido do cérebro (sem Flutter)

```powershell
python test_ollama.py
```

Digite frases — exemplos:

```
você> oi, tudo bem?         →  Oi  (id=oi)
você> falou, até mais         →  Tchau  (id=tchau)
você> show, beleza            →  OK  (id=ok)
você> que horas são?          →  nenhum sinal corresponde
```

Se isso funciona, a parte mais importante da etapa 1 está validada. ✔

## Rodando o servidor

```powershell
python app.py
```

Vai subir em `http://0.0.0.0:5000`. Pegue o IP do PC na rede (`ipconfig` →
"Endereço IPv4") e atualize a URL no Flutter em `app/lib/main.dart`.

### Endpoints disponíveis

| Método | Rota                       | O que faz                                                |
|--------|----------------------------|----------------------------------------------------------|
| GET    | `/api/status`              | Saúde do servidor + Ollama                               |
| GET    | `/api/sinais`              | Lista os sinais cadastrados                              |
| POST   | `/api/sinais`              | Cadastra novo sinal (corpo JSON)                         |
| DELETE | `/api/sinais/<id>`         | Remove um sinal                                          |
| POST   | `/api/comando`             | Recebe texto → Ollama escolhe sinal → devolve ângulos    |

### Exemplos de chamada (PowerShell)

Status:
```powershell
curl http://localhost:5000/api/status
```

Listar sinais:
```powershell
curl http://localhost:5000/api/sinais
```

Mandar um comando:
```powershell
curl -X POST http://localhost:5000/api/comando `
     -H "Content-Type: application/json" `
     -d '{"comando":"oi, tudo bem?"}'
```

Cadastrar um sinal novo:
```powershell
$body = @{
  id = "legal"
  nome = "Legal"
  descricao = "Sinalizar que algo é legal, maneiro, daora."
  sinonimos = @("daora","massa","maneiro","top")
  angulos = @{ polegar=180; indicador=0; medio=0; anelar=0; minimo=0; pulso=120 }
} | ConvertTo-Json
curl -X POST http://localhost:5000/api/sinais -H "Content-Type: application/json" -d $body
```

## Formato dos sinais (`signs.json`)

```jsonc
{
  "sinais": [
    {
      "id": "oi",                       // identificador único, snake_case
      "nome": "Oi",                     // exibição amigável
      "descricao": "Cumprimentar ...",  // o Ollama usa isso para decidir
      "sinonimos": ["olá", "salve"],    // ajuda o LLM a casar
      "angulos": {                      // 0..180 graus por servo
        "polegar": 0,
        "indicador": 180,
        "medio": 180,
        "anelar": 180,
        "minimo": 180,
        "pulso": 90
      }
    }
  ]
}
```

## Próximas etapas

- **2.** Telas de cadastro/biblioteca no Flutter consumindo `/api/sinais`.
- **3.** Firmware Arduino R4 com BLE + servos.
- **4.** Camada BLE no Python (`bleak`) — substituir o `TODO` em `app.py`.
- **5.** Polimento end-to-end (reconexão, feedback no app, logging).
