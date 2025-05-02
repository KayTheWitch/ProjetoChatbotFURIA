# FURIA ChatBot

Um chatbot desenvolvido para os fãs da FURIA, time brasileiro de CS, utilizando Python e a API do Google Gemini.

## Funcionalidades

- Interface web responsiva e moderna
- Integração com a API do Google Gemini
- Respostas sobre jogadores, resultados, próximos jogos e história da FURIA
- Design alinhado com a identidade visual da FURIA

## Requisitos

- Python 3.8 ou superior
- Chave de API do Google Gemini

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/furia-chatbot.git
cd furia-chatbot
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
├── app.py              # Aplicação principal
├── requirements.txt    # Dependências
├── .env               # Configurações (não versionado)
└── templates/
    └── index.html     # Interface web
```

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está sob a licença MIT. 