```markdown
# Azure WebApp High CPU Alert Runbook & Auto-Recovery

**Document Version:** 1.0
**Last Updated:** October 26, 2023
**Author:** GPT-3

This runbook details the procedure to follow when an Azure WebApp CPU alert is triggered. It includes symptom identification, initial troubleshooting steps, auto-remediation (restart), and investigation steps. The alert is configured to trigger when CPU usage exceeds 10% for a sustained period (e.g., 5 minutes). An Azure Function handles the auto-remediation.

## 1. Alert Details

*   **Alert Name:** WebAppHighCPU
*   **Resource:** `{WebAppName}` (Replace with actual WebApp name)
*   **Severity:** High
*   **Trigger Condition:** CPU Percentage > 10% for 5 minutes (Example - adjust as needed)
*   **Alert Rule Type:** Metric Alert
*   **Action Group:** `{ActionGroupName}` (Configured to trigger the Azure Function)
*   **Auto-Remediation:** Enabled (Calls the Azure Function)
*   **Azure Function Name:** `RestartWebAppFunction`
*   **Function App Name:** `RecoveryFunctionsApp`
*   **Resource Group:** `RecoveryFunctionsRG`

## 2. Symptoms

*   **High CPU Utilization:** Reported by Azure Monitor (above 10%).
*   **Web Application Slowness/Unresponsiveness:** User-reported slow performance or inability to access the web application.
*   **Increased Error Rates:** Potential increase in HTTP 500 errors or timeouts.
*   **Performance Degradation:** Monitoring dashboards may show performance bottlenecks related to CPU.

## 3. Initial Assessment

**3.1 Check Alert Details:**

*   **Confirm Alert Triggered:** Verify that the `WebAppHighCPU` alert has indeed triggered in Azure Monitor.
*   **Validate Timestamp:** Check the timestamp of the alert trigger.
*   **Resource Scope:** Ensure the alert is triggered for the correct WebApp (`{WebAppName}`).

**3.2 Verify Auto-Remediation Status:**

*   **Check Azure Function Execution:** Navigate to the `RecoveryFunctionsApp` in the Azure Portal.
*   **Monitor Function Execution Logs:**
    *   Go to `Functions` -> `RestartWebAppFunction` -> `Monitor`.
    *   Look for a recent execution log corresponding to the alert trigger timestamp.
    *   **Success:** A successful execution indicates the Function attempted to restart the WebApp. Verify the WebApp is back online.
    *   **Failure:** A failed execution indicates an issue with the Function.  See Section 6 (Logs and Troubleshooting).

## 4. Auto-Remediation (Restart via Azure Function)

The Azure Function `RestartWebAppFunction` is designed to automatically restart the WebApp when triggered.

**Function Logic:**

```python
# Example Python Azure Function Code (adjust for your setup and authentication)
import logging
import azure.functions as func
import azure.mgmt.web
from azure.identity import DefaultAzureCredential

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    web_app_name = '{WebAppName}' # Replace with your WebApp name
    resource_group = '{WebAppResourceGroup}' # Replace with your WebApp resource group
    subscription_id = '{AzureSubscriptionID}' # Replace with your Azure Subscription ID

    try:
        # Authenticate using Managed Identity or Service Principal
        credential = DefaultAzureCredential()

        # Create a WebAppsManagementClient
        web_client = azure.mgmt.web.WebAppsManagementClient(credential, subscription_id)

        # Restart the WebApp
        web_client.web_apps.restart(resource_group, web_app_name)
        logging.info(f"Successfully restarted WebApp: {web_app_name}")

        return func.HttpResponse(
             f"Restarted WebApp {web_app_name}.",
             status_code=200
        )

    except Exception as e:
        logging.error(f"Error restarting WebApp: {e}")
        return func.HttpResponse(
             f"Error restarting WebApp: {e}",
             status_code=500
        )

if __name__ == "__main__":
    import os
    os.environ["AzureWebJobsStorage"] = ""  # Local Testing: Remove in production
    req = func.HttpRequest(
            method='GET',
            url='/api/RestartWebAppFunction',
            body=b'',
            params={}
    )
    resp = main(req)
    print(resp.get_body())
