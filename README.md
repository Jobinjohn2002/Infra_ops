```markdown
# Azure WebApp High CPU Alert Runbook

**Document Version:** 1.0
**Last Updated:** 2023-10-27
**Author:** AI Generated (Edited for Quality)

**Purpose:** This runbook outlines the steps for responding to and resolving an Azure WebApp high CPU usage alert.  It details the symptoms, potential causes, troubleshooting steps, automated remediation (via an Azure Function), and how to review logs.

**Alert Name:** WebApp CPU Usage High

**Alert Description:** CPU usage for the Azure WebApp has exceeded 10% of its maximum allowed value.

**Severity:** Medium

**Escalation Point:**  On-call DevOps Engineer (pager: [PagerDuty integration here])

## 1. Symptoms

*   **High CPU Usage:**  Azure Monitor shows CPU Percentage exceeding 10% for the WebApp.
*   **Slow Response Times:** Users may experience slow page load times, API request timeouts, or application unresponsiveness.
*   **Error Logs:**  Application logs might contain error messages related to resource exhaustion, slow queries, or increased processing times.
*   **Performance Degradation:**  Overall application performance is noticeably degraded.
*   **Increased Queue Length:** Messages may be accumulating in associated queues (e.g., Azure Service Bus, Storage Queues) if the WebApp processes messages.

## 2. Potential Causes

*   **Code Issues:**
    *   **Inefficient Code:**  Poorly optimized code, infinite loops, or inefficient algorithms.
    *   **Memory Leaks:**  Gradual accumulation of memory that is not being released, leading to increased CPU usage due to garbage collection.
    *   **Deadlocks:**  Threads or processes waiting for resources held by other threads or processes, leading to CPU spinning while waiting.
*   **High Traffic:**  Sudden surge in user traffic exceeding the WebApp's capacity.
*   **Database Issues:**
    *   **Slow Queries:**  Database queries that take a long time to execute, consuming CPU resources.
    *   **Database Connection Issues:**  Frequent connection errors or timeouts impacting application performance and CPU.
*   **External Dependencies:**
    *   **Slow Downstream Services:**  Dependence on slow or unresponsive external services (e.g., APIs, databases).
    *   **Network Issues:** Network latency or connectivity problems affecting communication with external resources.
*   **Background Tasks:**
    *   **Scheduled Jobs:**  CPU-intensive scheduled tasks running on the WebApp.
    *   **WebJobs:** Continuously running or triggered WebJobs consuming CPU.
*   **Security Issues:**
    *   **Malicious Attacks:**  DoS or DDoS attacks overwhelming the WebApp's resources.
    *   **Compromised Code:**  Malicious code injected into the application.
*   **Resource Constraints:**
    *   **Insufficient App Service Plan:**  WebApp is operating in an App Service Plan with insufficient CPU resources.
    *   **Scaling Issues:** Autoscaling is not configured correctly or is failing to scale effectively.

## 3. Troubleshooting Steps

**A. Initial Investigation (5-10 minutes):**

1.  **Verify the Alert:** Confirm the alert is active in Azure Monitor and review the alert details, including the specific metric (CPU Percentage) and the time the alert was triggered.
2.  **Check Azure Status:**  Visit [https://status.azure.com/](https://status.azure.com/) to check for any known Azure outages or incidents that might be affecting the WebApp's region.
3.  **Review Azure Monitor Metrics:**
    *   **CPU Percentage:** Analyze the CPU Percentage graph in Azure Monitor for the WebApp to confirm the sustained high CPU usage.
    *   **Memory Percentage:** Check memory usage to identify potential memory leaks or excessive memory consumption.
    *   **Requests:** Analyze the number of requests per second to see if there is a sudden spike in traffic.
    *   **HTTP Queue Length:** Observe the HTTP Queue Length to determine if requests are being queued up due to high CPU.
    *   **Data In/Out:** High network data in or out may also point to network issues or unexpected traffic volumes.
4.  **Check Application Logs:**  Examine the WebApp's application logs in Azure App Service Logs (Application Insights if configured, or standard App Service logs) for any error messages, exceptions, or warnings that coincide with the high CPU usage. Look for clues about slow queries, timeouts, or resource exhaustion.

**B. Detailed Analysis (15-30 minutes):**

1.  **Investigate Slow Requests (Application Insights):** If Application Insights is configured:
    *   Navigate to the "Performance" section of your Application Insights resource associated with the WebApp.
    *   Identify the slowest requests based on response time.
    *   Drill down into individual request traces to analyze the call stack and identify the specific code sections or database queries that are consuming the most time.
2.  **Azure App Service Diagnostics:**
    *   Navigate to your WebApp in the Azure portal.
    *   In the left-hand menu, click on "Diagnose and solve problems."
    *   Use the built-in diagnostics tools (e.g., "Performance Issues," "Availability and Performance") to identify potential problems, such as slow requests, high CPU, or memory leaks.
    *   The "Diagnostic Tools" section allows for deeper analysis, including:
        *   **Process Explorer:** View running processes on the WebApp instance and their CPU and memory consumption.  Identify which processes are contributing the most to the high CPU usage.
        *   **Memory Dump Analysis:** Capture a memory dump of the WebApp process and analyze it to identify memory leaks or excessive memory consumption. (Requires deeper technical expertise)
        *   **Proactive CPU Monitoring:** Configure Proactive CPU Monitoring to automatically collect data when CPU spikes occur, providing valuable insights for root cause analysis.
3.  **Database Monitoring (If Applicable):**
    *   Check the performance metrics of the associated database (e.g., Azure SQL Database, Cosmos DB) for slow queries, high CPU utilization, or other performance bottlenecks.
    *   Use database monitoring tools to identify long-running queries and optimize them.
4.  **Check WebJobs:**  If using WebJobs, review their logs and resource consumption to ensure they are not contributing to the high CPU usage.
5.  **Check Scaling Settings:** Review the App Service Plan scaling rules and ensure that autoscale is enabled and configured correctly to handle traffic spikes. Are the scale-out triggers appropriate (e.g., CPU Threshold)? Are the scale-out limits sufficient?

## 4. Auto-Remediation (Azure Function Restart)

**A. Azure Function Details:**

*   **Function Name:**  `WebAppRestartFunction` (example)
*   **Resource Group:**  `rg-monitoring` (example)
*   **App Service Plan (for the Function):** `ASP-Monitoring` (example - ideally on a separate App Service Plan)
*   **Trigger:** HTTP Trigger (or Queue Trigger triggered by the Azure Monitor Alert Action Group)
*   **Authentication:**  Managed Identity (System-assigned or User-assigned) with `Web App Contributor` role assigned to the WebApp.
*   **Code Example (PowerShell):**

```powershell
param($Request, $TriggerMetadata)

