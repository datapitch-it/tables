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
import logging
from logging.handlers import RotatingFileHandler

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('obiettivoeuropa.log', maxBytes=5*1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_logging():
    """Configura il logging con rotazione dei file"""
    logger.info("="*50)
    logger.info("Inizializzazione logging completata")
    logger.info("="*50)

def check_and_rename_file(file_path):
    """Controlla e rinomina il file esistente"""
    logger.info("Step 1: Controllo e rinomina file esistente...")
    try:
        if os.path.exists(file_path):
            new_file_path = file_path.replace(".json", "ieri.json")
            if os.path.exists(new_file_path):
                os.remove(new_file_path)
                logger.info(f"Rimosso file esistente: {new_file_path}")
            shutil.move(file_path, new_file_path)
            logger.info(f"File rinominato in: {new_file_path}")
        else:
            logger.info(f"Nessun file esistente trovato in: {file_path}")
        logger.info("Step 1 completato con successo")
    except Exception as e:
        logger.error(f"Errore in Step 1: {str(e)}")
        raise

def get_session_with_retries():
    """Crea una sessione con retry configurati e user agent"""
    session = requests.Session()

    # Configura user agent
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    session.headers.update({
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.obiettivoeuropa.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })

    # Configura retry
    retries = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session

def standardize_date(date_str):
    """Standardizza le date in formato YYYY-MM-DD"""
    if not date_str or date_str == 'N/A':
        return 'N/A'

    date_str = date_str.lower()
    italian_months = {
        'gennaio': 'january', 'febbraio': 'february', 'marzo': 'march', 'aprile': 'april',
        'maggio': 'may', 'giugno': 'june', 'luglio': 'july', 'agosto': 'august',
        'settembre': 'september', 'ottobre': 'october', 'novembre': 'november', 'dicembre': 'december'
    }

    for it_month, en_month in italian_months.items():
        date_str = date_str.replace(it_month, en_month)

    date_formats = [
        "%d %B %Y", "%d %b %Y", "%d-%m-%Y", "%d/%m/%Y"
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    try:
        dt = dateparser.parse(date_str)
        if dt:
            return dt.strftime("%Y-%m-%d")
    except Exception as e:
        logger.warning(f"Impossibile standardizzare la data: {date_str}. Errore: {str(e)}")

    return date_str

def scrape_directly_from_list_pages(max_pages=None):
    """Scraping diretto dalle pagine /bandi/aperti/pagina/X/ con early stop dinamico

    Args:
        max_pages: Numero massimo di pagine da scrapare (None = tutte)
    """
    logger.info("Step 2: Scraping diretto dalle pagine di lista...")
    if max_pages:
        logger.info(f"MODALITÀ TEST: Limite impostato a {max_pages} pagine")

    base_url = "https://www.obiettivoeuropa.com/bandi/aperti/pagina"
    session = get_session_with_retries()

    all_call_urls = set()
    page = 1
    max_empty_pages = 5  # Fermati dopo 5 pagine vuote consecutive
    empty_count = 0

    while empty_count < max_empty_pages:
        # Check limite pagine per test
        if max_pages and page > max_pages:
            logger.info(f"Raggiunto limite test di {max_pages} pagine, stop")
            break
        page_url = f"{base_url}/{page}/"
        logger.info(f"Scraping pagina {page}: {page_url}")

        time.sleep(random.uniform(1, 3))

        try:
            response = session.get(page_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Trova tutti i link ai bandi usando la classe calls-list-item
            call_links = soup.select('a.calls-list-item')

            if not call_links or len(call_links) == 0:
                empty_count += 1
                logger.warning(f"Pagina {page} vuota ({empty_count}/{max_empty_pages})")
                page += 1
                continue

            empty_count = 0  # Reset counter se trovo bandi

            for link in call_links:
                href = link.get('href', '')
                if href.startswith('/'):
                    href = 'https://www.obiettivoeuropa.com' + href
                # Filtra solo link ai bandi, escludendo pagine di navigazione
                if '/bandi/' in href and not any(x in href for x in ['pagina', 'settore', 'tipo', 'regioni']):
                    all_call_urls.add(href)

            logger.info(f"Trovati {len(call_links)} bandi nella pagina {page} (totale unici: {len(all_call_urls)})")
            page += 1

            # Safety check: max 150 pagine per evitare loop infiniti
            if page > 150:
                logger.warning("Raggiunto limite di 150 pagine, stop")
                break

        except Exception as e:
            logger.error(f"Errore nella pagina {page}: {e}")
            empty_count += 1
            page += 1

    logger.info(f"Totale URL bandi trovati: {len(all_call_urls)}")
    return list(all_call_urls)

def get_call_details(call_url):
    """Ottiene i dettagli di un singolo bando con gestione degli errori"""
    session = get_session_with_retries()
    try:
        # Ritardo casuale tra 2 e 4 secondi (ridotto per efficienza)
        delay = random.uniform(2, 4)
        time.sleep(delay)

        response = session.get(call_url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Estrazione titolo con fallback
        title = 'N/A'
        h1_tag = soup.find('h1')
        if h1_tag:
            title = h1_tag.text.strip()
        else:
            logger.warning(f"Titolo non trovato in {call_url}")

        # Estrazione scadenza con fallback
        deadline = 'N/A'
        deadline_tag = soup.find('div', string=re.compile("Scadenza:", re.IGNORECASE))
        if deadline_tag:
            deadline_text = deadline_tag.text.strip()
            deadline = deadline_text.replace("Scadenza:", "").strip()
        else:
            logger.warning(f"Scadenza non trovata in {call_url}")

        # Estrazione descrizione con fallback
        description = 'N/A'
        description_tag = soup.find('h2', string=re.compile('Finalità', re.IGNORECASE))
        if description_tag:
            description_p = description_tag.find_next('p')
            if description_p:
                description = description_p.text.strip()
        else:
            logger.warning(f"Descrizione non trovata in {call_url}")

        # Estrazione budget con fallback
        budget = 'N/A'
        budget_tag = soup.find('div', string=re.compile('Dotazione', re.IGNORECASE))
        if budget_tag:
            budget_div = budget_tag.find_next_sibling('div')
            if budget_div:
                budget = budget_div.text.strip()
        else:
            logger.debug(f"Budget non trovato in {call_url}")

        # Estrazione tematiche con fallback
        topics = []
        topic_links = soup.select('a[href*="sectors"]')
        if topic_links:
            topics = [a.text.strip() for a in topic_links]
        else:
            logger.debug(f"Tematiche non trovate in {call_url}")

        return {
            "deadline": standardize_date(deadline),
            "title": title,
            "description": description,
            "link": call_url,
            "custom": {
                "Topics": ", ".join(topics) if topics else "N/A",
                "Stanziamento": budget
            }
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Errore nella richiesta per {call_url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Errore imprevisto in {call_url}: {str(e)}", exc_info=True)
        return None

def main(test_mode=False, test_pages=5):
    """Funzione principale dello scraper con gestione degli errori

    Args:
        test_mode: Se True, attiva modalità test con numero limitato di pagine
        test_pages: Numero di pagine da scrapare in modalità test (default: 5)
    """
    setup_logging()
    logger.info("Inizio scraping Obiettivo Europa")

    if test_mode:
        logger.info("="*50)
        logger.info(f"⚠️  MODALITÀ TEST ATTIVA - Solo {test_pages} pagine")
        logger.info("="*50)

    output_dir = "../data/"
    output_file = "obiettivoeuropa.json"
    output_path = os.path.join(output_dir, output_file)

    try:
        # Step 1: Gestione file
        check_and_rename_file(output_path)

        # Step 2: Recupero URL bandi direttamente dalle pagine di lista
        max_pages = test_pages if test_mode else None
        all_call_urls = scrape_directly_from_list_pages(max_pages=max_pages)

        if not all_call_urls:
            logger.warning("Nessun URL bando trovato")
            return

        logger.info(f"Totale URL bandi da scrapare: {len(all_call_urls)}")

        # Step 3: Scraping dettagli bandi
        logger.info("Step 3: Scraping dettagli bandi...")
        all_data = []
        printed_items = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(get_call_details, call_url): call_url for call_url in all_call_urls}
            for i, future in enumerate(as_completed(future_to_url)):
                try:
                    details = future.result()
                    if details:
                        all_data.append(details)
                        if printed_items < 2:
                            logger.info(f"Esempio di dati:\n{json.dumps(details, indent=4, ensure_ascii=False)}")
                            printed_items += 1
                    if (i + 1) % 50 == 0:
                        logger.info(f"Processati {i + 1}/{len(all_call_urls)} bandi...")
                except Exception as e:
                    logger.error(f"Errore nel thread: {str(e)}", exc_info=True)

        # Step 4: Salvataggio dati
        logger.info("Step 4: Salvataggio dati...")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_data = {
            "scraping_timestamp": timestamp,
            "data": all_data
        }

        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, mode='w', encoding='utf-8') as file:
            json.dump(output_data, file, ensure_ascii=False, indent=4)

        logger.info("="*50)
        logger.info(f"Dati salvati in: {output_path}")
        logger.info(f"Totale bandi recuperati: {len(all_data)}")
        logger.info("Scraping completato con successo")
        logger.info("="*50)

    except Exception as e:
        logger.critical(f"Errore critico nello script: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    import sys

    # Controlla se passato argomento --test o --test=N
    test_mode = False
    test_pages = 5

    for arg in sys.argv[1:]:
        if arg.startswith('--test'):
            test_mode = True
            if '=' in arg:
                try:
                    test_pages = int(arg.split('=')[1])
                except ValueError:
                    logger.warning(f"Valore non valido per --test, uso default: {test_pages}")

    main(test_mode=test_mode, test_pages=test_pages)
