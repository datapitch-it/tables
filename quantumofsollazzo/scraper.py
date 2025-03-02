import requests
from bs4 import BeautifulSoup
import time
import re

BASE_URL = "https://buttondown.com/puntofisso/archive"

# Function to extract text from an issue URL and append links correctly
def extract_issue_text(issue_url):
    try:
        response = requests.get(issue_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract main content (adjust selector as needed)
        main_content = soup.find('article') or soup.find('div', class_='content')
        if not main_content:
            return ""

        # Process all links inside the text
        for a_tag in main_content.find_all('a', href=True):
            link = a_tag['href'].split("?")[0]  # Remove tracking params
            text = a_tag.get_text(strip=True)

            if text:  # If anchor has text, append link next to it
                formatted_link = f"{text} ({link})"
            else:  # If anchor has no text, just insert raw URL
                formatted_link = f" ({link})"

            # Replace the <a> tag with the formatted text
            a_tag.replace_with(formatted_link)

        # Preserve original formatting while removing unwanted newlines
        formatted_text = main_content.get_text(separator="\n", strip=True)

        # Remove extra newlines directly following links
        formatted_text = re.sub(r"\)\n+", ")", formatted_text)

        return formatted_text

    except requests.RequestException as e:
        print(f"Error fetching {issue_url}: {e}")
        return ""

# Main function
def main():
    start_issue = 598  # Latest issue number
    end_issue = 550    # Oldest issue to scrape

    with open("extraction.txt", "w", encoding="utf-8") as file:
        for issue_number in range(start_issue, end_issue - 1, -1):
            issue_url = f"{BASE_URL}/{issue_number}-quantum-of-sollazzo/"
            print(f"Trying: {issue_url}")

            issue_content = extract_issue_text(issue_url)

            if issue_content:
                output = (
                    f"\n{'='*80}\n"
                    f"{issue_url}\n"
                    f"{issue_content}\n"
                    f"{'='*80}\n"
                )
                file.write(output)  # Save output to file
            else:
                file.write(f"No content found for {issue_url}\n")

            time.sleep(2)  # Avoid overloading the server

if __name__ == "__main__":
    main()
