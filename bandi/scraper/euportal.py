import json
import requests
from ics import Calendar
import re
from datetime import datetime
import os
import shutil

# Function to check if the JSON file exists and rename it
def check_and_rename_file(file_path):
    if os.path.exists(file_path):
        new_file_path = file_path.replace(".json", "ieri.json")
        shutil.move(file_path, new_file_path)
        print(f"File renamed to {new_file_path}")
    else:
        print(f"No existing file to rename at {file_path}")

def download_ics_content(url):
    """Downloads the .ics file content from the provided URL without saving it."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        print(f".ics file content fetched successfully from {url}")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch .ics file: {e}")
        return None

def clean_text(text):
    """Cleans newline characters and excessive spaces from the text."""
    return text.replace('\n', ' ').strip()

def extract_topic_link(description):
    """Extracts 'Topic Link' from the description."""
    match = re.search(r'Topic Link:\s*(https?://\S+)', description)
    return match.group(1) if match else None

def remove_topic_link_from_description(description):
    """Removes 'Topic Link' from the description."""
    return re.sub(r'Topic Link:\s*(https?://\S+)', '', description).strip()

def format_date_to_yyyy_mm_dd(date_obj):
    """Formats a given date object into YYYY-MM-DD format."""
    return date_obj.strftime('%Y-%m-%d') if date_obj else None

def parse_ics_content(ics_content):
    """Parses the .ics content and extracts event data."""
    calendar = Calendar(ics_content)

    events_data = []

    for event in calendar.events:
        # Map fields to the new structure
        deadline = format_date_to_yyyy_mm_dd(event.end) if event.end else "N/A"
        title = clean_text(event.name) if event.name else "No Title"
        
        description = clean_text(remove_topic_link_from_description(event.description)) if event.description else "No Description"
        link = extract_topic_link(event.description) if event.description else "N/A"
        
        # Collect additional fields into 'custom'
        custom = {
            "dtstart": format_date_to_yyyy_mm_dd(event.begin) if event.begin else "N/A",
            "location": clean_text(event.location) if event.location else "No Location",
            "uid": clean_text(event.uid) if event.uid else "No UID"
        }
        
        events_data.append({
            "deadline": deadline,
            "title": title,
            "description": description,
            "link": link,
            "custom": custom
        })

    return events_data

def save_to_json(events_data, output_file):
    """Saves the parsed event data to a JSON file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    output_data = {
        "scraping_timestamp": timestamp,
        "data": events_data
    }
    
    with open(output_file, 'w') as json_file:
        json.dump(output_data, json_file, ensure_ascii=False, indent=4)
    print(f"\nTotal items retrieved: {len(events_data)}")
    print(f"Data saved to {output_file}")

# URL of the .ics file
ics_url = "https://ec.europa.eu/info/funding-tenders/opportunities/data/referenceData/grantTenders.ics"
output_file = '../data/euportal.json'

# Step 1: Check if the existing file needs to be renamed
check_and_rename_file(output_file)

# Step 2: Fetch the .ics file content directly from the URL
ics_content = download_ics_content(ics_url)

# Step 3: Parse the .ics content and save as JSON if the download was successful
if ics_content:
    events_data = parse_ics_content(ics_content)
    save_to_json(events_data, output_file)
    print(f"Events successfully parsed and saved to {output_file}.")
    print("=" * 40)
else:
    print("No data to process due to content fetch failure.")
    print("=" * 40)
