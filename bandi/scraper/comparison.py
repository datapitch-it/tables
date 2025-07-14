import json
import os
import logging
from datetime import datetime

# Set up logging configuration with a custom format for improved readability
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the directory containing the JSON files
directory = os.path.abspath("../data")
new_items_filename = os.path.join(directory, "newitems.json")

# Step 1: Check if "newitems.json" exists, then delete it if it does
try:
    if os.path.exists(new_items_filename):
        os.remove(new_items_filename)
        logging.info(f"Removed existing file: {new_items_filename}")
    else:
        logging.info(f"No existing newitems.json file to remove.")
except Exception as e:
    logging.error(f"Error removing newitems.json: {e}")

# Function to load and standardize the "link" field in JSON files
def load_and_standardize_url(filepath):
    try:
        logging.info(f"Loading file: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for item in data.get("data", []):
                # Standardize URL field names and rename to "link"
                item["link"] = item.pop("link", item.pop("URL", item.get("url", "No link")))
        logging.info(f"Standardized URLs in file: {filepath}")
        return data["data"]
    except Exception as e:
        logging.error(f"Error loading file {filepath}: {e}")
        return []

# Function to pair files with and without "ieri" suffix
def get_file_pairs(directory):
    try:
        files = os.listdir(directory)
        pairs = []
        for file in files:
            if file.endswith(".json") and not file.endswith("ieri.json"):
                base_name = file.replace(".json", "")
                ieri_file = f"{base_name}ieri.json"
                if ieri_file in files:
                    pairs.append((file, ieri_file))
        logging.info(f"Found pairs: {pairs}")
        return pairs
    except Exception as e:
        logging.error(f"Error getting file pairs: {e}")
        return []

# Function to ensure each item matches the new structure
def standardize_structure(item):
    try:
        return {
            "deadline": item.get("deadline", "N/A"),
            "title": item.get("title", "No title"),
            "description": item.get("description", "No description"),
            "link": item.get("link", "No link"),
            "custom": {
                key: value for key, value in item.items()
                if key not in {"deadline", "title", "description", "link"}
            }
        }
    except Exception as e:
        logging.error(f"Error standardizing structure: {e}")
        return item

# Function to separate new and removed items, and create newitems.json
def compare_and_store_items(directory, pairs):
    total_new_items = []
    for current_file, ieri_file in pairs:
        try:
            current_data = load_and_standardize_url(os.path.join(directory, current_file))
            ieri_data = load_and_standardize_url(os.path.join(directory, ieri_file))

            current_dict = {item["link"]: item for item in current_data if "link" in item}
            ieri_dict = {item["link"]: item for item in ieri_data if "link" in item}

            new_items_group = []

            for link, current_item in current_dict.items():
                if link not in ieri_dict:
                    standardized_item = standardize_structure(current_item)
                    new_items_group.append(standardized_item)
                    logging.info(f"New item found - URL: {link}, Deadline: {standardized_item['deadline']}")

            total_new_items.extend(new_items_group)

            summary_line = "=" * 40
            logging.info(f"n{summary_line}")
            logging.info(f"Summary for pair {current_file} and {ieri_file}:")
            logging.info(f"Total items in current file: {len(current_dict)}")
            logging.info(f"Total items in ieri file: {len(ieri_dict)}")
            logging.info(f"New items: {len(new_items_group)}")
            logging.info(f"{summary_line}n")
        except Exception as e:
            logging.error(f"Error comparing files {current_file} and {ieri_file}: {e}")

    # Write new items to "newitems.json" in the standardized structure
    output_data = {
        "scraping_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": total_new_items
    }

    try:
        with open(new_items_filename, 'w', encoding='utf-8') as new_file:
            json.dump(output_data, new_file, ensure_ascii=False, indent=4)
        logging.info(f"Saved all new items to {new_items_filename}")
    except Exception as e:
        logging.error(f"Error saving new items to {new_items_filename}: {e}")

# Usage Example
pairs = get_file_pairs(directory)
compare_and_store_items(directory, pairs)
logging.info("Script execution completed.")
