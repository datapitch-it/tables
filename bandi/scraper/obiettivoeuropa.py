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
import hashlib

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('obiettivoeuropa_optimized.log', maxBytes=5*1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Pool di User-Agent realistici
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
]

# Accept-Language variants
ACCEPT_LANGUAGES = [
    'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    'it-IT,it;q=0.9,en;q=0.8',
    'it,en-US;q=0.9,en;q=0.8',
    'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
]

class AdaptiveRateLimiter:
    """Rate limiter adattivo basato sui tempi di risposta"""
    def __init__(self, base_delay_min=0.5, base_delay_max=1.5):
        self.base_delay_min = base_delay_min
        self.base_delay_max = base_delay_max
        self.current_delay_min = base_delay_min
        self.current_delay_max = base_delay_max
        self.consecutive_errors = 0
        self.consecutive_successes = 0

    def wait(self):
        """Attendi con delay adattivo"""
        delay = random.uniform(self.current_delay_min, self.current_delay_max)
        time.sleep(delay)
        return delay

    def record_success(self, response_time):
        """Registra richiesta riuscita"""
        self.consecutive_errors = 0
        self.consecutive_successes += 1

        # Se 10 successi consecutivi e server veloce, riduci delay
        if self.consecutive_successes >= 10 and response_time < 0.5:
            self.current_delay_min = max(0.3, self.current_delay_min * 0.9)
            self.current_delay_max = max(0.8, self.current_delay_max * 0.9)
            logger.info(f"Rate limiter: velocità aumentata → {self.current_delay_min:.2f}-{self.current_delay_max:.2f}s")
            self.consecutive_successes = 0

    def record_error(self, status_code=None):
        """Registra errore"""
        self.consecutive_successes = 0
        self.consecutive_errors += 1

        # Exponential backoff
        multiplier = min(2 ** self.consecutive_errors, 8)
        self.current_delay_min = min(self.base_delay_min * multiplier, 10)
        self.current_delay_max = min(self.base_delay_max * multiplier, 20)

        logger.warning(f"Rate limiter: errore rilevato (status={status_code}), rallentamento → {self.current_delay_min:.2f}-{self.current_delay_max:.2f}s")

    def reset(self):
        """Reset a valori base"""
        self.current_delay_min = self.base_delay_min
        self.current_delay_max = self.base_delay_max
        self.consecutive_errors = 0
        self.consecutive_successes = 0

# Rate limiters globali
list_rate_limiter = AdaptiveRateLimiter(base_delay_min=0.5, base_delay_max=1.5)
detail_rate_limiter = AdaptiveRateLimiter(base_delay_min=1.0, base_delay_max=2.5)

def setup_logging():
    """Configura il logging"""
    logger.info("="*50)
    logger.info("Scraper Obiettivo Europa - Versione Ottimizzata")
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

