import requests
from bs4 import BeautifulSoup
import time
import re
import os

BASE_URL = "https://buttondown.com/puntofisso/archive"
PROCESSED_ISSUES_FILE = "processed_urls.txt"
ERROR_LOG_FILE = "scraping_errors.txt"
OUTPUT_FILE_PREFIX = "extraction"
ISSUES_PER_FILE = 25
MAX_SEQUENTIAL_FETCH_ERRORS = 10

# Function to load processed issue URLs from a file
def load_processed_urls(filepath):
    if not os.path.exists(filepath):
        return set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    except Exception as e:
        print(f"Error loading processed URLs from {filepath}: {e}")
        return set()

# Function to save a processed issue URL to a file
def save_processed_url(filepath, issue_url_to_save):
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(f"{issue_url_to_save}\n")
    except Exception as e:
        print(f"Error saving processed URL {issue_url_to_save} to {filepath}: {e}")

# Function to extract data from an issue URL
def extract_issue_data(issue_url):
    print(f"Fetching: {issue_url}")
    try:
        response = requests.get(issue_url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        main_content = soup.find('article') or soup.find('div', class_='content')
        if not main_content:
            print(f"No main content block found for {issue_url}")
            return "no_content_block", None
        for a_tag in main_content.find_all('a', href=True):
            link = a_tag['href'].split("?")[0]
            text = a_tag.get_text(strip=True)
            formatted_link = f"{text} ({link})" if text else f" ({link})"
            a_tag.replace_with(formatted_link)
        formatted_text = main_content.get_text(separator="\n", strip=True)
        formatted_text = re.sub(r"\)\n+", ")", formatted_text)
        return "success", formatted_text
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            # print(f"Issue not found (404): {issue_url}") # Logging gestito in main
            return "404_error", str(e)
        else:
            # print(f"HTTP error fetching {issue_url}: {e}")
            return "fetch_error", str(e)
    except requests.RequestException as e:
        # print(f"Request error fetching {issue_url}: {e}")
        return "fetch_error", str(e)
    except Exception as e:
        # print(f"An unexpected error occurred while processing {issue_url}: {e}")
        return "fetch_error", str(e)

def ensure_output_file_open_and_ready(
    current_handle,
    issues_in_file_count,
    total_written_this_session, # Num issues scritti in file batch FINORA in questa sessione
    max_issues_per_file,
    file_prefix
):
    """
    Ensures the correct output batch file is open.
    Closes old file if max_issues_per_file is reached and opens a new one.
    Returns the (potentially new) file handle and the reset issue count for that file.
    """
    new_handle = current_handle
    new_issues_in_file_count = issues_in_file_count

    # Se è il primo issue o il file corrente è pieno
    if new_issues_in_file_count == 0 or new_issues_in_file_count >= max_issues_per_file:
        if new_handle and not new_handle.closed:
            print(f"Closing file: {new_handle.name}")
            new_handle.close()

        # Il conteggio per il nome del file parte da 1 (total_written_this_session è 0 per il primo issue)
        batch_start_num = total_written_this_session + 1
        batch_end_num = batch_start_num + max_issues_per_file - 1
        output_filename = f"{file_prefix}_{batch_start_num}-{batch_end_num}.txt"

        print(f"Opening new output file: {output_filename}")
        new_handle = open(output_filename, "a", encoding="utf-8")
        new_issues_in_file_count = 0 # Resetta il conteggio per il nuovo file
    return new_handle, new_issues_in_file_count


# Main function
def main():
    start_issue_number = 488
    processed_urls = load_processed_urls(PROCESSED_ISSUES_FILE)
    print(f"Loaded {len(processed_urls)} processed issue URLs.")
    print(f"Errors and progress will be logged to: {ERROR_LOG_FILE}")

    # Contatori per i file di output batch
    issues_in_current_file = 0
    total_issues_written_this_session = 0 # Totale issue scritti nei file batch in QUESTA sessione

    # Contatori generali
    new_issues_processed_for_report = 0 # Issue "validi" processati per il report finale
    current_issue_number = start_issue_number
    sequential_fetch_errors = 0

    current_output_file_handle = None
    error_file_handle = None

    try:
        error_file_handle = open(ERROR_LOG_FILE, "a", encoding="utf-8")
        error_file_handle.write(f"\n--- Script started at {time.ctime()} ---\n")
        error_file_handle.write(f"Starting from issue number: {start_issue_number}\n")

        while True:
            if sequential_fetch_errors >= MAX_SEQUENTIAL_FETCH_ERRORS:
                message = f"Raggiunto il limite massimo di {MAX_SEQUENTIAL_FETCH_ERRORS} errori di fetch consecutivi. Interruzione."
                print(message)
                error_file_handle.write(f"{time.ctime()}: {message}\n")
                break

            issue_url = f"{BASE_URL}/{current_issue_number}-quantum-of-sollazzo/"

            if issue_url in processed_urls:
                print(f"Issue URL {issue_url} è già processato. Salto.")
                current_issue_number += 1
                sequential_fetch_errors = 0
                time.sleep(0.1) # Breve pausa per non ciclare troppo velocemente sugli skip
                continue

            status, data = extract_issue_data(issue_url)
            save_processed_url(PROCESSED_ISSUES_FILE, issue_url) # Salva l'URL come tentato
            processed_urls.add(issue_url)

            if status == "success" or status == "no_content_block":
                sequential_fetch_errors = 0
                current_output_file_handle, issues_in_current_file = \
                    ensure_output_file_open_and_ready(
                        current_output_file_handle,
                        issues_in_current_file,
                        total_issues_written_this_session, # Passa il totale PRIMA di aggiungere questo
                        ISSUES_PER_FILE,
                        OUTPUT_FILE_PREFIX
                    )

                if status == "success":
                    output_content = (
                        f"\n{'='*80}\n"
                        f"{issue_url}\n"
                        f"{data}\n"
                        f"{'='*80}\n"
                    )
                    current_output_file_handle.write(output_content)
                else: # no_content_block
                    no_content_message = (
                        f"\n{'='*80}\n"
                        f"Nessun contenuto rilevante trovato per {issue_url} (ma la pagina è stata raggiunta)\n"
                        f"{'='*80}\n"
                    )
                    current_output_file_handle.write(no_content_message)

                issues_in_current_file += 1
                total_issues_written_this_session += 1
                new_issues_processed_for_report += 1

            elif status == "404_error":
                message = f"Issue {current_issue_number} (URL: {issue_url}) non trovato (404). Interrompo."
                print(message)
                error_file_handle.write(f"{time.ctime()}: {message} Details: {data}\n")
                break
            elif status == "fetch_error":
                sequential_fetch_errors += 1
                message = f"Errore durante il fetch di {issue_url} (tentativo {sequential_fetch_errors}/{MAX_SEQUENTIAL_FETCH_ERRORS})"
                print(message)
                error_file_handle.write(f"{time.ctime()}: {message}. Details: {data}\n")
            else: # Status sconosciuto
                sequential_fetch_errors += 1
                message = f"Status sconosciuto '{status}' per {issue_url}. Trattato come errore di fetch."
                print(message)
                error_file_handle.write(f"{time.ctime()}: {message}\n")

            current_issue_number += 1
            time.sleep(2)

    except IOError as e:
        io_err_msg = f"Errore di I/O: {e}"
        print(io_err_msg)
        if error_file_handle and not error_file_handle.closed:
            error_file_handle.write(f"{time.ctime()}: CRITICAL IO ERROR: {io_err_msg}\n")
    except Exception as e:
        gen_err_msg = f"Errore imprevisto nella funzione main: {e}"
        print(gen_err_msg)
        import traceback
        traceback.print_exc()
        if error_file_handle and not error_file_handle.closed:
            error_file_handle.write(f"{time.ctime()}: CRITICAL UNEXPECTED ERROR: {gen_err_msg}\n{traceback.format_exc()}\n")
    finally:
        if current_output_file_handle and not current_output_file_handle.closed:
            print(f"Closing final output file: {current_output_file_handle.name}")
            current_output_file_handle.close()
        if error_file_handle and not error_file_handle.closed:
            error_file_handle.write(f"--- Script finished at {time.ctime()} ---\n")
            error_file_handle.close()
            print(f"Error log updated: {ERROR_LOG_FILE}")

    print(f"\nOperazione completata.")
    print(f"Processati e scritti {new_issues_processed_for_report} nuovi issue in file batch in questa sessione.")
    print(f"Totale issue URLs nel file di tracciamento ({PROCESSED_ISSUES_FILE}): {len(load_processed_urls(PROCESSED_ISSUES_FILE))}")

if __name__ == "__main__":
    main()
