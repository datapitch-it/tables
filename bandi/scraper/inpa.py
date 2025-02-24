import requests
import os
import json
from datetime import datetime

# API endpoint and payload
url = "https://portale.inpa.gov.it/concorsi-smart/api/concorso-public-area/search-better"
payload = {
    "text": "",
    "categoriaId": "ced3de00dd504237a8ae",
    "regioneId": None,
    "status": ["OPEN"],
    "settoreId": None,
    "dateFrom": None,
    "dateTo": None,
    "livelliAnzianitaIds": None,
    "provinciaCodice": None,
    "salaryMax": None,
    "salaryMin": None,
    "tipoImpiegoId": None
}

# Output file paths
output_dir = "../data"
output_file = "inpa.json"
backup_file = "inpaieri.json"
output_path = os.path.join(output_dir, output_file)
backup_path = os.path.join(output_dir, backup_file)

def backup_existing_file(output_path, backup_path):
    print(f"Checking if {output_path} exists for backup...")
    if os.path.exists(output_path):
        os.rename(output_path, backup_path)
        print(f"File renamed to {backup_path}")
    else:
        print(f"No existing file to rename at {output_path}")

def format_date(date_str):
    """Formats an ISO date string to YYYY-MM-DD format."""
    if date_str is None:
        return "N/A"
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except (ValueError, TypeError) as e:
        print(f"Date formatting error: {e}")
        return "N/A"

def format_data(items):
    formatted_items = []
    for item in items:
        # Map fields to new structure
        item_id = item.get("id", "")
        formatted_item = {
            "deadline": format_date(item.get("dataScadenza")),
            "title": item.get("titolo", "N/A"),
            "description": item.get("descrizione", "N/A"),
            "link": f"https://www.inpa.gov.it/bandi-e-avvisi/dettaglio-bando-avviso/?concorso_id={item_id}" if item_id else "N/A",
            "custom": {
                "Topics": item.get("topics", "N/A"),
                "Area Classification": item.get("areaClassification", "N/A"),
                "Tipologia Scadenza": item.get("tipologiaScadenza", "N/A"),
                "Stanziamento": item.get("stanziamento", "N/A")
            }
        }
        
        formatted_items.append(formatted_item)
    return formatted_items

def save_data_to_json(data, output_path):
    # Structure data in the desired JSON format
    formatted_data = {
        "scraping_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": data
    }

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        print(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir)
        
    # Write data to JSON file
    print(f"Saving data to JSON at {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=4)
    print(f"Data saved to {output_path}")

# Execute backup before starting the data fetching
backup_existing_file(output_path, backup_path)

# Initial variables
page = 0
size = 4  # Adjust page size as needed
all_data = []

# Fetch the first page to determine total pages
print("Sending initial request to fetch first page and total page count...")
response = requests.post(
    url,
    json=payload,
    params={"page": page, "size": size}
)

if response.status_code == 200:
    # Parse JSON response
    print("Parsing initial response...")
    data = response.json()
    items = data.get('content', [])
    total_pages = data.get('totalPages', 1)
    print(f"Total pages to scrape: {total_pages}")
    all_data.extend(format_data(items))
    
    # Loop through each remaining page
    for page in range(1, total_pages):
        print(f"Fetching page {page}...")
        response = requests.post(
            url,
            json=payload,
            params={"page": page, "size": size}
        )
        
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()
            items = data.get('content', [])
            all_data.extend(format_data(items))
        else:
            print(f"Error fetching page {page}: {response.status_code} - {response.reason}")
            break

    # Save all collected data to JSON in the specified format
    save_data_to_json(all_data, output_path)
    print(f"\nTotal items retrieved: {len(all_data)}")
    print("=" * 40)
else:
    print(f"Initial request failed with status: {response.status_code} - {response.reason}")
    print("=" * 40)
