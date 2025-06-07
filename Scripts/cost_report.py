import os
import requests
from azure.identity import DefaultAzureCredential

cred = DefaultAzureCredential()
token = cred.get_token("https://management.azure.com/.default").token
headers = {
    "Authorization": f"Bearer {token}"
}

subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"]

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
data = response.json()

print("=== Azure Daily Cost Report ===")
for row in data["properties"]["rows"]:
    print(row)  # Add this to see what's inside
    service_name = row[0]
    cost = row[1]
    print(f"{service_name}: ₹{cost:.2f}")
