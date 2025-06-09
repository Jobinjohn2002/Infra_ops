```markdown
# Azure WebApp High CPU Usage Runbook (Auto-Recovery)

**Alert Name:** WebAppHighCPU

**Target:** Azure WebApp

**Trigger Condition:** CPU Usage > 10% for 5 minutes

**Recovery Method:** Azure Function Restart

**Last Updated:** October 26, 2023

**Purpose:** This runbook outlines the steps to diagnose and remediate high CPU usage on an Azure WebApp. It includes both manual troubleshooting steps and an automated recovery process.

## 1. Symptoms

*   **End-User Reported Issues:**
    *   Slow application response times.
    *   Application timeouts.
    *   Inability to access the WebApp.
    *   Error messages in the application UI.
*   **Alert Triggered:** Azure Monitor Alert "WebAppHighCPU" triggered.
*   **WebApp Performance:**
    *   High CPU usage reported in Azure Monitor metrics for the WebApp (e.g., > 10%).
    *   Increased response times for HTTP requests.
    *   Increased number of requests queued.

## 2. Initial Investigation & Triage

**2.1 Verify the Alert:**

*   **Check Azure Monitor:** Review the alert details in Azure Monitor. Confirm the alert is active and that the triggering CPU percentage and time duration align with the configured threshold.
*   **Assess Impact:** Determine the extent of the impact. Is it affecting all users or a specific subset? Is the application completely unresponsive, or just slower than usual?

**2.2 Gather Initial Information:**

*   **WebApp Name:** [WebApp Resource Name]
*   **Resource Group:** [Resource Group Name]
*   **App Service Plan:** [App Service Plan Name]
*   **WebApp Instance(s):** (If scaled out, list all instances experiencing high CPU)
*   **Alert Timestamp:** [Timestamp of Alert Trigger]
*   **Azure Region:** [Azure Region]

## 3. Troubleshooting

**3.1 Examine WebApp Metrics:**

*   **Navigate to the Azure Portal:** Open the Azure Portal and navigate to the WebApp.
*   **Explore Metrics:** Under "Monitoring," select "Metrics."
*   **Key Metrics to Analyze:**
    *   **CPU Percentage:** Confirm that the CPU usage is consistently above the threshold (10%). Look for patterns and spikes.
    *   **Memory Working Set:** Check if memory usage is also high. High memory usage can sometimes contribute to high CPU.
    *   **Requests:** Monitor the number of requests being processed. A sudden increase in requests can overload the WebApp.
    *   **Http Queue Length:** A large queue length indicates the WebApp is struggling to handle the request load.
    *   **Data In/Data Out:** Monitor network traffic for anomalies.
    *   **ThreadPool Threads:** Examine the number of threads in use by the .NET thread pool. Thread exhaustion can lead to CPU bottlenecks.
*   **Diagnostic Tools:** Use Application Insights or App Service Diagnostics (under "Diagnose and solve problems") for more in-depth analysis.

**3.2 Analyze Application Insights (If Configured):**

*   **Performance:** Investigate slow requests and dependencies. Identify the slowest transactions and their underlying components.
*   **Exceptions:** Look for any unhandled exceptions that might be causing the application to loop or consume excessive CPU.
*   **Live Metrics:**  Use Live Metrics to observe real-time performance data.

**3.3 App Service Diagnostics:**

*   **Navigate to "Diagnose and solve problems" in the WebApp blade.**
*   **Choose relevant diagnostic tools:**
    *   **Performance Issues:**  Run the "Performance Issues" diagnostic to identify potential bottlenecks.
    *   **CPU Analysis:** Utilize the CPU Analysis tool to identify methods or processes consuming the most CPU.
    *   **Availability and Performance:** Run diagnostics to check application availability and assess performance metrics.

**3.4 Remote Debugging (Advanced):**

*   If the above steps don't reveal the root cause, consider remote debugging the WebApp. This allows you to step through the code and identify the source of the CPU consumption.  **Note:** This should only be performed in a non-production environment first.
*   **Tools:** Visual Studio with the Azure SDK installed.
*   **Prerequisites:** Enable remote debugging on the WebApp through the Azure Portal (under "Configuration" -> "General settings").
*   **Procedure:** Attach the debugger to the `w3wp.exe` process (or the relevant process for your application framework) and examine thread activity and CPU usage.

**3.5 Examine Application Logs:**

*   **Access App Service Logs:**
    *   **Kudu Console:** Navigate to the Kudu console (`https://[your-webapp-name].scm.azurewebsites.net/`) and access log files under `D:\home\LogFiles`.  Check `application` logs, `http` logs, and any custom log files.
    *   **Log Stream:**  Use the Log Stream feature in the Azure Portal (under "Monitoring" -> "Log stream") to view real-time log output.
*   **Analyze Logs:**
    *   Look for error messages, warnings, or unusual activity that might indicate the cause of the high CPU.
    *   Correlate log entries with the timestamp of the alert trigger.

**3.6  Common Causes of High CPU Usage:**

*   **Code Issues:**
    *   Infinite loops.
    *   Inefficient algorithms.
    *   Memory leaks leading to garbage collection thrashing.
    *   Deadlocks.
*   **External Dependencies:**
    *   Slow database queries.
    *   Unresponsive external services.
    *   Network latency.
*   **High Request Load:**
    *   Sudden surge in user traffic.
    *   Denial-of-service (DoS) attack.
    *   Crawlers or bots.
*   **Configuration Issues:**
    *   Incorrectly configured caching.
    *   Excessive logging.
    *   Inadequate resources (e.g., small App Service Plan).
*   **Background Processes:**
    *   Scheduled tasks or background jobs consuming resources.

## 4. Auto-Remediation (Azure Function Restart)

