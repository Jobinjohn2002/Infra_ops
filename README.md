```markdown
# Azure WebApp High CPU Usage Alert & Auto-Recovery Runbook

**Purpose:** This runbook outlines the steps to diagnose and remediate a high CPU usage alert for an Azure WebApp, leveraging an Azure Function for automatic restart.  The alert threshold is set at 10% CPU usage.

**Scope:** This runbook applies to Azure WebApps exhibiting sustained CPU usage above 10%.

**Assumptions:**

*   An Azure Monitor alert is configured to trigger when the WebApp's CPU Percentage metric exceeds 10% for a defined period (e.g., 5 minutes).
*   An Azure Function is deployed with the necessary permissions to restart the target WebApp.
*   The Azure Function app service principal has the "Contributor" role on the resource group or web app.
*   Application Insights is enabled for both the WebApp and the Azure Function.
*   This runbook assumes a simple restart-based auto-recovery approach.  More sophisticated solutions (e.g., scaling out, code profiling) may be required for persistent issues.

## 1. Alert Symptoms

*   **Azure Monitor Alert:** A notification is received indicating high CPU usage (above 10%) for the WebApp.  The alert details should include the WebApp name, resource group, and timestamp of the alert.
*   **Slow Application Performance:** Users may experience slow response times, timeouts, or general unresponsiveness when accessing the WebApp.
*   **Increased Latency:** Monitoring tools might show increased latency for API calls or database queries.
*   **Application Errors:**  In extreme cases, the application might throw exceptions or experience crashes due to resource exhaustion.
*   **Decreased Throughput:** The number of requests the WebApp can handle per second may decrease.

## 2. Initial Troubleshooting

Before relying on auto-remediation, perform these initial checks to gain a better understanding of the situation:

*   **2.1. Review Azure Monitor Alert Details:**
    *   **Timestamp:**  Note the time when the alert triggered. This is crucial for correlating with logs.
    *   **WebApp Name and Resource Group:**  Confirm the affected WebApp.
    *   **Metric Values:** Review the CPU Percentage values leading up to the alert.  Was it a sudden spike or a gradual increase?
    *   **Alert Rule Configuration:** Verify the alert rule is correctly configured (threshold, evaluation period, etc.).

*   **2.2. Check Azure Portal Metrics:**
    *   **WebApp Metrics:**  Navigate to the Azure Portal -> App Services -> [Your WebApp] -> Monitoring -> Metrics.
    *   **Important Metrics:**
        *   **CPU Percentage:** (Verify the reported value matches the alert).
        *   **Memory Percentage:**  High memory usage can contribute to CPU pressure.
        *   **Requests:**  Look for a spike in the number of requests that could be overloading the WebApp.
        *   **Data In/Out:**  Check for excessive network traffic that could be a bottleneck.
        *   **HTTP Errors:** (4xx, 5xx) -  Increased error rates can indicate underlying issues causing high CPU.
        *   **Threads:** (If available) - High thread count can point to resource contention.
        *   **Connections:**  Excessive connections might overload the WebApp.
        *   **Process CPU:** A single process may be consuming the CPU

*   **2.3. Examine Application Insights Logs:**
    *   Navigate to Azure Portal -> App Services -> [Your WebApp] -> Monitoring -> Application Insights.
    *   **Live Metrics Stream:** Use Live Metrics Stream to get a near real-time view of CPU usage, request rates, and other metrics.
    *   **Performance Blade:** Analyze the Performance blade to identify slow requests, dependencies, and database queries that might be contributing to high CPU usage.
    *   **Failures Blade:** Investigate any recent exceptions or errors.  Stack traces can provide clues about the root cause.
    *   **Logs (Analytics):** Use Kusto Query Language (KQL) to query the logs.  Here are some useful queries:

        ```kusto
        // CPU usage over time
        performanceCounters
        | where counterName == "% Processor Time"
        | summarize avg(counterValue) by bin(timestamp, 1m)
        | render timechart

        // Top operations by duration
        traces
        | where timestamp > ago(1h)
        | summarize avg(duration) by operation_Name
        | top 10 by avg_duration desc

        // Exceptions
        exceptions
        | where timestamp > ago(1h)
        | summarize count() by type, details
        | order by count_ desc
        ```

*   **2.4. Investigate Kudu Console (Advanced)**
    *   Access the Kudu console:  `https://<your-webapp-name>.scm.azurewebsites.net/`
    *   **Process Explorer:**  Use the Process Explorer to identify specific processes consuming high CPU.  This can help pinpoint the source of the problem (e.g., a specific application component, a background process, etc.).
    *   **Memory Dump (Use with Caution):**  If you suspect a memory leak, you can create a memory dump using Kudu.  Analyze the dump with tools like WinDbg or Visual Studio to identify the source of the leak. *Note: Memory dumps can contain sensitive information. Handle them securely.*
    *   **Environment Variables:**  Verify the configured environment variables are correct. Incorrect configurations can lead to performance issues.

