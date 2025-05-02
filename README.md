# FURIA ChatBot

Um chatbot desenvolvido para os fãs da FURIA, utilizando Python, Flask e a API do Google Gemini. O bot integra dados da Liquipedia para fornecer informações atualizadas sobre o time.

## Funcionalidades

- Interface web responsiva e moderna
- Integração com a API do Google Gemini para processamento de linguagem natural
- Integração com a Liquipedia para dados atualizados sobre a FURIA
- Respostas sobre jogadores, resultados, próximos jogos e história da FURIA
- Sistema de cache para otimizar requisições à Liquipedia
- Design alinhado com a identidade visual da FURIA

## Requisitos

- Python 3.8 ou superior
- Chave de API do Google Gemini

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/StarDropUwU/ProjetoChatbotFURIA/
cd ProjetoChatbotFURIA
```

2. Crie um ambiente virtual e ative-o:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure a chave da API:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione sua chave da API do Gemini:
   ```
   GEMINI_API_KEY=sua_chave_aqui
   ```

## Uso

1. Inicie o servidor:
```bash
python app.py
```

2. Acesse o chatbot em seu navegador:
```
http://localhost:5000
```

## Estrutura do Projeto

```
furia-chatbot/
├── app.py                    # Aplicação principal Flask
├── liquipedia_client.py      # Cliente para integração com a Liquipedia
├── test_liquipedia_client.py # Testes do cliente Liquipedia
├── requirements.txt          # Dependências do projeto
├── .env                      # Configurações (não versionado)
├── cache/                    # Diretório para cache de dados
└── templates/
    └── index.html           # Interface web
```

## Dependências Principais

- Flask 3.0.2 - Framework web
- Flask-CORS 4.0.0 - Suporte a CORS
- Google Generative AI 0.3.2 - API do Gemini
- Python-dotenv 1.0.1 - Gerenciamento de variáveis de ambiente
- Requests 2.31.0 - Requisições HTTP
- BeautifulSoup4 4.12.3 - Web scraping
