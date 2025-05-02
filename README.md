# Chatbot FURIA CS2

Um chatbot especializado em fornecer informações sobre o time FURIA de CS2, desenvolvido com Flask e integrado à API do Google Gemini.

## 🎯 Funcionalidades

- Informações sobre o elenco atual do time de CS2
  - Lista de jogadores ativos e inativos
  - Posições dos jogadores
  - Status de atividade
- Próximos jogos agendados
- Resultados recentes
- Histórico do time
- Conquistas importantes
- Informações sobre produtos FURIA

## 🛠️ Tecnologias Utilizadas

- Python 3.x
- Flask (Framework Web)
- Google Gemini API (IA Generativa)
- BeautifulSoup4 (Web Scraping)
- Liquipedia API (Dados do time)

## 📋 Pré-requisitos

- Python 3.x instalado
- Chave de API do Google Gemini
- Conexão com a internet

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/StarDropUwU/ProjetoChatbotFURIA.git
cd ProjetoChatbotFURIA
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione sua chave da API do Gemini:
```
GEMINI_API_KEY=sua_chave_aqui
```

## 🚀 Executando o Projeto

1. Inicie o servidor Flask:
```bash
python app.py
```

2. Acesse a interface web:
   - Página inicial: `http://localhost:5000`
   - Interface do chat: `http://localhost:5000/chat`

## 📝 Estrutura do Projeto

```
ProjetoChatbotFURIA/
├── app.py                 # Aplicação principal Flask
├── liquipedia_client.py   # Cliente para a API da Liquipedia
├── requirements.txt       # Dependências do projeto
├── .env                  # Variáveis de ambiente
└── templates/            # Templates HTML
    ├── index.html        # Interface do chat
    └── landing.html      # Página inicial
```

## 🔄 Funcionamento

1. O chatbot utiliza a API do Google Gemini para processar as mensagens
2. Dados do time são obtidos em tempo real da Liquipedia
3. Sistema de cache implementado para otimizar requisições
4. Rate limiting para evitar sobrecarga da API
5. Histórico de conversas mantido por sessão

## ⚙️ Configurações

- Cache de respostas: 5 minutos
- Limite de requisições: 60 por minuto
- Histórico de conversas: 5 interações por sessão
- Intervalo mínimo entre requisições à Liquipedia: 2 segundos

