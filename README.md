```markdown
# Azure Web App CPU Alert and Auto-Recovery Runbook

This runbook details the process for responding to an Azure Monitor alert indicating high CPU usage (above 10%) on an Azure Web App and outlines the automated recovery process using an Azure Function that restarts the Web App.

## 1. Alert Definition

*   **Alert Name:** WebApp CPU Usage High
*   **Signal:** CPU Percentage
*   **Threshold:** > 10%
*   **Aggregation Type:** Average
*   **Aggregation Granularity:** 5 minutes
*   **Action Group:**  AlertActionGroup (includes email notification to the on-call team and triggers the Auto-Remediation Function)
*   **Resource:** [Specify your Web App Resource Name]

## 2. Symptoms

*   **End-User Impact:**
    *   Slow web page loading times.
    *   Application unresponsiveness.
    *   Possible application errors (e.g., 503 Service Unavailable).
    *   Increased latency for API calls.
*   **Monitoring Dashboard:**
    *   Elevated CPU usage reported in Azure Monitor metrics for the Web App.
    *   Potential spikes in error rates or latency metrics.
    *   Increased queue lengths in connected services (e.g., Azure Service Bus).
*   **Logs:**
    *   Warning or error messages in the Web App's application logs indicating performance bottlenecks.
    *   Slow query logs in associated databases.
    *   Increased request durations in Application Insights (if integrated).

## 3. Troubleshooting

Before the auto-remediation kicks in, quickly assess the situation.  Keep this brief as the system is designed to auto-recover.

1.  **Verify the Alert:** Ensure the alert is still active and hasn't resolved itself.  Check the Azure Monitor alert history.
2.  **Quick CPU Usage Check:**  Use Azure Portal or Azure CLI to view real-time CPU usage.

    *   **Azure Portal:** Navigate to the Web App in the Azure Portal.  Go to "Metrics" and select "CPU Percentage." Set the time range to the last 15 minutes.
    *   **Azure CLI:**
        ```bash
        az monitor metrics list --resource [Resource ID of WebApp] --metric "CpuPercentage" --aggregation "Average" --interval PT5M --timespan PT15M
        ```
3.  **Check Related Resources:** Briefly check the health and performance of dependent services (e.g., database, cache).  High CPU usage in the Web App could be a symptom of a problem elsewhere.

## 4. Auto-Remediation

This section describes the Azure Function responsible for automatically restarting the Web App.

### 4.1. Azure Function Details

*   **Function Name:** WebAppRestartFunction
*   **Function Type:** HTTP Trigger
*   **Authorization Level:** Function
*   **Identity:** Managed Identity enabled, with the 'Contributor' role assigned to the Web App resource group.
*   **Code (Example - Python):**

    ```python
    import logging
    import azure.functions as func
    import azure.mgmt.web.models as web_models
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.web import WebSiteManagementClient
    import os

    def main(req: func.HttpRequest) -> func.HttpResponse:
        logging.info('Python HTTP trigger function processed a request.')

        # Retrieve function key (or other authentication method)
        function_key = os.environ.get("WebAppRestartFunction_CODE")
        if not function_key:
            return func.HttpResponse(
                 "Please pass a function key in the request headers.",
                 status_code=400
            )

        # Verify function key
        if req.headers.get("x-functions-key") != function_key:
            return func.HttpResponse(
                 "Invalid function key.",
                 status_code=401
            )


        try:
            # Azure Resource Details (retrieve from environment variables for better config)
            subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"] # e.g., "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            resource_group_name = os.environ["RESOURCE_GROUP_NAME"] # e.g., "my-resource-group"
            web_app_name = os.environ["WEB_APP_NAME"] # e.g., "mywebapp"

            # Authenticate using Managed Identity
            credential = DefaultAzureCredential()

            # Create WebSiteManagementClient
            web_client = WebSiteManagementClient(credential, subscription_id)

            # Restart the Web App
            web_client.web_apps.restart(resource_group_name, web_app_name)
            logging.info(f"Web App '{web_app_name}' restarted successfully.")

            return func.HttpResponse(
                 f"Web App '{web_app_name}' restarted successfully.",
                 status_code=200
            )

        except Exception as e:
            logging.error(f"Error restarting Web App: {e}")
            return func.HttpResponse(
                 f"Error restarting Web App: {e}",
                 status_code=500
            )


    if __name__ == "__main__":
        # This section is for local testing only.  Set environment variables before running.
        #  Example: export AZURE_SUBSCRIPTION_ID="YOUR_SUBSCRIPTION_ID"
        import os
        os.environ["AZURE_SUBSCRIPTION_ID"] = "YOUR_SUBSCRIPTION_ID"
        os.environ["RESOURCE_GROUP_NAME"] = "YOUR_RESOURCE_GROUP"
        os.environ["WEB_APP_NAME"] = "YOUR_WEB_APP_NAME"
        os.environ["WebAppRestartFunction_CODE"] = "YOUR_FUNCTION_KEY" # Important for testing locally


        # Create a dummy HttpRequest object for testing
        class MockHttpRequest:
            def __init__(self, headers={}):
                self.headers = headers

        req = MockHttpRequest(headers={"x-functions-key": os.environ["WebAppRestartFunction_CODE"]})
        response = main(req)
        print(response.get_body())
        print(response.status_code)

    ```

    **Important considerations for the Azure Function:**

    *   **Function Key Security:** The function key provides authorization.  Treat it like a password. Rotate it periodically and protect it.  Store it securely in Azure Key Vault and retrieve it as an environment variable.
    *   **Environment Variables:** Store the `AZURE_SUBSCRIPTION_ID`, `RESOURCE_GROUP_NAME`, `WEB_APP_NAME`, and `WebAppRestartFunction_CODE` as application settings in the Function App configuration. This makes the function more portable and easier to manage. *Do not hardcode these values in the script.*
    *   **Managed Identity:**  Enabling a managed identity is the recommended authentication method for accessing Azure resources from Azure Functions. Assign the necessary role (e.g., 'Contributor') to the managed identity.  This eliminates the need to store credentials in your code or configuration.
    *   **Error Handling:**  Implement robust error handling to catch exceptions and log them appropriately.  Consider adding retry logic for transient errors.
    *   **Logging:**  Use the `logging` module to log important events, such as the start and end of the function execution, and any errors that occur.  This will help you troubleshoot issues.
    *   **Idempotency:** Restarting a Web App is typically idempotent.  However, consider adding logic to prevent the function from being executed multiple times in rapid succession if the alert fires repeatedly. You can use Azure Durable Functions or a distributed lock for this.
*   **Function Trigger:** HTTP trigger with a function key for authentication.
*   **Dependencies:** Requires the `azure-functions`, `azure-mgmt-web`, `azure-identity` and `azure-mgmt-core` Python packages.  Use a `requirements.txt` file for managing dependencies:

    ```
    azure-functions
    azure-mgmt-web
    azure-identity
    azure-mgmt-core
    ```

### 4.2. Action Group Configuration

The Action Group triggered by the Azure Monitor alert should be configured as follows:

*   **Actions:**
    *   **Action Type:** Azure Function
    *   **Function App:** [Your Function App Name]
    *   **Function:** WebAppRestartFunction
    *   **HTTP Request Body:**  (Optional - you can leave this blank as the function retrieves the necessary parameters from environment variables) A JSON payload can be passed, but it's usually not necessary when the Function is configured with environment variables.
    *   **Use common alert schema:** Yes

### 4.3. Expected Outcome

The Azure Function, when triggered, will restart the Web App. This will typically resolve the high CPU issue by clearing the process memory and restarting the application pool.

## 5. Verification

After the auto-remediation is triggered, verify the following:

1.  **Function Execution Success:** Check the logs of the Azure Function (WebAppRestartFunction) in the Azure Portal to confirm that the function executed successfully.
2.  **Web App Status:**  Confirm that the Web App has been restarted. In the Azure Portal, navigate to the Web App and check the "Overview" section.  The "Status" should indicate that the Web App is running.
3.  **CPU Usage Reduction:** Monitor the CPU usage of the Web App in Azure Monitor.  The CPU usage should return to normal levels (below the alert threshold of 10%) within a reasonable timeframe (e.g., 5-10 minutes).  Use the same Azure Portal/CLI commands from the Troubleshooting section to verify.
4.  **Application Functionality:**  Test the application's core functionalities (e.g., loading key pages, submitting forms) to ensure that the restart did not introduce any new issues.

## 6. Logs

*   **Azure Monitor Logs:**
    *   **Web App Logs:** Examine the Web App's application logs for any errors or warnings that occurred before the alert and after the restart.  Look for patterns or recurring issues that may be contributing to the high CPU usage. Access via App Service Logs.
    *   **Azure Function Logs:** Review the logs of the Azure Function (WebAppRestartFunction) to confirm successful execution and identify any errors.  Access via Monitor -> Logs in the Function App.
    *   **Azure Activity Log:** Review the Azure Activity Log for events related to the Web App restart. This log can be accessed through the Azure Portal's "Activity Log" blade.
*   **Application Insights (if integrated):**
    *   Examine performance metrics (e.g., request duration, exceptions) for the Web App.
    *   Analyze traces to identify slow or problematic code paths.

## 7. Escalation

If the auto-remediation fails to resolve the issue or if the high CPU usage persists after the Web App restart:

1.  **Escalate to the On-Call Engineer:** The Action Group should include an email notification to the on-call team if the alert remains active for a specified period (e.g., 15 minutes) after the auto-remediation is triggered.
2.  **Provide Context:**  The on-call engineer should have access to the following information:
    *   The alert details (including the threshold and time of occurrence).
    *   The results of the initial troubleshooting steps.
    *   The logs from the Azure Function and the Web App.

## 8. Post-Incident Analysis

After the incident is resolved, conduct a post-incident analysis to:

1.  **Identify the Root Cause:** Determine the underlying cause of the high CPU usage.  This may require further investigation of the application code, database queries, or infrastructure.
2.  **Prevent Future Occurrences:** Implement measures to prevent similar incidents from occurring in the future.  This may include:
    *   Optimizing application code.
    *   Tuning database queries.
    *   Increasing the resources allocated to the Web App (e.g., scaling up to a larger App Service Plan).
    *   Implementing caching mechanisms.
    *   Adding or improving monitoring and alerting.
3.  **Improve the Runbook:** Update this runbook with any lessons learned from the incident.

## 9. Testing

*   **Simulate High CPU:** Use a load testing tool or inject a CPU-intensive task into the Web App to simulate high CPU usage.
*   **Verify Alert Trigger:** Ensure that the Azure Monitor alert is triggered when the CPU usage exceeds the threshold.
*   **Confirm Auto-Remediation:** Verify that the Azure Function is triggered by the alert and that it successfully restarts the Web App.
*   **Monitor Recovery:** Monitor the CPU usage of the Web App after the restart to ensure that it returns to normal levels.
*   **Test Escalation:** Verify that the email notification is sent to the on-call team if the auto-remediation fails.

By implementing this runbook and automating the recovery process, you can quickly respond to high CPU usage issues in your Azure Web App and minimize the impact on your users.  Remember to regularly review and update this runbook to reflect changes in your application and infrastructure.
```

