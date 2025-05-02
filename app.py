from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv
from collections import deque

from liquipedia_client import LiquipediaClient

# Inicialize o cliente do Liquipedia
liquipedia_client = LiquipediaClient()

# Configuração do logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Carrega as variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)

# Verifica se a chave da API está configurada
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    logger.error("GEMINI_API_KEY não encontrada no arquivo .env")
    raise ValueError("GEMINI_API_KEY não configurada. Por favor, adicione sua chave no arquivo .env")

# Configuração da API do Gemini
try:
    genai.configure(api_key=api_key)
    # Lista os modelos disponíveis para debug
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            logger.info(f"Modelo disponível: {m.name}")
    
    # Usa o modelo mais recente e estável
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    logger.info("API do Gemini configurada com sucesso")
except Exception as e:
    logger.error(f"Erro ao configurar a API do Gemini: {str(e)}")
    raise

# Contexto inicial para o chatbot
INITIAL_CONTEXT = """
Você é um assistente virtual especializado em informações sobre a FURIA, time brasileiro de CS:GO. 
Sua base de conhecimento inclui:

[DADOS ATUALIZADOS]
{dynamic_data}
[/DADOS ATUALIZADOS]

Forneça informações sobre:
- Próximos jogos (consulte a seção de dados atualizados)
- Jogadores atuais
- Resultados recentes
- Histórico do time
- Conquistas importantes

Sempre que usar informações dos dados atualizados:
- Formate datas em negrito
- Use `backticks` para nomes de times
- Mantenha respostas curtas e informativas
- Inclua links relevantes quando possível: [Saiba mais](https://liquipedia.net/counterstrike/FURIA)

Quando o usuário solicitar informações sobre os produtos da FURIA, informe que o catálogo de produtos da FURIA pode ser visualizado no link: [Produtos FURIA](https://furia.gg/)
"""

# Armazena o histórico de conversas por sessão
conversation_histories = {}

def get_conversation_history(session_id):
    if session_id not in conversation_histories:
        conversation_histories[session_id] = deque(maxlen=10)  # Mantém as últimas 10 interações
    return conversation_histories[session_id]

def format_conversation_history(history):
    if not history:
        return ""
    return "\n\nHistórico da conversa:\n" + "\n".join(history)

@app.route('/')
def home():
    return render_template('landing.html')

@app.route('/chat')
def chat_interface():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        if not data:
            logger.error("Nenhum dado recebido na requisição")
            return jsonify({
                'status': 'error',
                'message': 'Nenhum dado recebido'
            }), 400
        
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            logger.error("Mensagem vazia recebida")
            return jsonify({
                'status': 'error',
                'message': 'Mensagem vazia'
            }), 400

        logger.debug(f"Mensagem recebida: {user_message}")
        
        # Obtém o histórico da conversa
        history = get_conversation_history(session_id)
        
        # Busca dados atualizados
        dynamic_data = "**Próximos Jogos:**\n" + liquipedia_client.format_upcoming_matches()
        
        # Atualiza o contexto com dados em tempo real
        updated_context = INITIAL_CONTEXT.format(dynamic_data=dynamic_data)
        
        # Combina o contexto atualizado com histórico e a nova mensagem
        full_prompt = f"{updated_context}{format_conversation_history(history)}\n\nUsuário: {user_message}"
        
        # Gera a resposta usando o Gemini
        response = model.generate_content(full_prompt)
        
        # Adiciona a interação ao histórico
        history.append(f"Usuário: {user_message}")
        history.append(f"Assistente: {response.text}")
        
        logger.debug(f"Resposta gerada: {response.text}")
        
        return jsonify({
            'status': 'success',
            'response': response.text
        })
    except Exception as e:
        error_message = str(e)
        logger.error(f"Erro ao processar mensagem: {error_message}", exc_info=True)
        
        # Verifica se é um erro de limite de requisições
        if "429" in error_message and "quota" in error_message.lower():
            user_friendly_message = "Desculpe, atingimos o limite de requisições do serviço. Por favor, aguarde alguns minutos e tente novamente."
        else:
            user_friendly_message = "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente mais tarde."
        
        return jsonify({
            'status': 'error',
            'message': user_friendly_message
        }), 500
    
    # Adicione métricas de monitoramento
@app.after_request
def log_request(response):
    logger.info(f"{request.remote_addr} - {request.method} {request.path} - {response.status_code}")
    return response

if __name__ == '__main__':
    app.run(debug=True) 