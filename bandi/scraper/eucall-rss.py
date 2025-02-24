import xml.etree.ElementTree as ET
import json
import logging
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime
import requests
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URL to download the XML file
xml_url = 'https://ec.europa.eu/info/funding-tenders/opportunities/data/referenceData/callupdates-rss.xml'
output_file = '../data/eucall-rss.json'

# Function to check if the JSON file exists and rename it
def check_and_rename_file(file_path):
    if os.path.exists(file_path):
        new_file_path = file_path.replace(".json", "ieri.json")
        shutil.move(file_path, new_file_path)
        logging.info(f"File renamed to {new_file_path}")
    else:
        logging.info(f"No existing file to rename at {file_path}")

# Check and rename the existing file if it exists
check_and_rename_file(output_file)

# Download the XML content from the URL
try:
    logging.info(f"Downloading XML file from: {xml_url}")
    response = requests.get(xml_url)
    response.raise_for_status()
    xml_content = response.content
except requests.exceptions.RequestException as e:
    logging.error(f"Error downloading XML file: {e}")
    exit(1)

# Parse the downloaded XML content
try:
    logging.info("Parsing the downloaded XML content.")
    root = ET.fromstring(xml_content)
except ET.ParseError as e:
    logging.error(f"Error parsing XML content: {e}")
    exit(1)

# Namespace
ns = {'dc': 'http://purl.org/dc/elements/1.1/'}

# List to hold JSON objects (array of items)
json_data = []

# Regular expressions to find deadlines and identifiers
deadline_pattern = re.compile(r'Deadline: ([\w, ]+ \d{2}:\d{2}:\d{2})')
identifier_pattern = re.compile(r'Identifier: (.*?)Pillar')

# Function to standardize date formats to YYYY-MM-DD
def standardize_date(date_str):
    date_formats = [
        "%d/%m/%Y", "%Y-%m-%dT%H:%M:%SZ", "%d.%m.%Y", "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S", "%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S"
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return "N/A"  # Return 'N/A' if no format matched

# Function to check if the item date is on or after 2024-03-01
def is_after_march_2024(date_string):
    try:
        date_obj = datetime.strptime(date_string, '%Y-%m-%d')
        limit_date = datetime(2015, 3, 1)
        return date_obj >= limit_date
    except Exception as e:
        logging.warning(f"Error checking date: {e}")
        return False

# Process XML items
for item in root.findall('.//item'):
    try:
        title = item.findtext('title')
        link = item.findtext('link')
        description_html = item.findtext('description')
        description = BeautifulSoup(description_html, 'html.parser').get_text() if description_html else "No Description"
        pub_date = item.findtext('pubDate')
        dc_date = item.find('dc:date', ns).text if item.find('dc:date', ns) is not None else None

        # Extract and standardize dates
        deadline_match = deadline_pattern.search(description)
        identifier_match = identifier_pattern.search(description)
        deadline = standardize_date(deadline_match.group(1)) if deadline_match else "N/A"
        formatted_pub_date = standardize_date(pub_date) if pub_date else "N/A"
        formatted_dc_date = standardize_date(dc_date) if dc_date else "N/A"

        # Filter out items before 2024-03-01
        if not is_after_march_2024(formatted_pub_date):
            continue

        # Custom fields
        custom = {
            "category": item.findtext('category') or "N/A",
            "guid": item.findtext('guid') or "N/A",
            "pub_date": formatted_pub_date,
            "dc_date": formatted_dc_date,
            "identifier": identifier_match.group(1).strip() if identifier_match else "N/A"
        }

        # Final data structure
        data = {
            "deadline": deadline,
            "title": title,
            "description": description,
            "link": f"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/{custom['identifier']}" if custom["identifier"] != "N/A" else link,
            "custom": custom
        }

        # Append to list
        json_data.append(data)
    
    except Exception as e:
        logging.error(f"Error processing item: {e}")

# Add the timestamp for scraping
scraping_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Final output structure with the timestamp and data
output_data = {
    "scraping_timestamp": scraping_timestamp,
    "data": json_data
}

# Save the JSON data to a file
try:
    logging.info(f"Saving extracted data to JSON file: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as json_file:
        json.dump(output_data, json_file, ensure_ascii=False, indent=4)
    logging.info("Data successfully saved.")
    print(f"\nTotal items retrieved: {len(json_data)}")
except Exception as e:
    logging.error(f"Error saving JSON file: {e}")
    exit(1)
    print("=" * 40)
