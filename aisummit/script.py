import requests
from bs4 import BeautifulSoup
import json
import time
import csv

# Base URL della pagina web
base_url = "https://app.ai-action-summit.fr/en/recherche-networking.htm?Nb_RechercheIndividu=30&Page_RechercheIndividu={}" 

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

data = []
current_page = 1
max_page = 35

while current_page <= max_page:
    print(f"Scraping page {current_page}...")
    response = requests.get(base_url.format(current_page), headers=headers)
    if response.status_code != 200:
        print(f"Errore nel recupero della pagina {current_page}")
        break
    
    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.find_all("div", class_="tg-search-list-element")

    for card in cards:
        # Estrarre il nome
        name_tag = card.find("h4")
        name = name_tag.text.strip() if name_tag else "N/A"
        
        # Estrarre l'organizzazione
        org_tag = name_tag.find_next("br")
        organization = org_tag.next_sibling.strip() if org_tag and org_tag.next_sibling else "N/A"
        
        # Estrarre l'immagine
        img_tag = card.find("img")
        img_src = f"https:{img_tag['src']}" if img_tag and "src" in img_tag.attrs else "N/A"

        # Aggiungere i dati
        data.append({"name": name, "organization": organization, "image_url": img_src})
    
    # Trova il pulsante "next"
    next_button = soup.find("span", class_="tg-clickable tg-icon tg-small tg-icon-next")
    if not next_button or current_page >= max_page:
        print("Nessuna pagina successiva trovata o limite massimo raggiunto, fine dello scraping.")
        break
    
    # Incrementare il numero della pagina
    current_page += 1
    #time.sleep(1)  # Evita di sovraccaricare il server

# Salvare i dati in un file JSON
with open("scraped_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

# Salvare i dati in un file CSV
csv_file = "scraped_data.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "organization", "image_url"])
    writer.writeheader()
    writer.writerows(data)

print("Dati salvati in scraped_data.json e scraped_data.csv")
