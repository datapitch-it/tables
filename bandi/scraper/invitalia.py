import requests
from bs4 import BeautifulSoup
import logging
import time
import os
import json
import shutil
from datetime import datetime
import dateparser
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

URLS = [
    "https://www.invitalia.it/per-chi-vuole-fare-impresa/incentivi-e-strumenti",
    "https://www.invitalia.it/per-le-imprese/incentivi-e-strumenti"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive'
}

# Sessione con retry
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=3,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Backup file se esiste
def check_and_rename_file(file_path):
    if os.path.exists(file_path):
        new_file_path = file_path.replace(".json", "ieri.json")
        shutil.move(file_path, new_file_path)
        logging.info(f"File rinominato in {new_file_path}")
    else:
        logging.info(f"Nessun file da rinominare in {file_path}")

def parse_date_it(raw_date):
    if not raw_date or raw_date.strip() == "N/A":
        return "N/A"
    dt = dateparser.parse(raw_date, languages=['it'])
    if dt:
        return dt.strftime("%Y-%m-%d")
    return "N/A"

def extract_total_pages(soup):
    page_links = soup.select("ul.pagination li.page-item a.page-link[href*='page=']")
    pages = []
    for link in page_links:
        href = link.get("href")
        if "page=" in href:
            try:
                page_number = int(href.split("page=")[-1])
                pages.append(page_number)
            except ValueError:
                continue
    return max(pages) if pages else 0

def extract_items_from_soup(soup):
    item_containers = soup.find_all('div', class_='card-wrapper pb-0 card-wrapper--incentivi')
    logging.info(f"Trovati {len(item_containers)} item containers.")
    data = []
    for i, container in enumerate(item_containers):
        card = container.find("article", class_="card")
        if not card:
            logging.warning(f"Card non trovata per l'item #{i + 1}")
            continue
        try:
            logging.info(f"Estraggo item #{i + 1}")
            title_element = card.find('h3')
            title = title_element.find('a').text.strip() if title_element and title_element.find('a') else "Titolo non trovato"

            description_element = card.find('p', class_='fw-normal')
            description = description_element.text.strip() if description_element else "Descrizione non trovata"

            link_element = card.find('a', class_='read-more')
            link = link_element['href'] if link_element else "Link non trovato"
            absolute_link = f"https://www.invitalia.it{link}"

            stato_element = card.find('span', class_='text-decoration-none fw-semibold category')
            stato = stato_element.text.strip() if stato_element else "Stato non trovato"

            apertura_span = card.find("span", class_="apertura")
            apertura = apertura_span.find("strong").text.strip() if apertura_span and apertura_span.find("strong") else "N/A"

            chiusura_span = card.find("span", class_="chiusura")
            chiusura = chiusura_span.find("strong").text.strip() if chiusura_span and chiusura_span.find("strong") else "N/A"

            deadline_raw = chiusura if chiusura != "N/A" else apertura
            deadline = parse_date_it(deadline_raw)

            formatted = {
                "deadline": deadline,
                "title": title,
                "description": description,
                "link": absolute_link,
                "custom": {
                    "Topics": "N/A",
                    "Area Classification": "Italia",
                    "Tipologia Scadenza": "Singola",
                    "Stanziamento": "N/A"
                }
            }

            data.append(formatted)
        except Exception as e:
            logging.error(f"Errore durante l'estrazione di un singolo item: {e}", exc_info=True)
    return data

def extract_all_incentivi(base_url):
    all_data = []
    page = 0

    while True:
        url = f"{base_url}?page={page}"
        logging.info(f"Scraping pagina {page}: {url}")
        try:
            response = session.get(url, headers=HEADERS, timeout=60)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            if page == 0:
                max_page = extract_total_pages(soup)
                logging.info(f"Pagine totali trovate: {max_page + 1}")

            items = extract_items_from_soup(soup)
            if not items:
                logging.info("Nessun item trovato, fine scraping.")
                break

            all_data.extend(items)

            if page >= max_page:
                break

            page += 1
            time.sleep(1)

        except Exception as e:
            logging.error(f"Errore nella pagina {page}: {e}", exc_info=True)
            break

    return all_data

def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    result = {
        "scraping_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": data
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    logging.info(f"Dati salvati in {path}")

# Esecuzione principale
output_path = "../data/invitalia.json"
check_and_rename_file(output_path)

all_incentivi = []
for url in URLS:
    result = extract_all_incentivi(url)
    all_incentivi.extend(result)

if all_incentivi:
    save_json(all_incentivi, output_path)
else:
    print("Impossibile recuperare i dati.")
