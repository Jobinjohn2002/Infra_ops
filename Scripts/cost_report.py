import os
import requests
from azure.identity import DefaultAzureCredential
from datetime import datetime
import json

cred = DefaultAzureCredential()
token = cred.get_token("https://management.azure.com/.default").token
headers = {
    "Authorization": f"Bearer {token}"
}

subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")

if not subscription_id:
    raise ValueError("AZURE_SUBSCRIPTION_ID environment variable not set.")

url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version=2023-03-01"

body = {
    "type": "Usage",
    "timeframe": "MonthToDate",
    "dataset": {
        "granularity": "Daily",
        "aggregation": {
            "totalCost": {
                "name": "PreTaxCost",
                "function": "Sum"
            }
        },
        "grouping": [
            {
                "type": "Dimension",
                "name": "ServiceName"
            }
        ]
    }
}

response = requests.post(url, json=body, headers=headers)

# DEBUG: check if response is successful
if response.status_code != 200:
    print(f"Error: {response.status_code}")
    print("Response content:")
    print(json.dumps(response.json(), indent=2))
    exit(1)

data = response.json()

# Check if 'properties' and 'rows' exist
if "properties" not in data or "rows" not in data["properties"]:
    print("Unexpected response format:")
    print(json.dumps(data, indent=2))
    exit(1)

print("=== Azure Daily Cost Report ===")
for row in data["properties"]["rows"]:
    cost = row[0]
    raw_date = str(row[1])
    service_name = row[2]
    currency = row[3]

    formatted_date = datetime.strptime(raw_date, "%Y%m%d").strftime("%d-%m-%Y")
    print(f"{formatted_date} - {service_name}: {currency} {cost:.2f}")
