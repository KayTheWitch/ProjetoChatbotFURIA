import logging
from liquipedia_client import LiquipediaClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_liquipedia_client():
    client = LiquipediaClient()
    
    # Test 1: Get upcoming matches
    logger.info("Testing upcoming matches...")
    wiki_text = client.fetch_page('FURIA/Matches')
    if wiki_text:
        logger.debug("Raw matches page content:")
        logger.debug(wiki_text[:1000])
    matches = client.get_upcoming_matches()
    if matches:
        logger.info("✓ Found upcoming matches:")
        for match in matches:
            logger.info(f"  - {match['date']}: {match['team1']} vs {match['team2']} ({match['tournament']})")
    else:
        logger.warning("✗ No upcoming matches found")
    
    # Test 2: Get current roster
    logger.info("\nTesting current roster...")
    wiki_text = client.fetch_page('FURIA')
    if wiki_text:
        logger.debug("Raw main page content:")
        logger.debug(wiki_text[:1000])
    roster = client.get_current_roster()
    if roster:
        logger.info("✓ Found current roster:")
        for player in roster:
            logger.info(f"  - {player['name']} ({player['role']})")
    else:
        logger.warning("✗ No roster information found")
    
    # Test 3: Get recent results
    logger.info("\nTesting recent results...")
    wiki_text = client.fetch_page('FURIA/Results')
    if wiki_text:
        logger.debug("Raw results page content:")
        logger.debug(wiki_text[:1000])
    results = client.get_recent_results()
    if results:
        logger.info("✓ Found recent results:")
        for result in results:
            logger.info(f"  - {result['date']}: {result['team1']} {result['score']} {result['team2']} ({result['tournament']})")
    else:
        logger.warning("✗ No recent results found")

if __name__ == "__main__":
    test_liquipedia_client() 