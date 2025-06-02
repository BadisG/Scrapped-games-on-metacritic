import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime
import re
import os

# --- Configuration ---
BASE_URL = "https://www.metacritic.com"
BROWSE_URL_TEMPLATE = "https://www.metacritic.com/browse/game/all/all/all-time/new/?releaseYearMin=1958&releaseYearMax=2025&page={}"
CSV_FILENAME = "games.csv"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
REQUEST_DELAY = 1
START_PAGE = 1

# --- Helper Functions ---
def format_date(date_str):
    """Converts various date formats to 'MM/DD/YYYY'."""
    if not date_str or date_str == "N/A":
        return "N/A"
    
    date_str = date_str.strip()
    
    # Try multiple date formats
    formats_to_try = [
        "%b %d, %Y",      # Mar 7, 2025
        "%B %d, %Y",      # March 7, 2025
        "%m/%d/%Y",       # 3/7/2025 or 03/07/2025
        "%m-%d-%Y",       # 3-7-2025 or 03-07-2025
        "%Y-%m-%d",       # 2025-03-07
    ]
    
    for fmt in formats_to_try:
        try:
            dt_obj = datetime.strptime(date_str, fmt)
            return dt_obj.strftime("%m/%d/%Y")  # Always return zero-padded format
        except ValueError:
            continue
    
    print(f"Warning: Could not parse date '{date_str}'")
    return date_str

def normalize_date(date_str):
    """Normalize date to MM/DD/YYYY format for consistent comparison."""
    if not date_str or date_str == "N/A":
        return "N/A"
    
    # If it's already in M/D/YYYY format, convert to MM/DD/YYYY
    try:
        parts = date_str.split('/')
        if len(parts) == 3:
            month, day, year = parts
            return f"{int(month):02d}/{int(day):02d}/{year}"
    except (ValueError, IndexError):
        pass
    
    return date_str

def extract_number_from_string(text):
    """Extracts the first number found in a string, handling commas (e.g., '1,014')."""
    if not text or text == "N/A":
        return "N/A"
    text = text.replace(',', '')
    match = re.search(r'\d+', text)
    return match.group(0) if match else "0"

def load_existing_games(csv_filename):
    """Load existing games from CSV file and return as a set of (title, date) tuples."""
    existing_games = set()
    if os.path.exists(csv_filename):
        try:
            with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip header row
                for row in reader:
                    if len(row) >= 2:  # Make sure we have at least title and date
                        title = row[0].strip()
                        date = normalize_date(row[1].strip())  # Normalize when loading
                        existing_games.add((title, date))
            print(f"Loaded {len(existing_games)} existing games from {csv_filename}")
        except Exception as e:
            print(f"Error reading existing CSV file: {e}")
            print("Starting with empty game list.")
    else:
        print(f"CSV file {csv_filename} not found. Starting fresh.")
    return existing_games

def is_game_exists(title, date, existing_games):
    """Check if a game with the same title and date already exists."""
    normalized_date = normalize_date(date)
    
    # Check against normalized versions of existing dates
    for existing_title, existing_date in existing_games:
        if (title == existing_title and 
            normalized_date == normalize_date(existing_date)):
            return True
    return False

def append_to_csv(csv_filename, new_games):
    """Append new games to the CSV file."""
    file_exists = os.path.exists(csv_filename)
    
    with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header if file doesn't exist
        if not file_exists:
            writer.writerow(['Title', 'Initial Release Date', 'User Rating', 'Number of Ratings'])
        
        # Write new games
        writer.writerows(new_games)

