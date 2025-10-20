import requests
import json
from datetime import datetime
import os
import shutil
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import dateparser
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Function to check if the JSON file exists and rename it
def check_and_rename_file(file_path):
    print("Step 1: Checking and renaming existing file...")
    if os.path.exists(file_path):
        new_file_path = file_path.replace(".json", "ieri.json")
        if os.path.exists(new_file_path):
            os.remove(new_file_path)
            print(f"Removed existing 'ieri' file: {new_file_path}")
        shutil.move(file_path, new_file_path)
        print(f"File renamed to {new_file_path}")
    else:
        print(f"No existing file to rename at {file_path}")
    print("Step 1: Completed.\n")

def get_session_with_retries():
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def standardize_date(date_str):
    if not date_str or date_str == 'N/A':
        return 'N/A'
    # Handle Italian month names
    date_str = date_str.lower()
    italian_months = {
        'gennaio': 'january', 'febbraio': 'february', 'marzo': 'march', 'aprile': 'april',
        'maggio': 'may', 'giugno': 'june', 'luglio': 'july', 'agosto': 'august',
        'settembre': 'september', 'ottobre': 'october', 'novembre': 'november', 'dicembre': 'december'
    }
    for it_month, en_month in italian_months.items():
        date_str = date_str.replace(it_month, en_month)

    date_formats = [
        "%d %B %Y", "%d %b %Y"
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # If specific formats fail, try dateparser as a fallback
    try:
        dt = dateparser.parse(date_str)
        if dt:
            return dt.strftime("%Y-%m-%d")
    except:
        pass

    return date_str # Return original if all parsing fails

def get_sitemap_urls(sitemap_url):
    print("Step 2: Fetching sitemap...")
    session = get_session_with_retries()
    try:
        time.sleep(random.uniform(0.5, 2))
        response = session.get(sitemap_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')
        urls = [loc.text for loc in soup.find_all('loc')]
        print(f"Found {len(urls)} URLs in the sitemap.")
        print("Step 2: Completed.\n")
        return urls
    except requests.RequestException as e:
        print(f"Error fetching sitemap: {e}")
        return []

def get_call_urls_from_page(page_url):
    session = get_session_with_retries()
    try:
        time.sleep(random.uniform(0.5, 2))
        response = session.get(page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        call_links = soup.select('a[href*="/bandi/"]')
        urls = list(set([link['href'] for link in call_links if link['href'].count('/') > 2 and 'pagina' not in link['href'] and 'settore' not in link['href'] and 'tipo' not in link['href'] and 'regioni' not in link['href']]))
        return ["https://www.obiettivoeuropa.com" + url for url in urls]
    except requests.RequestException as e:
        print(f"Error fetching page {page_url}: {e}")
        return []

def get_call_details(call_url):
    session = get_session_with_retries()
    try:
        time.sleep(random.uniform(0.5, 2))
        response = session.get(call_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title = soup.find('h1').text.strip()
        
        # Find deadline
        deadline = 'N/A'
        deadline_tag = soup.find('div', string=re.compile("Scadenza:"))
        if deadline_tag:
            deadline_text = deadline_tag.text.strip()
            deadline = deadline_text.replace("Scadenza:", "").strip()

        # Find description
        description = 'N/A'
        description_tag = soup.find('h2', string='Finalità')
        if description_tag:
            description_p = description_tag.find_next('p')
            if description_p:
                description = description_p.text.strip()

        # Find budget
        budget = 'N/A'
        budget_tag = soup.find('div', string='Dotazione Complessiva')
        if budget_tag:
            budget_div = budget_tag.find_next_sibling('div')
            if budget_div:
                budget = budget_div.text.strip()

        topics = [a.text for a in soup.select('a[href*="sectors"]')]
        
        custom = {
            "Topics": ", ".join(topics),
            "Stanziamento": budget
        }

        return {
            "deadline": standardize_date(deadline),
            "title": title,
            "description": description,
            "link": call_url,
            "custom": custom
        }
    except Exception as e:
        print(f"Error scraping call details from {call_url}: {e}")
        return None

def main():
    print("Starting the scraper for Obiettivo Europa...")
    print("=" * 40)

    output_dir = "../data/"
    output_file = "obiettivoeuropa.json"
    output_path = os.path.join(output_dir, output_file)

    check_and_rename_file(output_path)

    sitemap_url = "https://www.obiettivoeuropa.com/sitemap-call_list_open.xml"
    page_urls = get_sitemap_urls(sitemap_url)
    
    all_call_urls = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(get_call_urls_from_page, page_url): page_url for page_url in page_urls}
        for future in as_completed(future_to_url):
            all_call_urls.extend(future.result())
    
    all_call_urls = list(set(all_call_urls))
    print(f"Found {len(all_call_urls)} unique call URLs.")

    all_data = []
    printed_items = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(get_call_details, call_url): call_url for call_url in all_call_urls}
        for i, future in enumerate(as_completed(future_to_url)):
            details = future.result()
            if details:
                all_data.append(details)
                if printed_items < 2:
                    print(json.dumps(details, indent=4, ensure_ascii=False))
                    printed_items += 1
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(all_call_urls)} call URLs...")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    output_data = {
        "scraping_timestamp": timestamp,
        "data": all_data
    }

    print("Step 4: Saving data to JSON file...")
    os.makedirs(output_dir, exist_ok=True)

    with open(output_path, mode='w', encoding='utf-8') as file:
        json.dump(output_data, file, ensure_ascii=False, indent=4)
    
    print(f"Step 4: Completed. Data saved to {output_path}")
    print("=" * 40)
    print(f"\nTotal items retrieved and saved: {len(all_data)}")
    print("Scraping finished successfully!")
    print("=" * 40)


if __name__ == "__main__":
    main()