## 3. Auto-Remediation

The following steps describe the automated recovery process using an Azure Function.

*   **3.1. Trigger:** The Azure Monitor alert triggers the Azure Function.
*   **3.2. Azure Function Code:**  The Azure Function should contain code similar to the following (Python example using `azure-mgmt-web`):

```python
import logging
import os
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Retrieve WebApp details from the request (populated by the Alert Rule)
    resource_group_name = req.params.get('resource_group_name')
    web_app_name = req.params.get('web_app_name')
    subscription_id = os.environ["SUBSCRIPTION_ID"] # store as an env var


    if not resource_group_name or not web_app_name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            resource_group_name = req_body.get('resource_group_name')
            web_app_name = req_body.get('web_app_name')

    if not resource_group_name or not web_app_name:
        return func.HttpResponse(
             "Please pass resource_group_name and web_app_name in the request",
             status_code=400
        )

    try:
        # Authenticate using Managed Identity (or other appropriate credentials)
        credential = DefaultAzureCredential()

        # Create a WebSiteManagementClient
        web_client = WebSiteManagementClient(credential, subscription_id)

        # Restart the WebApp
        web_client.web_apps.restart(resource_group_name, web_app_name)

        logging.info(f'Restarted WebApp: {web_app_name} in resource group: {resource_group_name}')

        return func.HttpResponse(
             f"WebApp {web_app_name} in resource group {resource_group_name} restarted successfully.",
             status_code=200
        )

    except Exception as e:
        logging.error(f"Error restarting WebApp: {e}")
        return func.HttpResponse(
             f"Error restarting WebApp: {e}",
             status_code=500
        )
```

*   **3.3. Alert Rule Configuration:** Configure the Azure Monitor alert to trigger the Azure Function using a Webhook action.
    *   **Webhook URL:** The HTTP trigger URL of your Azure Function.  Include the function access key (if required).
    *   **Payload (JSON):**  The payload sent to the Azure Function should include the WebApp name and Resource Group.  Customize the payload based on your alert rule configuration and Function parameters.  Example:

    ```json
    {
      "resource_group_name": "{{resourceGroupName}}",
      "web_app_name": "{{resourceName}}"
    }
    ```

*   **3.4. Post-Restart Checks:** After the Function restarts the WebApp, monitor the CPU usage and application performance to verify the issue is resolved.

## 4. Logs

*   **4.1. Azure Function Logs:**  Monitor the logs of the Azure Function app in Azure Portal -> Function App -> [Your Function App] -> Monitoring -> Logs (Application Insights). This will show if the Function executed successfully and any errors that occurred.  Use KQL queries to analyze the Function's execution time and success rate.
    *   Example KQL query:

        ```kusto
        traces
        | where operation_Name == "Functions.main"
        | summarize count(), avg(duration) by success
        ```

*   **4.2. WebApp Application Insights Logs:**  Continue monitoring the WebApp's Application Insights logs to ensure the high CPU issue does not reoccur.  Use the queries from section 2.3 to identify any persistent problems.  Look for correlations between the restart event and changes in application performance.
*   **4.3. Azure Activity Log:** Review the Azure Activity Log (Azure Portal -> Monitor -> Activity Log) to verify the restart action was initiated by the Azure Function and to audit any other related events.
*   **4.4. Web Server Logs:** Access the web server logs for the WebApp.  This can be found under App Service -> Monitoring -> Log stream or through the Kudu console.  Look for error messages, slow requests, or other indicators of problems.

## 5. Manual Intervention (If Auto-Remediation Fails)