```

**4.1 Verify WebApp Restart:**

*   **Check WebApp Status:**  Navigate to the WebApp in the Azure Portal and check its status. It should be running.
*   **Test Application Functionality:**  Access the web application to verify that it is responsive and functioning correctly.
*   **Monitor CPU Usage:** Observe the CPU usage in Azure Monitor.  If the restart was successful, CPU usage should have dropped below the threshold.

**If Auto-Remediation Fails or CPU Remains High (Proceed to further investigation)**

## 5. Detailed Troubleshooting

If the auto-remediation fails to resolve the issue, perform the following steps:

**5.1 Identify the Cause of High CPU:**

*   **Azure App Service Diagnostics:**  Azure provides built-in diagnostics for App Services. Access them through the WebApp's blade in the Azure Portal under "Diagnose and solve problems."  Explore options like:
    *   **CPU Analysis:**  Provides insights into processes contributing to high CPU.
    *   **Memory Analysis:**  Examine memory usage patterns, which can indirectly affect CPU.
    *   **Availability and Performance:**  Review overall performance metrics.
*   **App Service Logs:**  Examine the WebApp's application logs for any errors or warnings that might indicate the cause of high CPU.  Access logs through:
    *   **Log stream:** Real-time logging from the WebApp.
    *   **Kudu Debug Console:** Allows you to browse the file system and view log files directly. (Access Kudu by navigating to `https://<your_web_app_name>.scm.azurewebsites.net/`)
*   **Azure Monitor Logs (if configured):** If you have configured Azure Monitor Logs, query the logs for events related to the WebApp's performance. Useful KQL queries include:
    ```kusto
    AppServiceAppLogs
    | where TimeGenerated > ago(1h)
    | where AppName == "{WebAppName}"
    | project TimeGenerated, Message, SourceContext
    | sort by TimeGenerated desc

    AppServiceHTTPLogs
    | where TimeGenerated > ago(1h)
    | where AppName == "{WebAppName}"
    | summarize count() by bin(TimeGenerated, 1m), ResultDescription
    | render timechart
    ```
*   **Profiling (Advanced):** Use Azure Profiler or other profiling tools to identify the specific code sections consuming the most CPU. This requires more in-depth application knowledge.

**5.2 Common Causes of High CPU:**

*   **Code Bugs:**  Inefficient code, infinite loops, or resource leaks.
*   **High Traffic:**  Unexpectedly high user load.
*   **Long-Running Processes:**  Scheduled tasks or background processes consuming excessive CPU.
*   **Database Bottlenecks:**  Slow database queries or connection issues.
*   **External Dependencies:**  Issues with external services or APIs used by the application.
*   **Security Threats:**  Malicious activity, such as denial-of-service attacks.

**5.3 Mitigation Steps (After Identifying the Cause):**

