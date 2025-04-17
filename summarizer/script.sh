#!/bin/bash

# Debugging: Print a message indicating the start of the script
echo "Starting script execution..."

# Legge gli URL dal file sources.txt
while IFS= read -r url; do
    # Debugging: Print each URL being read from sources.txt
    echo "Reading URL: $url"

    # Esegui la pipeline
    echo "Fetching and processing URL: $url"

    # Debugging: Capture the output of the curl command
    curl_output=$(curl -s "$url")
    echo "Curl output: $curl_output"

    # Debugging: Capture the output of the pup command
    pup_output=$(echo "$curl_output" | pup 'body text{}')
    echo "Pup output: $pup_output"

    # Debugging: Capture the output of the llm command
    llm_output=$(echo "$pup_output" | llm -m gemini --schema 'source_name, source_url, source_generated_summary' "given the text, generate json item with source name, source input url (example: https://www.wheresyoured.at/power-cut/?ref=ed-zitrons-wheres-your-ed-at-newsletter), source summary generated in Italian with a maximum of 300 tokens. No symbols, no markdown" -o json_object true)
    echo "LLM output: $llm_output"

    # Append the output to datacenter.json
    echo "$llm_output" >> datacenter.json

    # Debugging: Confirm the data has been appended to datacenter.json
    echo "Appended data to datacenter.json for URL: $url"

    # Generate a random sleep time between 2 and 9 seconds
    random_sleep_time=$(shuf -i 2-9 -n 1)

    # Add a random delay to avoid overwhelming the server
    echo "Pausing for $random_sleep_time seconds before the next request..."
    sleep $random_sleep_time
done < sources.txt

# Debugging: Print a message indicating the end of the script
echo "Script execution completed."

