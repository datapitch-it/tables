import requests
import json
import logging
import os
import shutil
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define URL and output path
url = "https://ec.europa.eu/info/funding-tenders/opportunities/data/referenceData/grantsTenders.json"
output_file = "../data/eugrants.json"

# Function to check if the JSON file exists and rename it
def check_and_rename_file(file_path):
    if os.path.exists(file_path):
        # Create the new filename by appending "ieri" before the file extension
        new_file_path = file_path.replace(".json", "ieri.json")
        shutil.move(file_path, new_file_path)
        print(f"File renamed to {new_file_path}")
    else:
        print(f"No existing file to rename at {file_path}")

def fetch_data():
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        logging.info(f"Fetched {len(data['fundingData']['GrantTenderObj'])} elements from the URL.")
        return data['fundingData']['GrantTenderObj']
    except requests.RequestException as e:
        logging.error("Error fetching data: ", exc_info=True)
        return []

def transform_data(call):
    # Transform the input data to the desired output format
    deadline = datetime.fromtimestamp(call.get('deadlineDatesLong', [0])[0] / 1000, timezone.utc).strftime('%Y-%m-%d') if call.get('deadlineDatesLong') else None
    opening_date = datetime.fromtimestamp(call.get('plannedOpeningDateLong', 0) / 1000, timezone.utc).strftime('%Y-%m-%d') if call.get('plannedOpeningDateLong') else None
    publication_date = datetime.fromtimestamp(call.get('publicationDateLong', 0) / 1000, timezone.utc).strftime('%Y-%m-%d') if call.get('publicationDateLong') else None

    identifier = call.get('identifier', 'N/A')
    description = (
        f"Identifier: {identifier}\n"
        f"Pillar: {call.get('callIdentifier', 'N/A')}\n"
        f"Opening Date: {opening_date}\n"
        f"Deadline: {deadline}\n"
    )

    # Append latestInfos if available
    latest_infos = call.get('latestInfos', [])
    if latest_infos:
        for info in latest_infos:
            last_change_date = info.get('lastChangeDate', 'No Date Provided')
            content = info.get('content', 'No Content Provided')
            description += f"\nLast Change Date: {last_change_date}\nContent: {content}\n"

    # Construct the link using the identifier
    link = f"https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/{identifier}"

    return {
        "deadline": deadline,
        "title": call.get('title', 'No Title Provided'),
        "description": description,
        "link": link,
        "custom": {
            "category": call.get('frameworkProgramme', {}).get('abbreviation', ""),
            "guid": call.get('callTitle', 'No Call Title'),
            "pub_date": publication_date,
            "dc_date": publication_date,
            "identifier": identifier
        }
    }

def save_data(transformed_data):
    # Get current timestamp
    scraping_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Structure the output with scraping timestamp and data
    output = {
        "scraping_timestamp": scraping_timestamp,
        "data": transformed_data
    }
    
    # Check if the previous file exists and rename it
    check_and_rename_file(output_file)
    
    try:
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=4)
        logging.info(f"Data saved to {output_file}")
    except IOError as e:
        logging.error("Error saving data: ", exc_info=True)

def main():
    raw_data = fetch_data()
    transformed_data = [transform_data(call) for call in raw_data]
    save_data(transformed_data)

if __name__ == "__main__":
    main()