*   **Code Optimization:**  Fix any identified code bugs or performance bottlenecks.
*   **Scaling Up/Out:**  Increase the App Service Plan size (Scale Up) or add more instances (Scale Out) to handle increased load.
*   **Throttling:** Implement request throttling or rate limiting to prevent overload.
*   **Database Optimization:**  Optimize database queries and indexes.
*   **Caching:**  Implement caching strategies to reduce database load.
*   **Service Restarts (Selective):** If a specific process is identified as the culprit, consider restarting only that process instead of the entire WebApp. (This might not be possible depending on your application's architecture).
*   **Security Measures:**  Implement security measures to protect against malicious activity.
*   **Rollback:** If a recent deployment caused the issue, consider rolling back to a previous version.

## 6. Logs and Troubleshooting (Function and Alerting)

**6.1 Azure Function Logs:**

*   **Accessing Logs:** Navigate to the `RecoveryFunctionsApp` in the Azure Portal.
    *   `Functions` -> `RestartWebAppFunction` -> `Monitor`.
    *   Consider enabling Application Insights for the Function App for more detailed logging and analytics.

**6.2 Common Function Errors:**

*   **Authentication Issues:** The Function may not have sufficient permissions to restart the WebApp.  Ensure that the Function's Managed Identity or Service Principal has the `Contributor` role or a custom role with the `Microsoft.Web/sites/restart/action` permission on the WebApp or Resource Group.
*   **WebApp Not Found:** Verify that the `web_app_name` and `resource_group` variables in the Function code are correct.
*   **Service Unavailable:**  Azure services might be temporarily unavailable. Implement retry logic in the Function.
*   **Missing Dependencies:** The Function might be missing required Python packages.  Ensure that the `requirements.txt` file includes all necessary dependencies and that they are deployed correctly.

**6.3 Azure Monitor Alert Troubleshooting:**

*   **Incorrect Alert Rule Configuration:** Verify that the alert rule is correctly configured, including the metric, threshold, and evaluation frequency.
*   **Disabled Alert Rule:** Ensure that the alert rule is enabled.
*   **Action Group Issues:**
    *   Verify that the Action Group is correctly configured and associated with the alert rule.
    *   Check the Action Group's history to see if the Azure Function was triggered.
    *   Confirm that the Action Group has permissions to trigger the Azure Function (if using HTTP Trigger).  If using a queue trigger, ensure the correct permissions are in place for the Function to access the queue.

## 7. Escalation

If the problem persists or you are unable to identify the root cause, escalate to the appropriate support team, providing the following information:

*   Alert Details (from Section 1)
*   Troubleshooting Steps Taken (and their results)
*   Function Logs
*   WebApp Logs
*   Diagnostic Reports
*   Suspected Cause (if any)

## 8. Post-Incident Review

After the incident is resolved, conduct a post-incident review to:

*   Identify the root cause of the high CPU.
*   Determine if the auto-remediation was effective.
*   Identify any gaps in the monitoring or alerting setup.
*   Implement preventative measures to avoid future incidents.
*   Update the runbook based on lessons learned.

## 9. Appendix

*   **Kudu Debug Console:** Access via `https://<your_web_app_name>.scm.azurewebsites.net/`
*   **Azure App Service Diagnostics:** Available in the Azure Portal for your WebApp under "Diagnose and solve problems."

**Note:** Replace the placeholder values (e.g., `{WebAppName}`, `{WebAppResourceGroup}`, `{AzureSubscriptionID}`, `{ActionGroupName}`) with your actual values.  This runbook provides a starting point and may need to be customized based on your specific application and environment.  Adjust trigger thresholds and monitoring intervals as needed. Remember to implement appropriate security measures, especially when using Managed Identities or Service Principals. Regularly review and update this runbook.

## Architecture Diagram (Mermaid)
```mermaid
```mermaid
graph LR
    subgraph Azure Resource Group
        A[WebApp (App Service)] --> B{Azure Monitor};
        B --> C{Action Group};
        C --> D[Function App (WebApp Restart)];

        style A fill:#f9f,stroke:#333,stroke-width:2px
        style B fill:#ccf,stroke:#333,stroke-width:2px
        style C fill:#ddf,stroke:#333,stroke-width:2px
        style D fill:#eef,stroke:#333,stroke-width:2px

        subgraph Optional
          E[Logic App (Orchestration)];
          C --> E;
          style E fill:#fdf,stroke:#333,stroke-width:2px
        end
    end

    B -- CPU > 10% --> C;
    D --> A;

    linkStyle 0,1,2,3 stroke-width:2px;

    classDef box fill:#f9f,stroke:#333,stroke-width:2px;
    class A box;

    classDef monitor fill:#ccf,stroke:#333,stroke-width:2px;
    class B monitor;

    classDef actiongroup fill:#ddf,stroke:#333,stroke-width:2px;
    class C actiongroup;

    classDef functionapp fill:#eef,stroke:#333,stroke-width:2px;
    class D functionapp;

    classDef logicapp fill:#fdf,stroke:#333,stroke-width:2px;
    class E logicapp;

    subgraph Legend
      L1[WebApp (App Service) - The Azure web app being monitored.];
      L2[Azure Monitor - Monitors metrics and triggers alerts.];
      L3[Action Group - Defines actions triggered by alerts (in this case, calling the Function App).];
      L4[Function App - Restarts the WebApp.];
      L5[Logic App (Optional) - Can be used for more complex orchestration, like notifying on restart or implementing throttling.];
    end
```

**Explanation:**

*   **Azure Resource Group:** A container for all the Azure resources.  This helps logically group related resources together for management.

*   **WebApp (App Service):** The Azure WebApp that is being monitored.

*   **Azure Monitor:** Monitors the WebApp's CPU usage. When the CPU usage exceeds 10%, it triggers an alert.

*   **CPU > 10%:**  An edge indicating the condition that triggers the alert.

*   **Action Group:**  Configured in Azure Monitor to specify the action to be taken when the alert is triggered.  In this case, it calls the Function App.

*   **Function App (WebApp Restart):** An Azure Function that contains the code to restart the WebApp.  This function is triggered by the Action Group.

*   **Logic App (Optional):**  An optional Azure Logic App that can be used for more complex orchestration.  For example, it could be used to:
    *   Send a notification when the WebApp is restarted.
    *   Implement throttling to prevent too many restarts in a short period.
    *   Log the restarts.

*   **Legend:** A section explaining each component.

**How it works:**

1.  Azure Monitor continuously monitors the CPU usage of the WebApp.
2.  If the CPU usage exceeds 10%, Azure Monitor triggers an alert.
3.  The alert triggers the Action Group.
4.  The Action Group executes the Azure Function.
5.  The Azure Function restarts the WebApp.
6.  Optionally, the Action Group could trigger a Logic App for more complex handling.

**Key Improvements in this Version:**

*   **Explicit Condition:** Added the `CPU > 10%` edge label to clearly show the alert trigger condition.
*   **Legend:** A helpful legend explaining each component in the diagram.
*   **Resource Group:**  Added an overall Azure Resource Group to represent the container for all the resources.
*   **Clearer Descriptions:** Improved the descriptions of each component.
*   **Styling:** Used styles to highlight each component type.
*   **Function App Label:** Clarified the Function App's purpose: `WebApp Restart`.
*   **Optional Logic App Description:** Added examples of how a Logic App could be used.
*   **Link Style:** Set the link style to have a thicker line, making them easier to see.
```
