import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import shutil

# URL base della pagina da cui estrarre i dati
base_url = "https://first.art-er.it/bandi?f%5B0%5D=stato%3Anext_open&f%5B1%5D=stato%3Aopen"

# Function to check if the JSON file exists and rename it
def check_and_rename_file(file_path):
    if os.path.exists(file_path):
        # Create the new filename by appending "ieri" before the file extension
        new_file_path = file_path.replace(".json", "ieri.json")
        shutil.move(file_path, new_file_path)
        print(f"File renamed to {new_file_path}")
    else:
        print(f"No existing file to rename at {file_path}")

def get_page_content(url):
    # Effettua la richiesta HTTP
    response = requests.get(url)
    response.raise_for_status()  # Controlla se la richiesta è andata a buon fine
    # Parsing del contenuto HTML con BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

def standardize_date(date_str):
    date_formats = ["%d/%m/%Y", "%Y-%m-%d", "%d.%m.%Y"]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str  # Return original if no format matched


def extract_data(soup):
    bandi = soup.find_all('div', class_='views-row')
    extracted_data = []
    
    for bando in bandi:
        # Map fields to new structure
        scadenza_elem = bando.find('span', class_='status-bando')
        scadenza_raw = scadenza_elem.text.strip().replace("Scadenza: ", "") if scadenza_elem else 'N/A'
        deadline = standardize_date(scadenza_raw) if scadenza_raw != 'N/A' else 'N/A'
        
        titolo_elem = bando.find('h2')
        title = titolo_elem.text.strip() if titolo_elem else 'N/A'
        
        url_elem = bando.find('h2').find('a')['href'] if bando.find('h2').find('a') else 'N/A'
        link = f"https://first.art-er.it{url_elem}" if url_elem else 'N/A'
        
        descrizione_elem = bando.find('div', class_='field--name-body')
        description = descrizione_elem.find('p').text.strip() if descrizione_elem and descrizione_elem.find('p') else 'N/A'
        
        # Collect additional fields into 'custom'
        topics_elem = bando.find('div', class_='field--name-field-topics')
        topics = [item.text.strip() for item in topics_elem.find_all('div', class_='field__item')] if topics_elem else 'N/A'
        
        secondary_group = bando.find('div', class_='group-secondary')
        
        area_classification_elem = secondary_group.find('div', class_='taxonomy-term') if secondary_group else None
        area_classification = area_classification_elem.find('img')['alt'] if area_classification_elem and area_classification_elem.find('img') else 'N/A'
        
        tipologia_scadenza_elem = secondary_group.find('div', class_='field--name-field-tipologia-scadenza') if secondary_group else None
        tipologia_scadenza = tipologia_scadenza_elem.find('div', class_='field__item').text.strip() if tipologia_scadenza_elem else 'N/A'
        
        stanziamento_elem = secondary_group.find('div', class_='field--name-field-stanziamento') if secondary_group else None
        stanziamento = stanziamento_elem.find('div', class_='field__item').text.strip() if stanziamento_elem else 'N/A'
        
        custom = {
            "Topics": ", ".join(topics) if topics != 'N/A' else 'N/A',
            "Area Classification": area_classification,
            "Tipologia Scadenza": tipologia_scadenza,
            "Stanziamento": stanziamento
        }
        
        extracted_data.append({
            "deadline": deadline,
            "title": title,
            "description": description,
            "link": link,
            "custom": custom
        })
    
    return extracted_data

def get_total_pages(soup):
    pager = soup.find('nav', class_='pager')
    if not pager:
        return 1  # Se non c'è paginazione, significa che c'è solo una pagina
    last_page_link = pager.find('li', class_='pager__item pager__item--last')
    if last_page_link:
        last_page_url = last_page_link.find('a')['href']
        last_page_num = int(last_page_url.split('page=')[-1])
        return last_page_num + 1  # Aggiungi 1 perché la paginazione inizia da 0
    return 1

def main():
    # Define the output file path
    output_dir = "../data/"
    output_file = "arter.json"
    output_path = os.path.join(output_dir, output_file)

    # Check and rename the existing file if it exists
    check_and_rename_file(output_path)

    first_page_soup = get_page_content(base_url)
    total_pages = get_total_pages(first_page_soup)
    
    all_data = []
    
    for page_num in range(total_pages):
        print(f"Scraping page {page_num + 1} of {total_pages}...")
        page_url = f"{base_url}&page={page_num}"
        soup = get_page_content(page_url)
        page_data = extract_data(soup)
        all_data.extend(page_data)
    
    # Aggiungi timestamp di scraping
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Salva i dati estratti in un file JSON con timestamp incluso
    output_data = {
        "scraping_timestamp": timestamp,
        "data": all_data
    }

    # Create the directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Save the JSON file in the specified path
    with open(output_path, mode='w', encoding='utf-8') as file:
        json.dump(output_data, file, ensure_ascii=False, indent=4)
    print(f"\nTotal items retrieved: {len(all_data)}")
    print(f"Dati salvati in {output_path}")
    print("=" * 40)

if __name__ == "__main__":
    main()
