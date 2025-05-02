import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
import time

logger = logging.getLogger(__name__)
load_dotenv()

class LiquipediaClient:
    def __init__(self):
        self.base_url = "https://liquipedia.net/counterstrike/api.php"
        self.cache = {}
        self.cache_duration = timedelta(minutes=10)
        self.headers = {
            'User-Agent': 'FURIA Chatbot/1.0 (https://github.com/StarDropUwU/ProjetoChatbotFURIA/)',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        self.last_request_time = 0
        self.min_request_interval = 2  # Intervalo mínimo entre requisições em segundos

    def _rate_limit(self):
        """Controla o intervalo entre requisições para evitar sobrecarga"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    def fetch_page(self, page_title):
        """Busca uma página da Liquipedia"""
        try:
            self._rate_limit()
            
            params = {
                'action': 'parse',
                'format': 'json',
                'page': page_title,
                'prop': 'text',
                'formatversion': '2'
            }
            
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Falha ao buscar página. Status code: {response.status_code}")
                return None
                
            data = response.json()
            return data.get('parse', {}).get('text', '')
            
        except requests.exceptions.Timeout:
            logger.error("Requisição excedeu o tempo limite")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Falha na requisição: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}")
            return None

    def get_upcoming_matches(self):
        """Obtém os próximos jogos da página de partidas"""
        if 'upcoming' in self.cache and datetime.now() - self.cache['upcoming']['timestamp'] < self.cache_duration:
            return self.cache['upcoming']['data']
        
        wiki_text = self.fetch_page('FURIA/Matches')
        if not wiki_text:
            return []
            
        matches = self.parse_upcoming_matches(wiki_text)
        self.cache['upcoming'] = {
            'timestamp': datetime.now(),
            'data': matches
        }
        return matches

    def get_recent_results(self):
        """Obtém os resultados recentes da página de resultados"""
        if 'results' in self.cache and datetime.now() - self.cache['upcoming']['timestamp'] < self.cache_duration:
            return self.cache['results']['data']
        
        wiki_text = self.fetch_page('FURIA/Results')
        if not wiki_text:
            return []
            
        results = self.parse_recent_results(wiki_text)
        self.cache['results'] = {
            'timestamp': datetime.now(),
            'data': results
        }
        return results

    def get_current_roster(self):
        """Obtém o elenco atual da página principal"""
        if 'roster' in self.cache and datetime.now() - self.cache['roster']['timestamp'] < self.cache_duration:
            return self.cache['roster']['data']
        
        wiki_text = self.fetch_page('FURIA')
        if not wiki_text:
            return []
            
        roster = self.parse_current_roster(wiki_text)
        self.cache['roster'] = {
            'timestamp': datetime.now(),
            'data': roster
        }
        return roster

    def format_upcoming_matches(self):
        """Formata os próximos jogos para exibição"""
        matches = self.get_upcoming_matches()
        if not matches:
            return "Nenhum jogo agendado encontrado"
            
        formatted = []
        for match in matches:
            formatted.append(
                f"- **{match['date']}**: `{match['team1']}` vs `{match['team2']}` ({match['tournament']})"
            )
        return "\n".join(formatted)

    def parse_upcoming_matches(self, html_content):
        """Extrai informações dos próximos jogos do HTML"""
        matches = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            match_tables = soup.find_all('table', class_='wikitable')
            
            for table in match_tables:
                header_row = table.find('tr')
                if not header_row:
                    continue
                    
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                if not ('date' in headers and 'tournament' in headers):
                    continue
                
                date_idx = headers.index('date')
                tournament_idx = -1
                team1_idx = -1
                team2_idx = -1
                
                for i, header in enumerate(headers):
                    if header == 'tournament':
                        tournament_idx = i
                    elif header == 'team 1' or header == 'participant':
                        team1_idx = i
                    elif header == 'team 2' or header == 'opponent':
                        team2_idx = i
                
                if tournament_idx == -1 or team1_idx == -1:
                    continue
                
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) > max(date_idx, tournament_idx, team1_idx):
                        date = cols[date_idx].get_text(strip=True)
                        team1 = cols[team1_idx].get_text(strip=True)
                        team2 = cols[team2_idx].get_text(strip=True) if team2_idx != -1 and len(cols) > team2_idx else "TBD"
                        tournament = cols[tournament_idx].get_text(strip=True)
                        
                        if date and team1 and tournament:
                            match = {
                                'date': date,
                                'team1': team1,
                                'team2': team2,
                                'tournament': tournament
                            }
                            matches.append(match)
            
        except Exception as e:
            logger.error(f"Erro ao extrair próximos jogos: {str(e)}")
            
        return matches

    def parse_current_roster(self, html_content):
        """Extrai informações do elenco atual do HTML"""
        roster = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            tables = soup.find_all('table')
            
            for table in tables:
                header_row = table.find('tr')
                if not header_row:
                    continue
                    
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                if not ('id' in headers or 'player' in headers):
                    continue
                
                id_idx = -1
                position_idx = -1
                game_idx = -1
                status_idx = -1
                
                for i, header in enumerate(headers):
                    if header in ['id', 'player']:
                        id_idx = i
                    elif header in ['role', 'position']:
                        position_idx = i
                    elif header == 'game':
                        game_idx = i
                    elif header in ['status', 'active']:
                        status_idx = i
                
                if id_idx == -1:
                    continue
                
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) > max(id_idx, position_idx if position_idx != -1 else 0):
                        player_id = cols[id_idx].get_text(strip=True)
                        position = cols[position_idx].get_text(strip=True) if position_idx != -1 and len(cols) > position_idx else "Unknown"
                        game = cols[game_idx].get_text(strip=True) if game_idx != -1 and len(cols) > game_idx else "CS2"
                        status = cols[status_idx].get_text(strip=True) if status_idx != -1 and len(cols) > status_idx else "Active"
                        
                        if game.upper() == "CS2":
                            is_active = status.lower() in ['active', 'starter', 'main']
                            
                            if position == "Unknown":
                                row_classes = row.get('class', [])
                                row_data = row.get('data-role', '')
                                
                                if any(pos in str(row_classes).lower() for pos in ['entry', 'fragger', 'lurker', 'igl', 'support', 'awper']):
                                    position = next(pos for pos in ['Entry Fragger', 'Lurker', 'IGL', 'Support', 'AWPer'] 
                                                  if pos.lower() in str(row_classes).lower())
                                elif any(pos in row_data.lower() for pos in ['entry', 'fragger', 'lurker', 'igl', 'support', 'awper']):
                                    position = next(pos for pos in ['Entry Fragger', 'Lurker', 'IGL', 'Support', 'AWPer'] 
                                                  if pos.lower() in row_data.lower())
                            
                            player = {
                                'id': player_id,
                                'position': position,
                                'game': 'CS2',
                                'is_active': is_active
                            }
                            roster.append(player)
            
        except Exception as e:
            logger.error(f"Erro ao extrair elenco: {str(e)}")
            
        return roster

    def parse_recent_results(self, html_content):
        """Extrai informações dos resultados recentes do HTML"""
        results = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            results_tables = soup.find_all('table', class_='wikitable')
            
            for table in results_tables:
                header_row = table.find('tr')
                if not header_row:
                    continue
                    
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                if not ('date' in headers and ('opponent' in headers or 'team 2' in headers)):
                    continue
                
                date_idx = headers.index('date')
                team1_idx = -1
                score_idx = -1
                team2_idx = -1
                tournament_idx = -1
                
                for i, header in enumerate(headers):
                    if header == 'team 1' or header == 'participant':
                        team1_idx = i
                    elif header == 'team 2' or header == 'opponent':
                        team2_idx = i
                    elif header == 'score' or header == 'result':
                        score_idx = i
                    elif header == 'tournament' or header == 'event':
                        tournament_idx = i
                
                if team1_idx == -1 or team2_idx == -1:
                    continue
                
                for row in table.find_all('tr')[1:]:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) > max(date_idx, team1_idx, team2_idx):
                        date = cols[date_idx].get_text(strip=True)
                        team1 = cols[team1_idx].get_text(strip=True)
                        team2 = cols[team2_idx].get_text(strip=True)
                        score = cols[score_idx].get_text(strip=True) if score_idx != -1 and len(cols) > score_idx else "vs"
                        tournament = cols[tournament_idx].get_text(strip=True) if tournament_idx != -1 and len(cols) > tournament_idx else "Unknown"
                        
                        if date and team1 and team2:
                            result = {
                                'date': date,
                                'team1': team1,
                                'score': score,
                                'team2': team2,
                                'tournament': tournament
                            }
                            results.append(result)
            
        except Exception as e:
            logger.error(f"Erro ao extrair resultados: {str(e)}")
            
        return results

# Exemplo de uso:
# client = LiquipediaClient()
# print(client.format_upcoming_matches())