# Replace with your WebApp name and Resource Group
$WebAppName = "your-webapp-name"
$ResourceGroupName = "your-resource-group-name"

# Get the WebApp using the AzureRM module
try {
    Connect-AzAccount -Identity
    Write-Host "Successfully connected to Azure with Managed Identity."
}
catch {
    Write-Host "Failed to connect to Azure with Managed Identity: $($_.Exception)"
    # Consider logging more details here for troubleshooting
    exit 1 # Exit with an error code
}


try {
    # Restart the Web App
    Write-Host "Restarting WebApp: $WebAppName in Resource Group: $ResourceGroupName"
    Restart-AzWebApp -Name $WebAppName -ResourceGroupName $ResourceGroupName -Force

    Write-Host "WebApp restart initiated successfully."

    # Optional: Return a success message to the caller.
    $body = @{ message = "WebApp restart initiated successfully for $WebAppName in $ResourceGroupName" } | ConvertTo-Json
    return [HttpResponseContext]@{
        StatusCode = 200
        Body = $body
        Headers = @{"Content-Type" = "application/json"}
    }
}
catch {
    Write-Host "Error restarting WebApp: $($_.Exception)"
    # Consider logging more details here for troubleshooting
    $body = @{ message = "Error restarting WebApp: $($_.Exception.Message)" } | ConvertTo-Json
    return [HttpResponseContext]@{
        StatusCode = 500
        Body = $body
        Headers = @{"Content-Type" = "application/json"}
    }
    exit 1 # Exit with an error code
}

