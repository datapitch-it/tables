import os
import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup

def parse_date(date_string):
    """
    Parses a date string into YYYY-MM-DD format.
    Returns "Invalid Date" if parsing fails.
    """
    for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %B %Y", "%B %d, %Y"]:
        try:
            return datetime.strptime(date_string, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return "Invalid Date"

def fetch_all_opportunities(base_url, headers, max_attempts=50):
    all_opportunities = []
    page = 1

    while True:
        url = f"{base_url}?paged={page}"
        print(f"Fetching page {page}...")

        response = requests.get(url, headers=headers)

        if response.status_code == 404 or page > max_attempts:
            print(f"No more pages or reached max attempts at page {page}.")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        opportunities = scrape_funding_opportunities(soup)

        if not opportunities:
            print(f"No opportunities found on page {page}.")
            break

        print(f"Page {page}: Found {len(opportunities)} items.")
        all_opportunities.extend(opportunities)
        page += 1

    print(f"Finished fetching. Total opportunities: {len(all_opportunities)}.")
    return all_opportunities

def scrape_funding_opportunities(soup):
    opportunities = []
    funding_items = soup.find_all('li', class_='funding')

    for item in funding_items:
        try:
            title = item.find('h4').get_text(strip=True) if item.find('h4') else "No Title"
            organisation = (
                item.find('strong', string="Organisation:").find_next_sibling(string=True).strip()
                if item.find('strong', string="Organisation:") else "No Organisation"
            )
            region = (
                item.find('strong', string="Region:").find_next_sibling(string=True).strip()
                if item.find('strong', string="Region:") else "No Region"
            )
            status = (
                item.find('strong', string="Status:").find_next_sibling(string=True).strip()
                if item.find('strong', string="Status:") else "No Status"
            )
            deadline_raw = (
                item.find('strong', string="Deadline:").find_next_sibling(string=True).strip()
                if item.find('strong', string="Deadline:") else "No Deadline"
            )
            deadline = parse_date(deadline_raw)
            funding_type = (
                item.find('strong', string="Type:").find_next('li').get_text(strip=True)
                if item.find('strong', string="Type:") else "No Type"
            )
            funding_size = (
                item.find('strong', string="Funding Size:").find_next_sibling(string=True).strip()
                if item.find('strong', string="Funding Size:") else "No Funding Size"
            )
            link = item.find('a', href=True)['href'] if item.find('a', href=True) else "No Link"
            
            opportunities.append({
                'deadline': deadline,
                'title': title,
                'description': organisation,  # Placeholder for description
                'link': link,
                'custom': {
                    'Topics': "N/A",  # Placeholder
                    'Area Classification': region,
                    'Tipologia Scadenza': status,
                    'Stanziamento': funding_size
                }
            })
        except AttributeError as e:
            print(f"Warning: Missing or malformed data for an item. Error: {e}")
            continue

    return opportunities

def save_opportunities_to_file(opportunities, folder="../data", filename="journalism.json"):
    # Create the data folder if it doesn't exist
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    old_filepath = os.path.join(folder, "journalismieri.json")

    # Check if the file exists, rename if necessary
    if os.path.exists(filepath):
        os.rename(filepath, old_filepath)
        print(f"Renamed existing file to {old_filepath}.")

    # Add timestamp and save data
    scraping_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_data = {
        "scraping_timestamp": scraping_timestamp,
        "data": opportunities
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
        print(f"Saved data to {filepath}.")

# Configuration
BASE_URL = "https://gfmd.info/fundings/"
HEADERS = {
    "accept": "text/html, */*; q=0.01",
    "accept-language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6,es;q=0.5,de;q=0.4",
    "cookie": "info-cookie-notice=closed",
    "referer": "https://gfmd.info/fundings/",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}

# Run the script
opportunities = fetch_all_opportunities(BASE_URL, HEADERS)
save_opportunities_to_file(opportunities)
