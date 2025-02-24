import requests
import json

# Replace with your LinkedIn access token
# access_token = 'AQWRbliHoPsnqhiXnoc7MmhLNNzlmtbxGoHglIJwlV-T7hBUpyEML_YhaHxwQQRRYBhYAMo0eqEpK7a84NrSRjQ3LIOEG8c3XkdxC1ICSaPuZCBC84RClkcewkDpCip4wcb9Am8sXoDoefeX3nOh-NjDKk27fZR-4N_j1gwpw9lpunqCQXl2LYgf7ARTl9U0nfOHQgL1rW26oRECvQ1gvsXwe8_7HKFIQZgTPDqD4Kkb-B--64Y-x_VC1KRVlyGPMpwBUBRTN6Mvl07FzQ27nOBARKh4brrl1HxU-pItnTb2XOrCjR7dvmwdusR4ZHpQrY8ffBD6ZtojaqFdmebmt7hPt__evA'

# Member Data Portability
access_token = 'AQVW5LIBWNnzwtPv_N2AE_e9N9Btf8_2DJm6BZAX6uCAOoEeDj7Htrc8XxXqKs256jgIFb3x4cn48VVBl-0jgTipi6hcsCGlH6x4acv6jkP8Qf2BFNDtgGddQWhsQyxbhR-7lr-CX5IJqKNgl5CleKJPISdPvB4jQc6FJcrDjUgk-QRo5GgDR_ZaC4JSSFaaP1wrSk7bnR9Qo-Dyf6qADL7aXOpYvOvMgmD0NE3Dkk7aznP6hfDi0cHT7OGUvmkcgrZfIBrqLe_UVKtpHJspbcRHmLsDaWHViOk6_2r2K5AEpukMRUbCmggXUmTFsmOGdNfUSCD-T-1m4Syx0UrjqhxTj01zjA'

# "sub": "nz-CeibFvN"

# Set the headers
headers = {
    'Authorization': f'Bearer {access_token}',
    'LinkedIn-Version': '202312',
    'Content-Type': 'application/json',
    'X-Restli-Protocol-Version': '2.0.0'
}

# API endpoint
url = 'https://api.linkedin.com/rest/memberSnapshotData'
query_params = {
    "q": "criteria",
    "start": 0,
    "domain": "SHARES",
    "count": 1
}

# Send the request
response = requests.get(url, headers=headers, params = query_params)

# Check if the response was successful
if response.status_code == 200:
    # Prettify the JSON response
    response_json = response.json()
    pretty_response = json.dumps(response_json, indent=4)
    print(pretty_response)
else:
    print(f"Request failed with status code {response.status_code}")
    print(response.text)