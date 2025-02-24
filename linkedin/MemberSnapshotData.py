import requests
import json

# Replace with your LinkedIn access token
# access_token = 'AQWRbliHoPsnqhiXnoc7MmhLNNzlmtbxGoHglIJwlV-T7hBUpyEML_YhaHxwQQRRYBhYAMo0eqEpK7a84NrSRjQ3LIOEG8c3XkdxC1ICSaPuZCBC84RClkcewkDpCip4wcb9Am8sXoDoefeX3nOh-NjDKk27fZR-4N_j1gwpw9lpunqCQXl2LYgf7ARTl9U0nfOHQgL1rW26oRECvQ1gvsXwe8_7HKFIQZgTPDqD4Kkb-B--64Y-x_VC1KRVlyGPMpwBUBRTN6Mvl07FzQ27nOBARKh4brrl1HxU-pItnTb2XOrCjR7dvmwdusR4ZHpQrY8ffBD6ZtojaqFdmebmt7hPt__evA'

# Member Data Portability
access_token = 'AQVW5LIBWNnzwtPv_N2AE_e9N9Btf8_2DJm6BZAX6uCAOoEeDj7Htrc8XxXqKs256jgIFb3x4cn48VVBl-0jgTipi6hcsCGlH6x4acv6jkP8Qf2BFNDtgGddQWhsQyxbhR-7lr-CX5IJqKNgl5CleKJPISdPvB4jQc6FJcrDjUgk-QRo5GgDR_ZaC4JSSFaaP1wrSk7bnR9Qo-Dyf6qADL7aXOpYvOvMgmD0NE3Dkk7aznP6hfDi0cHT7OGUvmkcgrZfIBrqLe_UVKtpHJspbcRHmLsDaWHViOk6_2r2K5AEpukMRUbCmggXUmTFsmOGdNfUSCD-T-1m4Syx0UrjqhxTj01zjA'

# Set the headers
headers = {
    'Authorization': f'Bearer {access_token}',
    'LinkedIn-Version': '202312',
    'Content-Type': 'application/json',
    'X-Restli-Protocol-Version': '2.0.0'
}

# API endpoint
url = 'https://api.linkedin.com/rest/memberSnapshotData'

# List of domains
domains = [
    "ACCOUNT_HISTORY", "ADS_CLICKED", "MEMBER_FOLLOWING", "LOGIN", "RICH_MEDIA", "SEARCHES",
    "INFERENCE_TAKEOUT", "MEMBER_HASHTAG", "ALL_COMMENTS", "ALL_LIKES", "GROUP_POSTS", "NAME_CHANGES",
    "CONTACTS", "EVENTS", "RECEIPTS", "AD_TARGETING", "REGISTRATION", "REVIEWS", "SAVED_PEOPLE_SEARCHES",
    "ARTICLES", "PATENTS", "GROUPS", "COMPANY_FOLLOWS", "INVITATIONS", "PHONE_NUMBERS", "CONNECTIONS",
    "EMAIL_ADDRESSES", "JOB_POSTINGS", "JOB_APPLICATIONS", "JOB_SEEKER_PREFERENCES", "LEARNING", "INBOX",
    "SAVED_JOBS", "SAVED_JOB_ALERTS", "PROFILE", "SKILLS", "POSITIONS", "EDUCATION", "TEST_SCORES",
    "CAUSES_YOU_CARE_ABOUT", "PUBLICATIONS", "PROJECTS", "ORGANIZATIONS", "LANGUAGES", "HONORS",
    "COURSES", "CERTIFICATIONS", "CALENDAR", "RECOMMENDATIONS", "ENDORSEMENTS", "VOLUNTEERING", "SHARES"
]

# Object to hold the entire response data
all_data = {}

# Loop through the domains and make requests
for domain in domains:
    query_params = {
        "q": "criteria",
        "start": 0,
        "domain": domain
    }

    print(f"Fetching data for domain: {domain}")
    response = requests.get(url, headers=headers, params=query_params)

    if response.status_code == 200:
        response_json = response.json()
        all_data[domain] = response_json
        pretty_response = json.dumps(response_json, indent=4)
        print(pretty_response)
    else:
        print(f"Failed to fetch data for domain: {domain}")
        print(f"Status Code: {response.status_code}")
        print(response.text)

# Save the entire output to a JSON file
with open('./fullexport.json', 'w') as outfile:
    json.dump(all_data, outfile, indent=4)

print("Export completed! Data saved to './fullexport.json'")