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
            'User-Agent': 'FURIA Bot/1.0 (https://github.com/yourusername/furia-chatbot)',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        self.last_request_time = 0
        self.min_request_interval = 2  # Minimum seconds between requests

    def _rate_limit(self):
        """Ensure we don't make requests too frequently"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    def fetch_page(self, page_title):
        """Fetch a page from Liquipedia"""
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
                logger.error(f"Failed to fetch page. Status code: {response.status_code}")
                return None
                
            data = response.json()
            return data.get('parse', {}).get('text', '')
            
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None

    def get_upcoming_matches(self):
        """Get upcoming matches from the matches page"""
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
        """Get recent results from the results page"""
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
        """Get current roster from the main page"""
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
        """Parse upcoming matches from HTML content"""
        matches = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all match tables
            match_tables = soup.find_all('table', class_='wikitable')
            
            for table in match_tables:
                # Check if this is a matches table
                header_row = table.find('tr')
                if not header_row:
                    continue
                    
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                if not ('date' in headers and 'tournament' in headers):
                    continue
                
                # Find column indices
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
                
                # Parse each match row
                for row in table.find_all('tr')[1:]:  # Skip header row
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
            logger.error(f"Error parsing upcoming matches: {str(e)}")
            
        return matches

    def parse_current_roster(self, html_content):
        """Parse current roster from HTML content"""
        roster = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all tables
            tables = soup.find_all('table')
            
            for table in tables:
                # Check if this is a roster table
                header_row = table.find('tr')
                if not header_row:
                    continue
                    
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                if not ('id' in headers or 'player' in headers or 'name' in headers):
                    continue
                
                # Find column indices
                name_idx = -1
                role_idx = -1
                
                for i, header in enumerate(headers):
                    if header in ['id', 'player', 'name']:
                        name_idx = i
                    elif header in ['role', 'position']:
                        role_idx = i
                
                if name_idx == -1:
                    continue
                
                # Parse each player row
                for row in table.find_all('tr')[1:]:  # Skip header row
                    cols = row.find_all(['td', 'th'])
                    if len(cols) > max(name_idx, role_idx if role_idx != -1 else 0):
                        name = cols[name_idx].get_text(strip=True)
                        role = cols[role_idx].get_text(strip=True) if role_idx != -1 and len(cols) > role_idx else "Player"
                        
                        if name:
                            player = {
                                'name': name,
                                'role': role
                            }
                            roster.append(player)
            
        except Exception as e:
            logger.error(f"Error parsing roster: {str(e)}")
            
        return roster

    def parse_recent_results(self, html_content):
        """Parse recent results from HTML content"""
        results = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all results tables
            results_tables = soup.find_all('table', class_='wikitable')
            
            for table in results_tables:
                # Check if this is a results table
                header_row = table.find('tr')
                if not header_row:
                    continue
                    
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                if not ('date' in headers and ('opponent' in headers or 'team 2' in headers)):
                    continue
                
                # Find column indices
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
                
                # Parse each result row
                for row in table.find_all('tr')[1:]:  # Skip header row
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
            logger.error(f"Error parsing results: {str(e)}")
            
        return results

# Exemplo de uso:
# client = LiquipediaClient()
# print(client.format_upcoming_matches())
