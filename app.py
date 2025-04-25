from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
import os
import logging
from dotenv import load_dotenv

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
Seu objetivo é fornecer informações precisas e atualizadas sobre:
- Jogadores do time
- Resultados recentes
- Próximos jogos
- História do time
- Conquistas
- Notícias relevantes

Mantenha um tom amigável e empolgado, típico de um fã da FURIA.
Se não souber alguma informação, seja honesto e diga que não tem essa informação no momento.

IMPORTANTE: Formate todas as suas respostas usando Markdown. Use:
- **negrito** para ênfase
- *itálico* para citações ou termos técnicos
- # para títulos
- ## para subtítulos
- - para listas
- > para citações
- `código` para nomes de jogadores ou termos específicos do CS:GO
- Links quando relevante: [texto](url)
"""

@app.route('/')
def home():
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
        if not user_message:
            logger.error("Mensagem vazia recebida")
            return jsonify({
                'status': 'error',
                'message': 'Mensagem vazia'
            }), 400

        logger.debug(f"Mensagem recebida: {user_message}")
        
        # Combina o contexto inicial com a mensagem do usuário
        full_prompt = f"{INITIAL_CONTEXT}\n\nUsuário: {user_message}"
        
        # Gera a resposta usando o Gemini
        response = model.generate_content(full_prompt)
        
        logger.debug(f"Resposta gerada: {response.text}")
        
        return jsonify({
            'status': 'success',
            'response': response.text
        })
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Erro ao processar mensagem: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 