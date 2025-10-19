import requests
import os
import json
from datetime import datetime
from bs4 import BeautifulSoup

# API endpoint
API_URL = "https://www.incentivi.gov.it/solr/coredrupal/select?q.op=OR&wt=json&rows=8000&fl=zs_nid,zs_url,page_title,zs_title,zs_body,zs_field_close_date,search_meta,regions,costs&q=index_id%3Aincentivi+tum_X3b_it_title_ft%3A***%5E3+twm_X3b_it_field_search_meta%3A*%5E2.5+tum_X3b_it_field_subtitle_ft%3A***%5E2+tum_X3b_it_body_ft%3A***%5E1+tum_X3b_it_output%3A***%5E0.5+&sort=ds_last_update+desc"

# Output file paths
output_dir = "../data"
output_file = "incentivigov.json"
backup_file = "incentivigovieri.json"
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
    if date_str is None:
        return "N/A"
    try:
        # The date format from the API is "YYYY-MM-DDTHH:MM:SS"
        return datetime.fromisoformat(date_str).strftime("%Y-%m-%d")
    except (ValueError, TypeError) as e:
        print(f"Date formatting error: {e} for date_str: {date_str}")
        return "N/A"

def save_data_to_json(data, output_path):
    formatted_data = {
        "scraping_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": data
    }

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=4)
    print(f"Data saved to {output_path}")

def scrape_incentivi():
    backup_existing_file(output_path, backup_path)
    all_incentives = []

    response = requests.get(API_URL)

    if response.status_code == 200:
        data = response.json()
        docs = data.get("response", {}).get("docs", [])

        for doc in docs:
            # Prioritize page_title, fallback to zs_title
            title = doc.get("page_title")
            if not title:
                title = doc.get("zs_title", "N/A")
            
            # Prioritize zs_url for the link
            relative_link = doc.get("zs_url")
            nid = doc.get("zs_nid") # Get nid for fallback
            
            link = "N/A"
            if relative_link:
                link = f"https://www.incentivi.gov.it{relative_link}"
            elif nid:
                # Fallback to nid if zs_url is not available
                link = f"https://www.incentivi.gov.it/it/catalogo/{nid}"
            
            deadline = format_date(doc.get("zs_field_close_date"))
            
            # Extract description from 'zs_body'
            description = doc.get("zs_body", "N/A")

            # Custom fields
            topics = doc.get("search_meta", "N/A")
            area_classification = ", ".join(doc.get("regions", [])) if doc.get("regions") else "N/A"
            tipologia_scadenza = "N/A" # Not directly available in API response
            stanziamento = "N/A"
            if doc.get("costs") and len(doc["costs"]) == 2:
                stanziamento = f"{doc["costs"][0]} - {doc["costs"][1]}"
            elif doc.get("costs") and len(doc["costs"]) == 1:
                stanziamento = doc["costs"][0]

            all_incentives.append({
                "deadline": deadline,
                "title": title,
                "description": description,
                "link": link,
                "custom": {
                    "Topics": topics,
                    "Area Classification": area_classification,
                    "Tipologia Scadenza": tipologia_scadenza,
                    "Stanziamento": stanziamento
                }
            })

        save_data_to_json(all_incentives, output_path)
        print(f"Total incentives scraped: {len(all_incentives)}")
    else:
        print(f"Error fetching data from API: {response.status_code} - {response.reason}")

if __name__ == "__main__":
    scrape_incentivi()