def scrape_game_details(card, index, total_cards, existing_games, page_number):
    """Scrape details for a single game card."""
    game_title = "N/A"
    release_date_formatted = "N/A"
    user_score = "N/A"
    num_user_ratings = "0"

    # Extract game title
    title_div = card.find('div', class_='c-finderProductCard_title')
    if title_div and 'data-title' in title_div.attrs:
        game_title = title_div['data-title'].strip()
    else:
        title_h3 = card.find('h3', class_='c-finderProductCard_titleHeading')
        if title_h3 and title_h3.span:
            game_title = title_h3.span.get_text(strip=True)

    # Extract release date
    meta_div = card.find('div', class_='c-finderProductCard_meta')
    if meta_div:
        date_span = meta_div.find('span', class_='u-text-uppercase')
        if date_span:
            release_date_formatted = format_date(date_span.get_text(strip=True))

    # Check if game already exists
    if is_game_exists(game_title, release_date_formatted, existing_games):
        print(f"Skipping ({index+1}/{total_cards}) [Page {page_number}]: {game_title} ({release_date_formatted}) - Already exists")
        return None

    # Extract detail page URL
    link_tag = card.find('a', class_='c-finderProductCard_container')
    if not link_tag or 'href' not in link_tag.attrs:
        print(f"Warning: Could not find detail page link for a game (card index {index}). Skipping.")
        return [game_title, release_date_formatted, user_score, num_user_ratings]

    detail_page_path = link_tag['href']
    detail_page_url = BASE_URL + detail_page_path

    print(f"\nProcessing ({index+1}/{total_cards}) [Page {page_number}]: {game_title}")
    print(f"  Detail URL: {detail_page_url}")
    print(f"  Initial Release Date: {release_date_formatted}")

    try:
        time.sleep(REQUEST_DELAY)
        detail_response = requests.get(detail_page_url, headers=HEADERS, timeout=20)
        if detail_response.status_code == 404:
            print(f"  Warning: Game detail page not found (404): {detail_page_url}")
            return [game_title, "N/A (Page 404)", "N/A", "0"]
        detail_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching detail page for {game_title}: {e}")
        return [game_title, "N/A (Fetch Error)", "N/A", "0"]

    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')

    # Extract User Score
    user_score_div = detail_soup.find('div', class_=lambda x: x and 'c-siteReviewScore_user' in x.split())
    if user_score_div:
        score_span = user_score_div.find('span')
        if score_span:
            user_score = score_span.get_text(strip=True)
            print(f"  User Score: {user_score}")

    # Extract Number of User Ratings
    if user_score.lower() == 'tbd':
        num_user_ratings = '0'
        print(f"  Number of User Ratings: {num_user_ratings} (score was tbd)")
    else:
        user_score_container = detail_soup.find('div', attrs={"data-testid": "user-score-info"})
        reviews_total_span = None
        if user_score_container:
            reviews_total_span = user_score_container.find('span', class_='c-productScoreInfo_reviewsTotal')
        if reviews_total_span:
            text_content = reviews_total_span.get_text(strip=True)
            if "based on" in text_content.lower():
                num_user_ratings = extract_number_from_string(text_content)
            elif text_content.lower() == 'tbd' or "no user score" in text_content.lower():
                num_user_ratings = '0'
            else:
                potential_num = extract_number_from_string(text_content)
                num_user_ratings = potential_num if potential_num != "0" else '0'
            print(f"  Number of User Ratings: {num_user_ratings} (From text: '{text_content}')")
        else:
            print(f"  Warning: Could not find number of user ratings for {game_title}")

    # Normalize score and ratings
    user_score_clean = "" if user_score.lower() in ["tbd", "n/a"] else user_score
    num_user_ratings_clean = "" if num_user_ratings in ["0", "N/A"] else num_user_ratings

    # Try to cast them appropriately
    try:
        user_score_clean = float(user_score_clean) if user_score_clean else ""
    except ValueError:
        user_score_clean = ""

    try:
        num_user_ratings_clean = int(num_user_ratings_clean) if num_user_ratings_clean else ""
    except ValueError:
        num_user_ratings_clean = ""

    return [game_title, release_date_formatted, user_score_clean, num_user_ratings_clean]

# --- Main Scraping Logic ---
# Load existing games
existing_games = load_existing_games(CSV_FILENAME)
total_new_games = 0
total_skipped = 0
current_page = START_PAGE

# Loop through pages until no more games are found
while True:
    browse_url = BROWSE_URL_TEMPLATE.format(current_page)
    print(f"\n{'='*60}")
    print(f"Fetching page {current_page}: {browse_url}")
    
    try:
        browse_response = requests.get(browse_url, headers=HEADERS, timeout=20)
        browse_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching browse page: {e}")
        break

    browse_soup = BeautifulSoup(browse_response.text, 'html.parser')
    game_cards = browse_soup.find_all('div', class_='c-finderProductCard-game')

    if not game_cards:
        print(f"No game cards found on page {current_page}. Reached the end of available pages.")
        break
    
    print(f"Found {len(game_cards)} game cards on page {current_page}.")
    
    page_new_games = []
    page_skipped = 0
    
    # Process each game card on the current page
    for index, card in enumerate(game_cards):
        game_data = scrape_game_details(card, index, len(game_cards), existing_games, current_page)
        
        if game_data is None:
            page_skipped += 1
        else:
            page_new_games.append(game_data)
            # Add to existing games set to avoid duplicates within the same run
            existing_games.add((game_data[0], game_data[1]))
    
    # Append new games from this page to CSV
    if page_new_games:
        append_to_csv(CSV_FILENAME, page_new_games)
        print(f"\nPage {current_page} complete: Added {len(page_new_games)} new games, skipped {page_skipped} existing games")
        total_new_games += len(page_new_games)
    else:
        print(f"\nPage {current_page} complete: No new games found, skipped {page_skipped} existing games")
    
    total_skipped += page_skipped
    
    # Move to next page
    current_page += 1
    
    # Add a small delay between pages to be respectful to the server
    time.sleep(REQUEST_DELAY)

# --- Final Summary ---
print(f"\n{'='*60}")
print(f"SCRAPING COMPLETE!")
print(f"Total pages processed: {current_page - START_PAGE}")
print(f"Total new games added: {total_new_games}")
print(f"Total existing games skipped: {total_skipped}")
print(f"Results saved to: {CSV_FILENAME}")