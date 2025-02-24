import os
import requests
from bs4 import BeautifulSoup

# URL del sito web
url = "https://aied2024.cesar.school/organization"

# Cartella per salvare le immagini
output_folder = "images"
os.makedirs(output_folder, exist_ok=True)

# Funzione per scaricare l'immagine
def download_image(img_url, save_path):
    response = requests.get(img_url)
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response.content)

# Scarica il contenuto della pagina
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# Identifica le card
cards = soup.find_all("div", class_="hJDwNd-AhqUyc-ibL1re")  # Aggiusta la classe se necessario

# Itera su ogni card
for card in cards:
    # Estrai il nome della persona
    name_tag = card.find("h2")
    name = name_tag.text.strip() if name_tag else "unknown"

    # Estrai organizzazione e paese
    org_country_tag = card.find("p")
    org_country = org_country_tag.text.strip() if org_country_tag else "unknown"

    # Estrai l'URL dell'immagine
    img_tag = card.find("img")
    img_url = img_tag["src"] if img_tag else None

    if img_url:
        # Genera il nome del file per l'immagine
        img_name = f"{name.replace(' ', '_')}_{org_country.replace(', ', '_').replace(' ', '_')}.jpg"
        save_path = os.path.join(output_folder, img_name)

        # Scarica l'immagine
        download_image(img_url, save_path)
        print(f"Immagine salvata: {save_path}")

    # Stampa i dettagli
    print(f"Nome: {name}, Organizzazione e Paese: {org_country}")
