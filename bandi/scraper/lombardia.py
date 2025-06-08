import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import shutil

# URL dell'endpoint per la ricerca
url = "https://www.bandi.regione.lombardia.it/servizi/servizio/bandi/ricerca"

# Headers per la richiesta POST
headers = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9,it;q=0.8,fr;q=0.7",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Host": "www.bandi.regione.lombardia.it",
    "Origin": "https://www.bandi.regione.lombardia.it",
    "Referer": "https://www.bandi.regione.lombardia.it/servizi/servizio/bandi",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

# Payload per la richiesta POST
payload = {
    "titolo": "",
    "ricercaAvanzata": "true",
    "pageNum": 0,
    "maxPageNum": 0,
    "targetStr": "",
    "descrizione": "",
    "partitaIva": "",
    "stato[0]": "APERTO",
    "stato[1]": "IN APERTURA"
}

# Funzione per standardizzare le date
def standardize_date(date_str):
    date_formats = ["%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y"]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str  # Return original if no format matched

# Funzione per estrarre i dati da una pagina specifica
def extract_data_from_page(payload):
    # Effettua la richiesta POST
    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()  # Assicurati che la richiesta sia andata a buon fine

    # Parsa il contenuto HTML della pagina
    soup = BeautifulSoup(response.content, 'html.parser')

    # Trova il div con la classe "results-block"
    results_block = soup.find('div', class_='results-block')

    # Trova tutti i div con la classe "col-lg-6" all'interno di "results-block"
    items = results_block.find_all('div', class_='col-lg-6') if results_block else []

    # Lista per memorizzare i dati estratti
    data = []

    # Itera su ciascun elemento e estrai le informazioni desiderate
    for item in items:
        # Trova il titolo
        img_tag = item.find('img')
        title = img_tag['alt'] if img_tag else "N/A"

        # Trova il codice
        code_tag = item.find('strong', class_='code')
        code = code_tag.get_text(strip=True) if code_tag else "N/A"

        # Trova l'URL
        link_tag = item.find('a', class_='text-decoration-none')
        link = "https://www.bandi.regione.lombardia.it" + link_tag['href'] if link_tag else "N/A"

        # Trova il testo descrittivo
        description_tag = item.find('p', class_='card-text')
        if description_tag:
            # Funzione di filtro personalizzata per trovare il tag <svg> con l'attributo data-content
            def has_data_content(tag):
                return tag.name == 'svg' and 'data-content' in tag.attrs

            text_tag = description_tag.find(has_data_content)
            if text_tag:
                text = text_tag['data-content']
            else:
                text = "N/A"
        else:
            text = "N/A"

        # Trova la data di scadenza
        date_tag = item.find('input', class_='checkCloseDate')
        date_value = date_tag['value'] if date_tag else "N/A"
        standardized_date = standardize_date(date_value) if date_value != "N/A" else "N/A"

        # Aggiungi i dati estratti alla lista
        data.append({
            "deadline": standardized_date,
            "title": title,
            "description": text,
            "link": link,
            "custom": {
                "Topics": "N/A",
                "Area Classification": "N/A",
                "Tipologia Scadenza": "N/A",
                "Stanziamento": "N/A"
            }
        })

    return data

# Funzione per determinare il numero totale di pagine
def get_total_pages():
    # Effettua una richiesta POST per ottenere la prima pagina
    payload['pageNum'] = 1
    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()

    # Parsa il contenuto HTML della pagina
    soup = BeautifulSoup(response.content, 'html.parser')

    # Trova il div con la classe "results-block"
    results_block = soup.find('div', class_='results-block')

    # Trova il div con la classe "pagination-wrapper"
    pagination_wrapper = soup.find('nav', class_='pagination-wrapper')

    # Trova tutti i link di paginazione
    page_links = pagination_wrapper.find_all('a', class_='page-num') if pagination_wrapper else []

    # Determina il numero totale di pagine
    if page_links:
        max_page_num = max(int(link['data-page-num']) for link in page_links)
    else:
        max_page_num = 1

    return max_page_num

# Funzione per salvare i dati in un file JSON
def save_to_json(data, output_path):
    # Aggiungi timestamp di scraping
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Salva i dati estratti in un file JSON con timestamp incluso
    output_data = {
        "scraping_timestamp": timestamp,
        "data": data
    }

    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save the JSON file in the specified path
    with open(output_path, mode='w', encoding='utf-8') as file:
        json.dump(output_data, file, ensure_ascii=False, indent=4)

    print(f"Dati salvati in {output_path}")

# Funzione per rinominare il file esistente
def check_and_rename_file(file_path):
    if os.path.exists(file_path):
        # Create the new filename by appending "ieri" before the file extension
        new_file_path = file_path.replace(".json", "ieri.json")
        shutil.move(file_path, new_file_path)
        print(f"File renamed to {new_file_path}")
    else:
        print(f"No existing file to rename at {file_path}")

# Funzione principale
def main():
    # Define the output file path
    output_dir = "../data/"
    output_file = "regione_lombardia.json"
    output_path = os.path.join(output_dir, output_file)

    # Check and rename the existing file if it exists
    check_and_rename_file(output_path)

    all_data = []

    # Determina il numero totale di pagine
    total_pages = get_total_pages()

    # Itera attraverso tutte le pagine
    for page in range(1, total_pages + 1):
        payload['pageNum'] = page  # Aggiorna il numero della pagina
        print(f"Estrazione dati dalla pagina {page}...")
        data = extract_data_from_page(payload)
        all_data.extend(data)

    # Salva i dati estratti in un file JSON
    save_to_json(all_data, output_path)

    print(f"Total items retrieved: {len(all_data)}")

if __name__ == "__main__":
    main()
