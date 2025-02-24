import json
import os
import shutil
import re
import requests
from bs4 import BeautifulSoup

# Define the file path and the target paths to look for
file_path = './posts.json'
output_file = './extracted_data.json'
target_paths = {
    "/commentary/text/text",
    "/content/com.linkedin.voyager.feed.render.ArticleComponent/navigationContext/actionTarget",
    "/updateMetadata/urn"  # Updated path
}

# Function to find a value by path within each JSON object
def find_by_path(data, target_path, current_path=""):
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{current_path}/{key}"
            if new_path == target_path:
                return value
            result = find_by_path(value, target_path, new_path)
            if result is not None:
                return result
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_path = f"{current_path}[{i}]"
            result = find_by_path(item, target_path, new_path)
            if result is not None:
                return result
    return None

# Function to extract URLs from a string
def extract_urls(text):
    return re.findall(r'https?://[^\s]+', text)

# Function to fetch the href attribute from the target <a> tag on a webpage
def fetch_href_from_url(url):
    print(f"Attempting to fetch URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"Successfully fetched URL: {url}, Status Code: {response.status_code}")
        response.raise_for_status()  # Raise an error for HTTP errors
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find the <a> tag with the specified attributes
        a_tag = soup.find('a', {
            'class': 'artdeco-button artdeco-button--tertiary',
            'data-tracking-control-name': 'external_url_click',
            'data-tracking-will-navigate': ''
        })
        if a_tag and 'href' in a_tag.attrs:
            extracted_href = a_tag['href']
            print(f"Extracted href: {extracted_href} from URL: {url}")
            return extracted_href
        else:
            print(f"No matching <a> tag found on URL: {url}")
    except requests.RequestException as e:
        print(f"Request error for URL: {url}, Error: {e}")
    except Exception as e:
        print(f"General error while processing URL: {url}, Error: {e}")
    return None

# Function to backup the existing output file
def backup_output_file(file_path):
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup"
        shutil.copy(file_path, backup_path)
        print(f"Backup created: {backup_path}")

# Main script
def main():
    # Load existing output data
    if os.path.exists(output_file):
        with open(output_file, 'r') as outfile:
            existing_data = json.load(outfile)
    else:
        existing_data = []

    # Load the input JSON data
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)  # Load the entire JSON file as an array
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading input file: {e}")
        return

    # Extract data from the JSON file
    extracted_entries = []
    for entry in data:
        extracted_data = {}
        inline_urls = []  # To store URLs from /commentary/text/text

        for path in target_paths:
            found_value = find_by_path(entry, path)
            if found_value:
                if "actionTarget" in path:
                    label = "link"
                elif "text" in path:
                    label = "text"
                    # Extract URLs if the path is /commentary/text/text
                    extracted_urls = extract_urls(found_value)
                    for url in extracted_urls:
                        # Fetch and extract href from the webpage
                        href = fetch_href_from_url(url)
                        if href:
                            inline_urls.append(href)
                elif "urn" in path:
                    label = "urn"  # New label for /updateMetadata/urn
                else:
                    label = "value"
                extracted_data[label] = found_value

        # Add the extracted inline URLs to the new key
        if inline_urls:
            extracted_data["inline-url"] = inline_urls

        if extracted_data:
            extracted_entries.append(extracted_data)

    # Deduplicate based on 'urn' field
    existing_urns = {entry.get("urn") for entry in existing_data}
    for new_entry in extracted_entries:
        if new_entry.get("urn") not in existing_urns:
            existing_data.append(new_entry)

    # Backup the current output file
    backup_output_file(output_file)

    # Save the updated data to the output file
    with open(output_file, 'w') as outfile:
        json.dump(existing_data, outfile, indent=4)

    print(f"Updated data has been written to {output_file}. Total entries: {len(existing_data)}")

# Run the script
if __name__ == "__main__":
    main()