If the auto-remediation fails (e.g., the Azure Function errors out, the WebApp doesn't restart, or the high CPU persists), perform the following steps:

*   **5.1.  Restart the WebApp Manually:**  Restart the WebApp directly from the Azure Portal (App Service -> [Your WebApp] -> Restart).  This can help isolate the issue.
*   **5.2. Scale Up/Out the App Service Plan:**  Increase the resources allocated to the App Service Plan (e.g., upgrade to a larger instance size or add more instances).  This provides the WebApp with more CPU and memory.
*   **5.3. Diagnose with Diagnostics Tools:**  Use the built-in diagnostic tools in the Azure Portal (App Service -> [Your WebApp] -> Diagnose and solve problems). These tools can help identify common issues like memory leaks, high CPU usage, or database connectivity problems.
*   **5.4. Enable Profiling:** Enable the profiler in Application Insights to identify specific code paths that are consuming high CPU.
*   **5.5. Code Review:** Review the application code for potential performance bottlenecks, inefficient algorithms, or memory leaks.  Pay particular attention to any code that has been recently deployed.
*   **5.6. Contact Support:** If the issue persists after trying the above steps, contact Azure support for assistance.  Provide them with all the collected logs and diagnostic information.

## 6. Preventative Measures

*   **6.1. Code Optimization:** Regularly review and optimize the application code for performance.  Use profiling tools to identify and address bottlenecks.
*   **6.2. Monitoring and Alerting:**  Fine-tune the alert rules and monitoring dashboards to provide early warnings of potential issues.  Add alerts for other critical metrics like memory usage, HTTP errors, and database performance.
*   **6.3. Auto-Scaling:** Implement auto-scaling to automatically scale out the WebApp based on CPU usage or other metrics.
*   **6.4. Resource Limits:**  Set resource limits (CPU and memory) for the WebApp to prevent it from consuming excessive resources and impacting other applications.
*   **6.5. Load Testing:**  Regularly perform load testing to identify performance issues and ensure the WebApp can handle expected traffic.
*   **6.6. Dependency Analysis:**  Analyze the application's dependencies and ensure they are properly configured and optimized.
*   **6.7. Azure Advisor Recommendations:** Regularly review Azure Advisor recommendations for performance and cost optimization.

## 7. Rollback Plan

If the remediation steps cause further issues, revert the changes made and restore the WebApp to its previous state.

*   **Rollback Scaling Changes:**  If the App Service Plan was scaled up or out, revert to the original configuration.
*   **Rollback Code Deployments:**  If a recent code deployment is suspected, revert to the previous version.  Use deployment slots for safe deployment and rollback.

## 8. Known Issues and Workarounds

*   **Intermittent CPU Spikes:**  Transient CPU spikes can sometimes occur due to background tasks or garbage collection.  If these spikes are infrequent and short-lived, they may not require immediate action. Consider increasing the alert threshold or evaluation period to avoid false positives.
*   **Dependency Issues:**  Problems with external dependencies (e.g., databases, APIs) can cause high CPU usage.  Monitor the health and performance of dependencies and implement appropriate error handling and retry logic.
*   **Memory Leaks:**  Memory leaks can lead to gradual increases in CPU usage over time.  Use memory profiling tools to identify and fix memory leaks.
*   **Alert Rule Configuration Errors:**  Incorrectly configured alert rules can lead to false positives or missed alerts.  Review the alert rule configuration regularly.

This runbook provides a starting point for addressing high CPU usage in Azure WebApps.  Adapt it to your specific environment and application requirements. Remember to document any changes or additions made to the runbook.
```

## Architecture Diagram (Mermaid)
```mermaid
```mermaid
graph LR
    subgraph Azure Subscription
    A[App Service - MyWebApp] -- Monitors CPU --> B(Azure Monitor - CPU High Usage)
    B -- Triggers --> C(Action Group - Restart App)
    C -- Invokes --> D[Function App - RestartWebAppFunc]
    D -- Restarts --> A
    end

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#ccf,stroke:#333,stroke-width:2px
    style C fill:#ccf,stroke:#333,stroke-width:2px
    style D fill:#f9f,stroke:#333,stroke-width:2px

    subgraph Alternative - Logic App
        E[Action Group - Restart App (Alternative)] --> F[Logic App - Orchestrate Restart]
        F -- Restarts --> A
        style E fill:#ccf,stroke:#333,stroke-width:2px
        style F fill:#ccf,stroke:#333,stroke-width:2px
        linkStyle 1,2,3,4,5,6 stroke-dasharray: 5 5;
    end

    C -- Invokes (Alternatively) --> E

    Note over B,D: CPU > 10% trigger
```

Explanation:

* **Azure Subscription:**  Encloses all components as they reside within an Azure Subscription.
* **App Service - MyWebApp:** Represents the Azure Web App being monitored.  Named "MyWebApp" for clarity.
* **Azure Monitor - CPU High Usage:**  Represents the Azure Monitor alert rule that detects high CPU usage on the Web App.  It explicitly mentions "CPU High Usage" to specify the monitoring aspect.  This monitors the CPU usage of "MyWebApp".
* **Action Group - Restart App:** Represents the Azure Action Group that's triggered when the Azure Monitor alert is fired.  It's configured to invoke the Azure Function.
* **Function App - RestartWebAppFunc:** Represents the Azure Function App containing the function that restarts the Web App.  Named "RestartWebAppFunc" to indicate its purpose. This restarts the "MyWebApp".
* **Arrows:** The arrows indicate the flow of events.
* **Alternative - Logic App (Optional):** Shows an alternative approach using a Logic App for more complex orchestration.  This demonstrates how an Action Group *could* invoke a Logic App instead of a Function App.  The Logic App would then handle the actual restart of the Web App.
* **Note:** A note explains the triggering condition for the Azure Monitor alert.
* **Styles:** The diagram uses different styles (fill colors, border thickness) to visually distinguish the components.  App Services and Function Apps are green, while Monitor and Action Groups are light blue.
* **Dashed Links:** The alternative path using the Logic App has dashed lines to indicate it's optional.

This diagram clearly illustrates the architecture for automated Web App restarts based on high CPU usage monitoring using Azure Monitor, Action Groups, and Azure Functions, including an optional alternative path using Logic Apps.  The naming conventions make the diagram easier to understand.
```