**4.1 Azure Function Details:**

*   **Function Name:**  [Azure Function Name] (e.g., RestartWebAppFunction)
*   **Resource Group:** [Resource Group Name containing the Azure Function]
*   **Function Logic:**
    *   Receives a WebApp name as input.
    *   Authenticates with Azure using a Managed Identity (recommended) or a Service Principal.
    *   Uses the Azure SDK to restart the WebApp.

**4.2 Function Code Example (PowerShell):**

```powershell
# Requires -Modules Az.Websites, Az.Accounts

param($webAppName)

try {
    # Connect to Azure
    Connect-AzAccount -Identity  # Use Managed Identity

    # Alternatively, use Service Principal:
    # Connect-AzAccount -ServicePrincipal -TenantId "<TenantId>" -ApplicationId "<AppId>" -CertificateThumbprint "<Thumbprint>"

    Write-Host "Restarting WebApp: $webAppName"

    Restart-AzWebApp -ResourceGroupName "[Resource Group Name]" -Name $webAppName -Force

    Write-Host "WebApp $webAppName restarted successfully."
}
catch {
    Write-Error "Error restarting WebApp: $($_.Exception)"
    throw $_.Exception
}
```

**4.3 Alert Rule Configuration:**

*   **Action Group:** The Azure Monitor Alert rule should be configured to trigger the Azure Function.
*   **Webhook Payload:**  The alert's webhook payload should include the `webAppName` as a parameter that the function expects.

**Example Webhook Payload (JSON):**

```json
{
  "schemaId": "AzureMonitorMetricAlert",
  "data": {
    "context": {
      "timestamp": "2023-10-26T12:00:00Z",
      "id": "/subscriptions/[subscriptionId]/resourceGroups/[resourceGroupName]/providers/Microsoft.Web/sites/[webAppName]",
      "name": "[webAppName]",
      "description": "High CPU Usage Alert",
      "conditionType": "SingleResourceMultipleMetricCriteria",
      "condition": {
        "metricName": "CpuPercentage",
        "metricUnit": "Percent",
        "timeAggregation": "Average",
        "operator": "GreaterThan",
        "threshold": "10",
        "windowSize": "00:05:00",
        "failedLocationCount": 1
      },
      "subscriptionId": "[subscriptionId]",
      "resourceGroupName": "[resourceGroupName]",
      "resourceName": "[webAppName]",
      "resourceType": "Microsoft.Web/sites",
      "resourceId": "/subscriptions/[subscriptionId]/resourceGroups/[resourceGroupName]/providers/Microsoft.Web/sites/[webAppName]",
      "resourceRegion": "[region]",
      "portalLink": "https://portal.azure.com/#resource/subscriptions/[subscriptionId]/resourceGroups/[resourceGroupName]/providers/Microsoft.Web/sites/[webAppName]/overview",
       "properties": {
           "webAppName": "[webAppName]"  // Pass the WebApp name to the Function
       }
    },
    "configuration": {
      "metricName": "CpuPercentage",
      "threshold": "10",
      "windowSize": "PT5M"
    }
  }
}
```

**4.4 Monitoring the Auto-Remediation:**

*   **Azure Function Logs:** Monitor the Azure Function's execution logs to ensure the restart was successful.  Check for errors in the function execution.
*   **WebApp Metrics:** After the function executes, monitor the WebApp's CPU usage to confirm that it has returned to a normal level.
*   **Azure Monitor Activity Log:** Review the Azure Monitor Activity Log for the WebApp to verify the restart operation.

## 5. Escalation

If the auto-remediation fails to resolve the issue, or if the high CPU usage persists shortly after the restart, escalate to the on-call engineer.

**Escalation Path:**

1.  **On-Call Engineer:** [Name/Alias of On-Call Engineer]
2.  **Engineering Team Lead:** [Name/Alias of Engineering Team Lead]

## 6. Post-Incident Analysis

*   **Root Cause Analysis:** After the incident is resolved, conduct a thorough root cause analysis to determine the underlying cause of the high CPU usage.
*   **Permanent Fix:** Implement a permanent fix to prevent the issue from recurring. This might involve code changes, configuration adjustments, or resource upgrades.
*   **Runbook Updates:** Update this runbook with any lessons learned and improvements to the auto-remediation process.
*   **Monitoring Improvements:** Enhance the monitoring configuration to provide earlier detection of potential issues.

## 7. Logs

*   **Azure WebApp Logs:** Access logs through the Kudu console or the Log Stream feature.
*   **Azure Function Logs:** View logs in the Azure Portal for the Azure Function.
*   **Azure Monitor Activity Log:** Review the Activity Log for events related to the WebApp and Function.
*   **Application Insights Logs:** Utilize Application Insights queries to analyze telemetry data related to the WebApp's performance and exceptions.  Examples:

    *   `requests | where timestamp > ago(1h) | summarize avg(duration), count() by bin(timestamp, 5m)` (Average request duration over time)
    *   `exceptions | where timestamp > ago(1h) | summarize count() by type` (Exception counts by type)

## 8. Related Documentation

*   **Azure Monitor Documentation:** [Link to Azure Monitor Documentation]
*   **Azure WebApp Documentation:** [Link to Azure WebApp Documentation]
*   **Azure Functions Documentation:** [Link to Azure Functions Documentation]
*   **Application Insights Documentation:** [Link to Application Insights Documentation]

This comprehensive runbook provides a structured approach to handling high CPU usage on an Azure WebApp, combining automated recovery with detailed troubleshooting steps and logging guidance. Remember to replace the bracketed placeholders with the actual values for your environment.  This will allow for faster and more accurate responses to incidents.

## Architecture Diagram

![Diagram](diagram.png)
