import os
import requests
from azure.identity import DefaultAzureCredential
from datetime import datetime

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
    cost = row[0]
    raw_date = str(row[1])
    service_name = row[2]
    currency = row[3]

    # Format the date from YYYYMMDD to DD-MM-YYYY
    formatted_date = datetime.strptime(raw_date, "%Y%m%d").strftime("%d-%m-%Y")

    print(f"{formatted_date} - {service_name}: {currency} {cost:.2f}")