def get_random_headers():
    """Genera headers casuali ma realistici"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': random.choice(ACCEPT_LANGUAGES),
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.obiettivoeuropa.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Cache-Control': 'max-age=0',
    }

def get_session_with_retries():
    """Crea una sessione con retry e headers randomizzati"""
    session = requests.Session()

    # Headers iniziali (verranno sovrascritti ad ogni richiesta)
    session.headers.update(get_random_headers())

    # Configura retry
    retries = Retry(
        total=3,  # Ridotto da 5 a 3
        backoff_factor=1,  # Ridotto da 2 a 1
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=20)
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
        logger.debug(f"Impossibile standardizzare la data: {date_str}")

    return date_str

def load_seen_links_cache(cache_file):
    """Carica la cache dei link già visti"""
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
                logger.info(f"Cache caricata: {len(cache.get('links', []))} link già visti")
                return set(cache.get('links', []))
        except Exception as e:
            logger.warning(f"Errore caricamento cache: {e}")
    return set()

def save_seen_links_cache(cache_file, links):
    """Salva la cache dei link visti"""
    try:
        with open(cache_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'links': list(links)
            }, f)
        logger.info(f"Cache salvata: {len(links)} link")
    except Exception as e:
        logger.warning(f"Errore salvataggio cache: {e}")

def scrape_directly_from_list_pages(max_pages=None, use_cache=True):
    """Scraping diretto dalle pagine /bandi/aperti/pagina/X/ con ottimizzazioni

    Args:
        max_pages: Numero massimo di pagine da scrapare (None = tutte)
        use_cache: Se True, usa la cache per identificare link già visti
    """
    logger.info("Step 2: Scraping diretto dalle pagine di lista (OTTIMIZZATO)...")
    if max_pages:
        logger.info(f"MODALITÀ TEST: Limite impostato a {max_pages} pagine")

    # Carica cache
    cache_file = "../data/.obiettivoeuropa_cache.json"
    seen_links = set()
    if use_cache:
        seen_links = load_seen_links_cache(cache_file)

    base_url = "https://www.obiettivoeuropa.com/bandi/aperti/pagina"
    session = get_session_with_retries()

    all_call_urls = set()
    new_call_urls = set()
    page = 1
    max_empty_pages = 5
    empty_count = 0

    while empty_count < max_empty_pages:
        if max_pages and page > max_pages:
            logger.info(f"Raggiunto limite test di {max_pages} pagine, stop")
            break

        page_url = f"{base_url}/{page}/"

        # Adaptive rate limiting
        delay = list_rate_limiter.wait()

        try:
            # Headers casuali per ogni richiesta
            session.headers.update(get_random_headers())

            start_time = time.time()
            response = session.get(page_url, timeout=30)
            response_time = time.time() - start_time
            response.raise_for_status()

            # Registra successo
            list_rate_limiter.record_success(response_time)

            soup = BeautifulSoup(response.content, 'html.parser')
            call_links = soup.select('a.calls-list-item')

            if not call_links or len(call_links) == 0:
                empty_count += 1
                logger.warning(f"Pagina {page} vuota ({empty_count}/{max_empty_pages})")
                page += 1
                continue

            empty_count = 0

            page_new = 0
            for link in call_links:
                href = link.get('href', '')
                if href.startswith('/'):
                    href = 'https://www.obiettivoeuropa.com' + href

                if '/bandi/' in href and not any(x in href for x in ['pagina', 'settore', 'tipo', 'regioni']):
                    all_call_urls.add(href)
                    if href not in seen_links:
                        new_call_urls.add(href)
                        page_new += 1

            logger.info(f"Pag {page}: {len(call_links)} bandi ({page_new} nuovi) | Totali: {len(all_call_urls)} ({len(new_call_urls)} nuovi) | Delay: {delay:.2f}s | RT: {response_time:.2f}s")
            page += 1

            if page > 150:
                logger.warning("Raggiunto limite di 150 pagine, stop")
                break

        except requests.exceptions.HTTPError as e:
            list_rate_limiter.record_error(e.response.status_code if hasattr(e, 'response') else None)
            logger.error(f"Errore HTTP nella pagina {page}: {e}")
            empty_count += 1
            page += 1
        except Exception as e:
            list_rate_limiter.record_error()
            logger.error(f"Errore nella pagina {page}: {e}")
            empty_count += 1
            page += 1

    logger.info(f"Totale URL: {len(all_call_urls)} | Nuovi: {len(new_call_urls)} | Da cache: {len(all_call_urls) - len(new_call_urls)}")

    # Salva cache aggiornata
    if use_cache:
        save_seen_links_cache(cache_file, all_call_urls)

    # Restituisci solo i nuovi se use_cache è attivo
    return list(new_call_urls) if use_cache and seen_links else list(all_call_urls)

def get_call_details(call_url):
    """Ottiene i dettagli di un singolo bando con ottimizzazioni anti-detection"""
    session = get_session_with_retries()

    try:
        # Adaptive rate limiting
        delay = detail_rate_limiter.wait()

        # Headers casuali
        session.headers.update(get_random_headers())

        start_time = time.time()
        response = session.get(call_url, timeout=30)
        response_time = time.time() - start_time
        response.raise_for_status()

        # Registra successo
        detail_rate_limiter.record_success(response_time)

        soup = BeautifulSoup(response.content, 'html.parser')

        # Estrazione dati (identica alla versione originale)
        title = 'N/A'
        h1_tag = soup.find('h1')
        if h1_tag:
            title = h1_tag.text.strip()

        deadline = 'N/A'
        deadline_tag = soup.find('div', string=re.compile("Scadenza:", re.IGNORECASE))
        if deadline_tag:
            deadline_text = deadline_tag.text.strip()
            deadline = deadline_text.replace("Scadenza:", "").strip()

        description = 'N/A'
        description_tag = soup.find('h2', string=re.compile('Finalità', re.IGNORECASE))
        if description_tag:
            description_p = description_tag.find_next('p')
            if description_p:
                description = description_p.text.strip()

        budget = 'N/A'
        budget_tag = soup.find('div', string=re.compile('Dotazione', re.IGNORECASE))
        if budget_tag:
            budget_div = budget_tag.find_next_sibling('div')
            if budget_div:
                budget = budget_div.text.strip()

        topics = []
        topic_links = soup.select('a[href*="sectors"]')
        if topic_links:
            topics = [a.text.strip() for a in topic_links]

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

    except requests.exceptions.HTTPError as e:
        detail_rate_limiter.record_error(e.response.status_code if hasattr(e, 'response') else None)
        logger.error(f"Errore HTTP per {call_url}: {e}")
        return None
    except Exception as e:
        detail_rate_limiter.record_error()
        logger.error(f"Errore per {call_url}: {e}")
        return None

def main(test_mode=False, test_pages=5, use_cache=True):
    """Funzione principale dello scraper ottimizzato

    Args:
        test_mode: Se True, attiva modalità test
        test_pages: Numero di pagine in modalità test
        use_cache: Se True, usa la cache per evitare re-scraping
    """
    setup_logging()
    logger.info("Inizio scraping Obiettivo Europa (VERSIONE OTTIMIZZATA)")

    if test_mode:
        logger.info("="*50)
        logger.info(f"⚠️  MODALITÀ TEST - {test_pages} pagine")
        logger.info("="*50)

    if use_cache:
        logger.info("✅ Cache attiva: verrà scrapato solo contenuto nuovo")
    else:
        logger.info("⚠️  Cache disattivata: scraping completo")

    output_dir = "../data/"
    output_file = "obiettivoeuropa.json"
    output_path = os.path.join(output_dir, output_file)

    try:
        # Step 1: Gestione file
        check_and_rename_file(output_path)

        # Step 2: Recupero URL bandi
        max_pages = test_pages if test_mode else None
        all_call_urls = scrape_directly_from_list_pages(max_pages=max_pages, use_cache=use_cache)

        if not all_call_urls:
            logger.warning("Nessun URL nuovo da scrapare")
            # Se non ci sono nuovi bandi, copia il file ieri a oggi
            ieri_path = output_path.replace(".json", "ieri.json")
            if os.path.exists(ieri_path):
                shutil.copy(ieri_path, output_path)
                logger.info("Nessun nuovo bando, file copiato da 'ieri'")
            return

        logger.info(f"Totale URL da scrapare: {len(all_call_urls)}")

        # Step 3: Scraping dettagli (con più workers se pochi bandi)
        logger.info("Step 3: Scraping dettagli bandi...")

        # Adatta workers al carico
        workers = min(8, max(3, len(all_call_urls) // 50))
        logger.info(f"Workers paralleli: {workers}")

        all_data = []
        printed_items = 0

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_url = {executor.submit(get_call_details, call_url): call_url for call_url in all_call_urls}
            for i, future in enumerate(as_completed(future_to_url)):
                try:
                    details = future.result()
                    if details:
                        all_data.append(details)
                        if printed_items < 2:
                            logger.info(f"Esempio:\n{json.dumps(details, indent=2, ensure_ascii=False)}")
                            printed_items += 1
                    if (i + 1) % 50 == 0:
                        elapsed = time.time() - start_time
                        rate = (i + 1) / elapsed
                        remaining = (len(all_call_urls) - (i + 1)) / rate if rate > 0 else 0
                        logger.info(f"Processati {i + 1}/{len(all_call_urls)} | {rate:.1f} bandi/s | ETA: {remaining/60:.1f}min")
                except Exception as e:
                    logger.error(f"Errore nel thread: {str(e)}")

        elapsed_total = time.time() - start_time

        # Step 4: Merge con dati vecchi se usiamo cache
        if use_cache:
            ieri_path = output_path.replace(".json", "ieri.json")
            if os.path.exists(ieri_path):
                try:
                    with open(ieri_path, 'r') as f:
                        old_data = json.load(f)
                        old_items = {item['link']: item for item in old_data.get('data', [])}

                    # Aggiungi nuovi items
                    new_links = {item['link'] for item in all_data}
                    for link, item in old_items.items():
                        if link not in new_links:
                            all_data.append(item)

                    logger.info(f"Merge: {len(all_data) - len(new_links)} bandi vecchi + {len(new_links)} nuovi = {len(all_data)} totali")
                except Exception as e:
                    logger.warning(f"Errore merge con dati vecchi: {e}")

        # Step 5: Salvataggio
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
        logger.info(f"✅ Scraping completato in {elapsed_total/60:.1f} minuti")
        logger.info(f"📁 Dati salvati in: {output_path}")
        logger.info(f"📊 Totale bandi: {len(all_data)}")
        logger.info(f"⚡ Velocità media: {len(all_call_urls)/elapsed_total:.2f} bandi/s")
        logger.info("="*50)

    except Exception as e:
        logger.critical(f"Errore critico: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    import sys

    test_mode = False
    test_pages = 5
    use_cache = True

    for arg in sys.argv[1:]:
        if arg.startswith('--test'):
            test_mode = True
            if '=' in arg:
                try:
                    test_pages = int(arg.split('=')[1])
                except ValueError:
                    logger.warning(f"Valore non valido per --test, uso default: {test_pages}")
        elif arg == '--no-cache':
            use_cache = False

    main(test_mode=test_mode, test_pages=test_pages, use_cache=use_cache)
