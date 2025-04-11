import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
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

# Start measuring time
start_time = time.time()

# Set up WebDriver using WebDriver Manager
driver = webdriver.Chrome(service=Service())

# New source URL
base_url = "https://getonepass.eu/search/opportunities?refinementList%5Btype%5D%5B0%5D=equity-free&refinementList%5Bstatus%5D%5B0%5D=Open%20for%20applications&sortBy=prod_dates_desc"
base_website_url = "https://getonepass.eu"

# List to store all the opportunities
opportunities_data = []

# Function to scrape data from a single page
def scrape_opportunities_from_page(page_num):
    driver.get(f"{base_url}&page={page_num}")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "ui.segment.discoveryCard")))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Loop through each opportunity div and extract relevant information
    for div in soup.find_all('div', class_='ui segment discoveryCard'):
        title_tag = div.find('h3', class_='ui wide header')
        title = title_tag.get_text(strip=True) if title_tag else "No title found"

        link_tag = title_tag.find('a') if title_tag else None
        url_path = link_tag.get('href') if link_tag else "No URL found"
        link = f"{base_website_url}{url_path}" if url_path.startswith('/') else url_path

        description_tag = div.find_all('p')[0]
        description = description_tag.get_text(strip=True) if description_tag else "No description found"

        tags_div = div.find('div', class_='tags')
        tags = [tag.get_text(strip=True) for tag in tags_div.find_all('a')] if tags_div else ["No tags found"]

        status_tag = div.find_all('p')[1]
        if status_tag:
            deadline_small = status_tag.find('small')
            raw_deadline = deadline_small.get_text(strip=True).replace('Apply before ', '') if deadline_small else "No deadline found"
        else:
            raw_deadline = "No deadline found"
        
        # Format deadline
        deadline = format_deadline(raw_deadline)

        # Prepare data structure
        opportunity = {
            "deadline": deadline,
            "title": title,
            "description": description,
            "link": link,
            "custom": {
                "tags": tags,
                "status": "Open for applications" if status_tag and status_tag.find('span', class_='ui empty olive circular mini label') else "Unknown status"
            }
        }
        opportunities_data.append(opportunity)

# Function to format the deadline to "YYYY-MM-DD"
def format_deadline(deadline_str):
    try:
        if deadline_str == "No deadline found":
            return "N/A"
        deadline_date = datetime.strptime(deadline_str, "%d/%m/%Y")
        return deadline_date.strftime("%Y-%m-%d")
    except ValueError:
        return "Invalid date format"

# Determine the total number of pages from pagination
def get_total_pages():
    driver.get(f"{base_url}&page=1")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "pagination")))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    pagination = soup.find('ul', class_='ais-Pagination-list')
    if pagination:
        page_links = [link.get_text(strip=True) for link in pagination.find_all('a') if link.get_text(strip=True).isdigit()]
        if page_links:
            return int(page_links[-1])
    return 1

# Get the total number of pages
total_pages = get_total_pages()

# Loop through all pages and scrape data
for page_num in range(1, total_pages + 1):
    print(f"Scraping page {page_num} of {total_pages}...\n")
    scrape_opportunities_from_page(page_num)

# Close the browser
driver.quit()

# Prepare final output structure
output_data = {
    "scraping_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "data": opportunities_data
}

# Check if the existing file needs to be renamed
output_file = "../data/onepass.json"
check_and_rename_file(output_file)

# Write the collected data to a JSON file
with open(output_file, "w", encoding="utf-8") as json_file:
    json.dump(output_data, json_file, ensure_ascii=False, indent=4)

# Measure the total time taken
end_time = time.time()
execution_time = end_time - start_time

print(f"Script executed in {execution_time:.2f} seconds.")
print(f"\nTotal items retrieved: {len(opportunities_data)}")
print(f"Last scraping on {output_data['scraping_timestamp']}")
print("=" * 40)
