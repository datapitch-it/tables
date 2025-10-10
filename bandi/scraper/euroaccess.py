import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
import shutil
import re

# URL base della pagina da cui estrarre i dati
base_url = "https://www.euro-access.eu/en/calls"

def check_and_rename_file(file_path):
    """Checks if the JSON file exists and renames it."""
    if os.path.exists(file_path):
        # Create the new filename by appending "ieri" before the file extension
        new_file_path = file_path.replace(".json", "_ieri.json")
        if os.path.exists(new_file_path):
            os.remove(new_file_path)
        shutil.move(file_path, new_file_path)
        print(f"File renamed to {new_file_path}")
    else:
        print(f"No existing file to rename at {file_path}")

def get_page_content(url):
    """Fetches and parses the HTML content of a URL."""
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def standardize_date(date_str):
    """Standardizes date strings to YYYY-MM-DD format."""
    if not date_str or date_str == 'N/A':
        return 'N/A'
    # Format on the site is "DD.MM.YYYY HH:MM"
    try:
        # We only care about the date part
        date_part = date_str.split(' ')[0]
        return datetime.strptime(date_part, "%d.%m.%Y").strftime("%Y-%m-%d")
    except (ValueError, IndexError):
        print(f"Could not parse date: {date_str}")
        return date_str

def extract_call_details(detail_url):
    """Extracts detailed information from a call's detail page using a robust method."""
    soup = get_page_content(detail_url)
    if not soup:
        return "N/A", {}

    custom_data = {}
    description = "N/A"  # Reliably extracting description is not feasible.

    # --- Extract all sections based on h4 headings ---
    sections = soup.find_all('div', class_='row-flex')
    for section in sections:
        headings = section.find_all('h4')
        for heading in headings:
            heading_text = heading.text.strip()
            content_div = heading.find_next_sibling('div')
            if not content_div:
                continue

            # --- Key Data Section ---
            if "Call key data" in heading_text:
                # Find all paragraphs, then find strong tags within them
                all_paragraphs = content_div.find_all('p')
                for p in all_paragraphs:
                    label_elem = p.find('strong')
                    if label_elem:
                        label = label_elem.text.strip()
                        value_p = p.find_next_sibling('p')
                        if value_p:
                            custom_data[label] = value_p.text.strip()

            # --- Eligibility and Additional Info ---
            else:
                # For other sections, find all strong tags as labels
                labels = content_div.find_all('strong')
                for label_elem in labels:
                    label = label_elem.text.strip()
                    # Find the text in the parent, removing the label to get the value
                    parent_text = label_elem.find_parent().text.strip()
                    value = parent_text.replace(label, '').strip()
                    if value:
                        custom_data[label] = value

    return description, custom_data

def extract_data_from_list_page(soup):
    """Extracts basic call data from a list/results page."""
    bandi = soup.select('table > tbody > tr')
    extracted_data = []

    for bando in bandi:
        cells = bando.find_all('td')
        if len(cells) < 3:
            continue

        title_elem = cells[1].find('a')
        title = title_elem.text.strip() if title_elem else 'N/A'

        relative_link = title_elem['href'] if title_elem else None
        if not relative_link:
            continue
        link = f"https://www.euro-access.eu{relative_link}"

        deadline_raw = cells[2].text.strip()
        deadline = standardize_date(deadline_raw)

        # Removed the print statement here
        # print(f"  - Found: {title}")

        description, custom_details = extract_call_details(link)

        custom_details["Funding Program"] = cells[0].text.strip()

        extracted_data.append({
            "deadline": deadline,
            "title": title,
            "description": description,
            "link": link,
            "custom": custom_details
        })

    return extracted_data

def get_total_pages(soup):
    """Gets the total number of pages from the pagination control."""
    pager = soup.find('ul', class_='pagination')
    if not pager:
        return 1

    last_page_link = pager.find('a', string=re.compile(r"Last", re.IGNORECASE))
    if last_page_link and 'href' in last_page_link.attrs:
        last_page_url = last_page_link['href']
        match = re.search(r'page=(\d+)', last_page_url)
        if match:
            return int(match.group(1)) + 1

    # Fallback if "Last" is not found, find the highest page number visible
    page_numbers = pager.find_all('a')
    max_page = 1
    for page_link in page_numbers:
        match = re.search(r'page=(\d+)', page_link.get('href', ''))
        if match:
            max_page = max(max_page, int(match.group(1)))
    return max_page + 1 if max_page > 1 else 1

def main():
    """Main function to orchestrate the scraping process."""
    output_dir = "../data/"
    output_file = "euro-access.json"
    output_path = os.path.join(output_dir, output_file)

    check_and_rename_file(output_path)

    # Start with a broad search to get all calls
    initial_url = f"{base_url}?keyword=&submit=&sent=search"
    print(f"Starting scraping from {initial_url}")

    first_page_soup = get_page_content(initial_url)
    if not first_page_soup:
        print("Could not fetch the first page. Aborting.")
        return

    total_pages = get_total_pages(first_page_soup)
    print(f"Found a total of {total_pages} pages.")

    all_data = []

    for page_num in range(total_pages):
        print(f"\nScraping page {page_num + 1} of {total_pages}...")
        page_url = f"{initial_url}&page={page_num}"
        soup = get_page_content(page_url)
        if soup:
            page_data = extract_data_from_list_page(soup)
            all_data.extend(page_data)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output_data = {
        "scraping_timestamp": timestamp,
        "data": all_data
    }

    os.makedirs(output_dir, exist_ok=True)

    with open(output_path, mode='w', encoding='utf-8') as file:
        json.dump(output_data, file, ensure_ascii=False, indent=4)

    print("=" * 40)
    print(f"\nTotal items retrieved: {len(all_data)}")
    print(f"Data saved to {output_path}")
    print("=" * 40)

if __name__ == "__main__":
    main()

