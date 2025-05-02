from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv
from collections import deque
import time
import hashlib
import json

from liquipedia_client import LiquipediaClient

# Inicializa o cliente do Liquipedia
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
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    logger.info("API do Gemini configurada com sucesso")
except Exception as e:
    logger.error(f"Erro ao configurar a API do Gemini: {str(e)}")
    raise

# Sistema de cache para respostas
response_cache = {}
CACHE_DURATION = 300  # 5 minutos em segundos

# Limite de requisições
RATE_LIMIT = 60  # requisições por minuto
request_timestamps = deque(maxlen=RATE_LIMIT)

def check_rate_limit():
    """Verifica se o limite de requisições foi atingido"""
    current_time = time.time()
    if len(request_timestamps) >= RATE_LIMIT:
        oldest_timestamp = request_timestamps[0]
        if current_time - oldest_timestamp < 60:  # 60 segundos
            return False
        request_timestamps.popleft()
    request_timestamps.append(current_time)
    return True

def get_cached_response(message_hash):
    """Obtém uma resposta do cache se disponível"""
    if message_hash in response_cache:
        cache_entry = response_cache[message_hash]
        if time.time() - cache_entry['timestamp'] < CACHE_DURATION:
            return cache_entry['response']
        else:
            del response_cache[message_hash]
    return None

def cache_response(message_hash, response):
    """Armazena uma resposta no cache"""
    response_cache[message_hash] = {
        'response': response,
        'timestamp': time.time()
    }

def get_dynamic_data():
    """Obtém dados atualizados da Liquipedia"""
    try:
        upcoming_matches = liquipedia_client.get_upcoming_matches()
        recent_results = liquipedia_client.get_recent_results()
        current_roster = liquipedia_client.get_current_roster()
        
        dynamic_data = {
            'upcoming_matches': upcoming_matches,
            'recent_results': recent_results,
            'current_roster': current_roster,
            'timestamp': time.time()
        }
        
        return dynamic_data
    except Exception as e:
        logger.error(f"Erro ao obter dados dinâmicos: {str(e)}")
        return None

# Contexto inicial para o chatbot
INITIAL_CONTEXT = """
Você é um assistente virtual especializado em informações sobre a FURIA, time brasileiro de CS2 
Sua base de conhecimento inclui:

[DADOS ATUALIZADOS]
{dynamic_data}
[/DADOS ATUALIZADOS]

Forneça informações sobre:
- Próximos jogos (consulte a seção de dados atualizados)
- Jogadores atuais do time de CS2 (incluindo posições e status)
- Resultados recentes
- Histórico do time
- Conquistas importantes

Sempre que usar informações dos dados atualizados:
- Formate datas em negrito
- Use `backticks` para nomes de times
- Mantenha respostas curtas e informativas
- Inclua links relevantes quando possível: [Saiba mais](https://liquipedia.net/counterstrike/FURIA)

Quando o usuário solicitar informações sobre os produtos da FURIA, informe que o catálogo de produtos da FURIA pode ser visualizado no link: [Produtos FURIA](https://furia.gg/)

IMPORTANTE: Forneça informações APENAS sobre o time de CS2 da FURIA.
"""

# Armazena o histórico de conversas por sessão
conversation_histories = {}

def get_conversation_history(session_id):
    """Obtém o histórico de conversas de uma sessão"""
    if session_id not in conversation_histories:
        conversation_histories[session_id] = deque(maxlen=5)
    return conversation_histories[session_id]

def format_conversation_history(history):
    """Formata o histórico de conversas"""
    if not history:
        return ""
    return "\n".join(history) + "\n"

@app.route('/')
def home():
    """Rota para a página inicial"""
    return render_template('landing.html')

@app.route('/chat')
def chat_interface():
    """Rota para a interface do chat"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint para processar mensagens do chat"""
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

        if not check_rate_limit():
            return jsonify({
                'status': 'error',
                'message': 'Limite de requisições atingido. Por favor, aguarde um minuto.'
            }), 429

        message_hash = hashlib.md5(user_message.encode()).hexdigest()
        cached_response = get_cached_response(message_hash)
        if cached_response:
            return jsonify({
                'status': 'success',
                'response': cached_response
            })

        logger.debug(f"Mensagem recebida: {user_message}")
        
        history = get_conversation_history(session_id)
        
        dynamic_data = get_dynamic_data()
        if dynamic_data:
            formatted_data = f"""
**Próximos Jogos:**
{format_upcoming_matches(dynamic_data['upcoming_matches'])}

**Resultados Recentes:**
{format_recent_results(dynamic_data['recent_results'])}

**Elenco Atual:**
{format_current_roster(dynamic_data['current_roster'])}
"""
        else:
            formatted_data = "Dados temporariamente indisponíveis. Por favor, tente novamente em alguns minutos."
        
        updated_context = INITIAL_CONTEXT.format(dynamic_data=formatted_data)
        full_prompt = f"{updated_context}{format_conversation_history(history)}\n\nUsuário: {user_message}"
        
        response = model.generate_content(full_prompt)
        
        history.append(f"Usuário: {user_message}")
        history.append(f"Assistente: {response.text}")
        
        cache_response(message_hash, response.text)
        
        logger.debug(f"Resposta gerada: {response.text}")
        
        return jsonify({
            'status': 'success',
            'response': response.text
        })
    except Exception as e:
        error_message = str(e)
        logger.error(f"Erro ao processar mensagem: {error_message}", exc_info=True)
        
        if "429" in error_message and "quota" in error_message.lower():
            user_friendly_message = "Desculpe, atingimos o limite de requisições do serviço. Por favor, aguarde alguns minutos e tente novamente."
        else:
            user_friendly_message = "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente mais tarde."
        
        return jsonify({
            'status': 'error',
            'message': user_friendly_message
        }), 500

def format_upcoming_matches(matches):
    """Formata os próximos jogos para exibição"""
    if not matches:
        return "Nenhum jogo agendado encontrado"
    return "\n".join([
        f"- **{match['date']}**: `{match['team1']}` vs `{match['team2']}` ({match['tournament']})"
        for match in matches
    ])

def format_recent_results(results):
    """Formata os resultados recentes para exibição"""
    if not results:
        return "Nenhum resultado recente encontrado"
    return "\n".join([
        f"- **{result['date']}**: `{result['team1']}` {result['score']} `{result['team2']}` ({result['tournament']})"
        for result in results
    ])

def format_current_roster(roster):
    """Formata o elenco atual para exibição"""
    if not roster:
        return "Informações do elenco não disponíveis"
    
    active_players = [player for player in roster if player.get('is_active', False)]
    inactive_players = [player for player in roster if not player.get('is_active', False)]
    
    formatted_roster = []
    
    if active_players:
        formatted_roster.append("**Jogadores Ativos:**")
        for player in active_players:
            position = player.get('position', 'Unknown')
            if position == "Unknown":
                formatted_roster.append(f"- {player['id']}")
            else:
                formatted_roster.append(f"- {player['id']} ({position})")
    
    if inactive_players:
        formatted_roster.append("\n**Jogadores Inativos:**")
        for player in inactive_players:
            position = player.get('position', 'Unknown')
            if position == "Unknown":
                formatted_roster.append(f"- {player['id']}")
            else:
                formatted_roster.append(f"- {player['id']} ({position})")
    
    return "\n".join(formatted_roster)

@app.after_request
def log_request(response):
    """Registra informações sobre cada requisição"""
    logger.info(f"{request.remote_addr} - {request.method} {request.path} - {response.status_code}")
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 