```

**B. Azure Monitor Alert Action Group Configuration:**

1.  In the Azure portal, navigate to the Azure Monitor service.
2.  Select "Alerts" and then "Action groups."
3.  Create a new action group (or modify an existing one).
4.  Add an action with the following settings:
    *   **Action Type:**  "Azure Function"
    *   **Function App:** Select the `WebAppRestartFunction` you created.
    *   **HTTP Trigger:**  Select the appropriate HTTP Trigger.
    *   **Use common alert schema:** Enabled

**C.  How it Works:**

1.  The Azure Monitor alert triggers when the CPU usage exceeds the defined threshold (10%).
2.  The alert triggers the Action Group.
3.  The Action Group calls the `WebAppRestartFunction` via its HTTP Trigger endpoint.
4.  The `WebAppRestartFunction`, authenticating with its Managed Identity, uses the Azure Resource Manager (ARM) APIs to restart the WebApp.
5.  The WebApp restarts, clearing its current state and hopefully resolving the high CPU issue.

**D.  Important Considerations:**

*   **Managed Identity:** Using a Managed Identity is crucial for secure authentication to the Azure Resource Manager.  Avoid storing credentials directly in the function code.
*   **Idempotency:** While a simple restart is typically idempotent, consider more robust error handling within the Azure Function.  For example, you could check the WebApp's status *after* attempting the restart to confirm it was successful.
*   **Monitoring Function Executions:**  Monitor the execution of the Azure Function in Azure Monitor to ensure it is running correctly and without errors.
*   **Cooldown Period:** Consider implementing a cooldown period in the Azure Monitor alert to prevent excessive restarts if the high CPU issue persists. For example, set the "Evaluate based on" setting to a longer period (e.g., 15 minutes) and the "Frequency of evaluation" to a shorter period (e.g., 5 minutes) to avoid triggering the alert and restart too frequently.
*   **Alternative Triggers:** You can use a Queue Trigger instead of an HTTP trigger. The Alert Action group will then enqueue a message on to a dedicated queue which will in turn trigger the Azure Function. This helps decouple the alert from the function execution.

## 5. Post-Remediation Steps

1.  **Monitor CPU Usage:** After the restart, closely monitor the WebApp's CPU usage to ensure that it has returned to normal levels.  If the high CPU usage persists, the automated remediation may not be sufficient, and further investigation is required.
2.  **Analyze Logs:**  Review application logs, Azure Monitor metrics, and other diagnostic data to identify the root cause of the high CPU usage.  This is crucial to prevent recurrence of the issue.
3.  **Address Root Cause:**  Based on the root cause analysis, take appropriate actions, such as:
    *   **Optimize Code:**  Refactor inefficient code, fix memory leaks, and optimize database queries.
    *   **Scale Up App Service Plan:**  Upgrade the App Service Plan to a higher tier with more CPU resources.
    *   **Scale Out WebApp Instances:**  Increase the number of WebApp instances to handle the load.
    *   **Implement Caching:**  Implement caching mechanisms to reduce the load on the WebApp and database.
    *   **Throttle Requests:** Implement request throttling to prevent traffic spikes from overwhelming the WebApp.
    *   **Update Dependencies:** Update outdated libraries and dependencies.
4.  **Document Findings:**  Document the root cause analysis, remediation steps taken, and any recommendations for future prevention.
5.  **Update Runbook (If Needed):** Based on your experiences, update this runbook to improve its effectiveness and accuracy.

## 6. Logs

**A. Azure App Service Logs:**

*   **Location:** Azure portal -> Your WebApp -> App Service Logs
*   **Types:**
    *   **Application Logs:**  Logs generated by the application code.  (Important for identifying code issues, exceptions, and slow operations.)
    *   **Web Server Logs:** Logs generated by the web server (IIS or Kestrel). (Useful for diagnosing HTTP errors, access patterns, and security issues.)
    *   **Detailed Error Messages:** Detailed error messages from the web server.
    *   **Failed Request Tracing:** Detailed tracing information for failed requests.
*   **Configuration:**  Enable logging and configure the desired log levels in the WebApp's configuration settings.

**B. Application Insights (If Configured):**

*   **Location:** Azure portal -> Your Application Insights resource.
*   **Data:**
    *   **Requests:**  Detailed information about incoming requests, including response times, dependencies, and exceptions.
    *   **Exceptions:**  Logged exceptions and errors.
    *   **Performance:**  Performance metrics, including CPU usage, memory usage, and request durations.
    *   **Availability:**  Availability tests to monitor the uptime and responsiveness of the WebApp.
    *   **Custom Events and Metrics:**  Custom events and metrics that you can log from your application code.
*   **Querying:** Use Kusto Query Language (KQL) to query the data in Application Insights and identify patterns and anomalies.

**C. Azure Function Logs:**

*   **Location:** Azure portal -> Your Function App -> Function -> Monitor
*   **Data:** Logs generated by the Azure Function during execution.  (Essential for troubleshooting issues with the auto-remediation process.)
*   **Application Insights:** Integrate the Azure Function with Application Insights for more detailed monitoring and logging.

**D. Database Logs (If Applicable):**

*   **Azure SQL Database:** Use Azure SQL Database auditing and diagnostics to monitor database performance, identify slow queries, and troubleshoot database-related issues.
*   **Cosmos DB:** Use Cosmos DB monitoring and diagnostics to monitor database performance, identify slow queries, and troubleshoot database-related issues.

## 7. Known Issues and Workarounds

*   **Restart Fails:** The Azure Function might fail to restart the WebApp due to various reasons (e.g., network issues, permissions problems). Monitor the Function's execution logs and investigate any errors.  Ensure the Managed Identity has the necessary permissions.
*   **High CPU Persists:** The restart might only provide temporary relief, and the high CPU usage might return shortly afterward. This indicates that the root cause has not been addressed, and further investigation is required.
*   **Autoscale Issues:** If autoscale is not working correctly, the WebApp might not scale out quickly enough to handle traffic spikes. Review the autoscale settings and ensure that the scale-out rules are appropriate.

## 8.  Security Considerations

*   **Managed Identities:**  Always use Managed Identities for authentication to Azure resources. Avoid storing credentials directly in code or configuration files.
*   **Principle of Least Privilege:**  Grant the Managed Identity only the necessary permissions to perform its tasks (e.g., `Web App Contributor` role on the specific WebApp).
*   **Input Validation:**  Sanitize and validate all inputs to the Azure Function to prevent injection attacks.
*   **Secure Communication:**  Use HTTPS for all communication with the Azure Function and other Azure resources.

This runbook provides a comprehensive guide for responding to and resolving high CPU usage alerts for Azure WebApps.  Remember to customize the runbook with your specific application details and update it regularly based on your experiences and evolving needs.
```

## Architecture Diagram

![Diagram](diagram.png)
