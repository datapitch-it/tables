import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json

def get_text_or_na(element, join_paragraphs=False):
    """Safely extracts text from a BeautifulSoup element."""
    if not element:
        return "N/A"
    if join_paragraphs:
        paragraphs = element.find_all('p')
        if paragraphs:
            return "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        else: # Fallback if no <p> tags, just get all text
            return element.get_text(strip=True)
    return element.get_text(strip=True)

def get_multiple_texts_or_na(elements_list):
    """Safely extracts text from a list of BeautifulSoup elements and joins them."""
    if not elements_list:
        return "N/A"
    texts = [el.get_text(strip=True) for el in elements_list if el.get_text(strip=True)]
    return ", ".join(texts) if texts else "N/A"


def scrape_project_details(project_url, project_title, headers):
    """
    Scrapes detailed content from a single project page.
    """
    print(f"  Scraping details for: {project_title} ({project_url})")
    project_content = {
        "Science cluster": "N/A",
        "Summary": "N/A",
        "Challenge": "N/A",
        "Solution": "N/A",
        "Scientific Impact": "N/A",
        "Keywords": "N/A",
        "Principal investigator": {"Name": "N/A", "Organisation": "N/A"}
    }

    try:
        response = requests.get(project_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')

        # Main content area for project details
        # The overall container for a project page seems to be div.node--type-project
        node_full = soup.find('div', class_='node--type-project') # node--full or node--type-project
        if not node_full:
            print(f"    Warning: Could not find main project content area for {project_url}")
            return project_content # Return default N/A values

        # --- Science Cluster ---
        intro_area = node_full.find('div', class_='intro-area')
        if intro_area:
            cluster_elements = intro_area.select('div.clusters div.cluster div.label')
            project_content["Science cluster"] = get_multiple_texts_or_na(cluster_elements)

        # Main body content (Summary, Challenge, Solution, Impact, Keywords)
        main_body = node_full.find('div', class_='main-body')
        if main_body:
            # --- Summary ---
            summary_div = main_body.find('div', class_='summary')
            if summary_div:
                summary_field = summary_div.find('div', class_='field--name-body') or \
                                summary_div.find('div', class_='text-formatted') # Fallback
                project_content["Summary"] = get_text_or_na(summary_field, join_paragraphs=True)

            # --- Challenge ---
            challenge_div = main_body.find('div', class_='challenge')
            if challenge_div:
                challenge_field = challenge_div.find('div', class_='field--name-field-challenge-formatted') or \
                                  challenge_div.find('div', class_='text-formatted')
                project_content["Challenge"] = get_text_or_na(challenge_field, join_paragraphs=True)

            # --- Solution ---
            solution_div = main_body.find('div', class_='solution')
            if solution_div:
                solution_field = solution_div.find('div', class_='field--name-field-solution') or \
                                 solution_div.find('div', class_ = 'text-formatted')
                project_content["Solution"] = get_text_or_na(solution_field, join_paragraphs=True)

            # --- Scientific Impact ---
            impact_div = main_body.find('div', class_='impact')
            if impact_div:
                impact_field = impact_div.find('div', class_='field--name-field-scientific-impact-formatte') or \
                               impact_div.find('div', class_='text-formatted') # field-scientific-impact-formatted
                project_content["Scientific Impact"] = get_text_or_na(impact_field, join_paragraphs=True)
            
            # --- Keywords ---
            # Keywords are in a div.resources structure, but we'll target the specific field name
            keywords_field = main_body.find('div', class_='field--name-field-keywords')
            if keywords_field: # This directly gives the div with keywords
                 project_content["Keywords"] = get_text_or_na(keywords_field)
            else: # Fallback if the above is not found, try to find by label
                resources_divs = main_body.find_all('div', class_='resources')
                for res_div in resources_divs:
                    label_div = res_div.find('div', class_='label')
                    if label_div and 'Keywords' in label_div.get_text(strip=True):
                        value_div = res_div.find('div', class_='value')
                        if value_div:
                            project_content["Keywords"] = get_text_or_na(value_div.find('div', class_='field__item') or value_div)
                        break


        # Sidebar for Principal Investigator
        sidebar = node_full.find('div', class_='col-lg-3') # More robust than offset-lg-1
        if sidebar:
            pi_section = sidebar.find('div', class_='principal-investigator')
            if pi_section:
                pi_name_div = pi_section.find('div', class_='pi-name')
                project_content["Principal investigator"]["Name"] = get_text_or_na(pi_name_div)
                
                pi_org_div = pi_section.find('div', class_='pi-organisation')
                if pi_org_div:
                    pi_org_field = pi_org_div.find('div', class_='field--name-field-pi-organisation') or pi_org_div
                    project_content["Principal investigator"]["Organisation"] = get_text_or_na(pi_org_field)

    except requests.exceptions.RequestException as e:
        print(f"    Error fetching project details from {project_url}: {e}")
        # project_content will retain its N/A defaults
    except Exception as e:
        print(f"    An unexpected error occurred while parsing {project_url}: {e}")

    time.sleep(0.25) # Be polite to the server for detail pages
    return project_content


def scrape_oscars_project_list_and_details():
    """
    Scrapes project titles, URLs from all pages of the OSCARS project site,
    then scrapes details for each project and outputs as JSON.
    """
    base_target_url = "https://oscars-project.eu/projects"
    base_domain_url = "https://oscars-project.eu"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    all_projects_data = []
    page_num = 0
    max_pages_to_scrape = 3 # Safety break for pagination, adjust if needed

    while True:
        if page_num >= max_pages_to_scrape:
            print(f"Reached max pages to scrape ({max_pages_to_scrape}). Stopping pagination.")
            break

        if page_num == 0:
            current_list_url = base_target_url
        else:
            current_list_url = f"{base_target_url}?page={page_num}"

        print(f"\nFetching project list page: {current_list_url}")
        try:
            response = requests.get(current_list_url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404 and page_num > 0:
                print(f"Page {page_num} not found (404). Assuming end of pagination.")
            else:
                print(f"Error fetching project list URL {current_list_url}: {e}")
            break
        except requests.exceptions.RequestException as e:
            print(f"Error fetching project list URL {current_list_url}: {e}")
            break

        soup = BeautifulSoup(response.content, 'lxml')
        main_content_block = soup.find('div', id='block-skeleton-content') or soup.find('div', class_='view-content')
        if not main_content_block:
            print(f"Could not find main project container on {current_list_url}.")
            if page_num == 0:
                return [] # Abort if not found on first page
            break

        project_container = main_content_block.find('div', class_='view-content') or main_content_block
        project_items_on_page = project_container.find_all('div', class_='col-lg-6 mb-4')

        if not project_items_on_page:
            if page_num == 0:
                print("No project items found on the first list page.")
            else:
                print(f"No more project items found on list page {page_num}. Reached end of pagination.")
            break

        print(f"Found {len(project_items_on_page)} project items on this list page. Scraping details...")
        
        for item_container in project_items_on_page:
            anchor_tag = item_container.find('a', class_='card-link')
            if not anchor_tag:
                continue

            title_h5 = anchor_tag.find('h5')
            project_title = "N/A"
            if title_h5:
                title_span = title_h5.find('span', class_='field--name-title')
                project_title = get_text_or_na(title_span or title_h5)
            
            relative_url = anchor_tag.get('href')
            if not relative_url:
                continue
            project_url = urljoin(base_domain_url, relative_url)

            # Scrape details for this project
            project_details_content = scrape_project_details(project_url, project_title, headers)
            
            # Combine list info with detail info
            current_project_data = {
                "Project_Title": project_title,
                "Project_url": project_url,
                "Project_content": project_details_content
            }
            all_projects_data.append(current_project_data)
        
        page_num += 1
        time.sleep(0.5) # Be polite to the server for list pages

    return all_projects_data

if __name__ == '__main__':
    print("Starting OSCARS projects scraper...")
    scraped_data = scrape_oscars_project_list_and_details()
    
    if scraped_data:
        print(f"\n--- Scraping Complete ---")
        print(f"Total projects extracted: {len(scraped_data)}")
        
        # Output as JSON
        output_filename = "oscars_projects_data.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {output_filename}")
        
        # Optional: Print the JSON to console
        # print("\n--- JSON Output ---")
        # print(json.dumps(scraped_data, indent=2, ensure_ascii=False))
    else:
        print("\nNo project data was successfully extracted.")
