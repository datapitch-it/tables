#!/bin/bash

# Array of models
models=(
    "gemini-pro"
    "gemini-1.5-pro-latest"
    "gemini-1.5-flash-latest"
    "gemini-1.5-pro-001"
    "gemini-1.5-flash-001"
    "gemini-1.5-pro-002"
    "gemini-1.5-flash-002"
    "gemini-1.5-flash-8b-latest"
    "gemini-1.5-flash-8b-001"
    "gemini-exp-1114"
    "gemini-exp-1121"
    "gemini-exp-1206"
    "gemini-2.0-flash-exp"
    "gemini-2.0-flash-thinking-exp-1219"
    "gemini-2.0-flash-thinking-exp-01-21"
    "gemini-2.0-flash"
    "gemini-2.0-pro-exp-02-05"
    "gemini-2.0-flash-lite"
    "gemini-2.5-pro-exp-03-25"
)

# Loop through each model
for model in "${models[@]}"
do
    echo "Processing model: $model"
    output_file="${model}.json"
    curl -s "https://edmo.eu/about-us/edmo-hubs/" | pup 'body text{}' | llm -m "$model" "Given the text, first extract the list of diverse observatories, the for each add: 1) Coordinating Institution, 2) Countries covered, 3) Consortium partners, 4) website (href attr from tag <a>" --schema 'Observatory name, Coordinating Instituion, Countries covered, Consortium Partners, website' -o json_object true > "$output_file"
    echo "Output saved to $output_file"
done