## Architecture Diagram (Mermaid)
```mermaid
```mermaid
graph LR
    subgraph Azure Resources
      A[WebApp (App Service)]
      B[Azure Monitor (Alert Rule)]
      C[Action Group]
      D[Function App (HTTP Trigger)]
      E[Logic App (Optional)]
    end

    A --> B: CPU Usage
    B --> C: Alert (CPU > 10%)
    C --> D: Triggers (HTTP Request)
    D --> A: Restarts WebApp
    C --> E: Optional: Triggers
    E --> D: Optional: Orchestration

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#ccf,stroke:#333,stroke-width:2px
    style C fill:#ccf,stroke:#333,stroke-width:2px
    style D fill:#f9f,stroke:#333,stroke-width:2px
    style E fill:#ccf,stroke:#333,stroke-width:2px

    subgraph Notes
    F[CPU usage monitored by Azure Monitor\nAlert triggers when threshold exceeded (10%)]
    G[Action Group configured to trigger Function App]
    H[Function App receives HTTP request and restarts WebApp]
    I[Logic App (optional) can add\ncomplex orchestration logic]
    end

    linkStyle 0,1,2,3,4 stroke-width:2px,stroke:#333,color:black;
```

**Explanation:**

*   **Azure Resources:**  This subgraph groups all the Azure components used in the monitoring and remediation solution.
*   **WebApp (App Service):**  The target web application we want to monitor and restart.  Styled with a light pink fill to represent a PaaS resource.
*   **Azure Monitor (Alert Rule):**  This service continuously monitors the WebApp's CPU usage. An alert rule is configured to trigger when the CPU usage exceeds a predefined threshold (10% in this example).  Styled with light blue fill representing a monitoring service.
*   **Action Group:** When the Azure Monitor alert is triggered, it sends a notification to the Action Group. The Action Group is configured to trigger the Function App via an HTTP request.  Styled with light blue fill representing a configuration/management service.
*   **Function App (HTTP Trigger):** This serverless function receives the HTTP request from the Action Group.  The function code then restarts the WebApp using the Azure SDK (or Azure CLI). Styled with a light pink fill to represent a PaaS/compute resource.
*   **Logic App (Optional):** A Logic App can be optionally used to provide more complex orchestration. For example, before restarting the WebApp, it could send a notification, check other resources, or perform a rolling restart across multiple instances. Styled with light blue fill representing a workflow service.
*   **Arrows:** The arrows indicate the flow of events and actions:
    *   WebApp CPU usage is monitored by Azure Monitor.
    *   Azure Monitor triggers an alert when the CPU exceeds 10%.
    *   The alert sends a notification to the Action Group.
    *   The Action Group triggers the Function App.
    *   The Function App restarts the WebApp.
    *   Optionally, the Action Group can trigger a Logic App for more complex orchestration, which then calls the Function App.
*   **Notes:** The Notes subgraph provides additional context and explanation for each component and its role in the solution.

**Key improvements and considerations:**

*   **Clearer Arrows and Flow:**  The arrow directions explicitly show the data flow and the triggering events.
*   **Consistent Styling:** All resources have a defined style, making the diagram easier to read.
*   **Optional Logic App:**  The Logic App is correctly shown as an optional component, and its role in orchestration is described.
*   **Detailed Notes:**  The notes section provides explanations for each component and the configuration required.  This helps understanding the purpose of each element.
*   **Azure Resource Styling:** Uses consistent styling for Azure Monitor and Action Groups (management) and WebApp and Function App (PaaS/Compute).

This improved diagram provides a more complete and understandable representation of the Azure WebApp monitoring and auto-remediation solution. Remember to install the Mermaid extension in your code editor or use an online Mermaid editor to render the diagram.
```
