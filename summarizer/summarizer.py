import os
import random
import time
import subprocess
import json
from datetime import datetime

def process_item(item):
    try:
        with open('items.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    data.append(item)
    with open('items.json', 'w') as f:
        json.dump(data, f, indent=4)

def remove_control_characters(s):
    return ''.join(c for c in s if 31 < ord(c))

def is_url_processed(url):
    try:
        with open('items.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return False
    for item in data:
        if item.get('source_url') == url:
            return True
    return False

# Read URLs from the file
try:
    with open('./sources.txt', 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
except FileNotFoundError:
    print("Error: The file 'sources.txt' was not found.")
    urls = []

data_list = []  # Keep this initialization outside the loop
for url in urls:
    url = url.strip()
    if is_url_processed(url):
        print(f"URL {url} is already processed. Skipping.")
        continue
    # Execute the pipeline
    print(f"Fetching and processing URL: {url}")
    try:
        curl_output = subprocess.check_output(['curl', '-s', '-H', 'Accept-Charset: utf-8', url]).decode('utf-8', errors='ignore')
        pup_output = subprocess.check_output(['pup', 'body text{}'], input=curl_output, text=True)

        # Truncate the input if it's too long
        max_context_length = 131072
        if len(pup_output) > max_context_length:
            pup_output = pup_output[:max_context_length]

        # Correct the llm command
        llm_output = subprocess.check_output(
            [
                'llm', '-m', 'mistral-small',
                '--schema', 'source_name,source_url,source_generated_summary',
                'given the text, generate json item with source name, source url (example: https://www.wheresyoured.at/power-cut/?ref=ed-zitrons-wheres-your-ed-newsletter), source generated summary in Italian with a maximum of 300 tokens. No symbols, no markdown',
                '-o', 'max_tokens', '300'
            ],
            input=remove_control_characters(pup_output),
            text=True
        )

        llm_data = json.loads(llm_output)
        formatted_data = {
            "source_name": llm_data.get('source_name', 'N/A'),
            "source_url": llm_data.get('source_url', 'N/A'),
            "source_generated_summary": llm_data.get('source_generated_summary', 'N/A')
        }
        # Append to items.json immediately after processing each item
        process_item(formatted_data)
    except subprocess.CalledProcessError as e:
        print(f"Error in pipeline execution for URL {url}: {e}")
        error_item = {
            "source_name": "N/A",
            "source_url": url,
            "source_generated_summary": f"Errore: il sommario non è stato generato per il seguente errore: {str(e)}"
        }
        process_item(error_item)
        continue  # Skip to the next URL
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for URL {url}: {e}")
        error_item = {
            "source_name": "N/A",
            "source_url": url,
            "source_generated_summary": f"Errore: il sommario non è stato generato per il seguente errore: {str(e)}"
        }
        process_item(error_item)
        continue  # Skip to the next URL
    except Exception as e:
        print(f"Unexpected error for URL {url}: {e}")
        error_item = {
            "source_name": "N/A",
            "source_url": url,
            "source_generated_summary": f"Errore: il sommario non è stato generato per il seguente errore: {str(e)}"
        }
        process_item(error_item)
        continue  # Skip to the next URL

    random_sleep_time = random.randint(2, 9)
    time.sleep(random_sleep_time)

# Debugging: Print a message indicating the end of the script
print("Script execution completed.")
