Okay, here's a detailed runbook for an Azure Web App CPU alert and auto-recovery workflow, designed to be used directly as a guide, not just a Markdown document. It covers symptoms, troubleshooting steps, auto-remediation details, and relevant logs. This runbook assumes a basic understanding of Azure portal and Azure Function concepts.

**Runbook: Azure Web App High CPU Usage Alert & Auto-Recovery**

**1. Alert Definition:**

*   **Alert Name:** WebAppHighCPU
*   **Resource:** [Your Azure Web App Name]
*   **Signal:** CPU Percentage
*   **Threshold:** Greater than 70%
*   **Aggregation Type:** Average
*   **Aggregation Granularity:** 5 Minutes
*   **Evaluation Frequency:** 1 Minute
*   **Action Group:** [Name of the Action Group that triggers the Azure Function]
*   **Severity:**  Medium (Adjust based on business impact)

**2. Symptoms:**

*   **User Reported:**
    *   Slow page load times.
    *   Application timeouts.
    *   Errors when submitting forms or accessing specific features.
*   **Monitoring:**
    *   Alert "WebAppHighCPU" triggered in Azure Monitor.
    *   CPU percentage consistently above 70% in the Azure portal's App Service Metrics section.
    *   Increased response times in Application Insights (if enabled).
    *   Increased error rates in Application Insights (if enabled).
    *   Increased queue lengths (if applicable, if the web app integrates with queueing systems).

**3. Initial Troubleshooting Steps (Manual Investigation):**

*   **3.1. Verify Alert:**
    *   Confirm the alert in Azure Monitor.  Acknowledge the alert to indicate you're working on it.
    *   Check the alert details to see the exact time the alert triggered, the average CPU percentage during the evaluation window, and the resources affected.
*   **3.2. Check Web App Metrics in Azure Portal:**
    *   Navigate to your Web App in the Azure portal.
    *   Go to the "Monitoring" section, then "Metrics".
    *   Add the following metrics to the chart:
        *   **CPU Percentage:** Verify that CPU is consistently high.  Look for patterns (e.g., spikes at certain times).
        *   **Memory Working Set:** Check if memory usage is also high. High memory usage can indirectly cause high CPU.
        *   **Requests:** Monitor the number of requests per second. A sudden increase in requests could be the cause.
        *   **Data In/Out:** Monitor network traffic.  Unusually high network activity can indicate a problem.
    *   Change the time range to match the duration of the alert (e.g., "Last 30 Minutes").  Look at trends over time.
*   **3.3. Check Application Insights (If Enabled):**
    *   Navigate to your Application Insights resource associated with the Web App.
    *   **Performance:** Investigate slow operations, dependencies, and database queries.  Identify bottlenecks.
    *   **Failures:** Check for exceptions and error messages.  Errors can lead to CPU spikes.
    *   **Live Metrics Stream:**  Use Live Metrics Stream for near real-time diagnostics. Observe CPU usage, memory, requests, and exceptions.
*   **3.4. Diagnose using Kudu Console:**
    *   Navigate to `https://[your-web-app-name].scm.azurewebsites.net/DebugConsole` (Kudu Console).
    *   **Process Explorer:**  Identify which processes are consuming the most CPU.  Look for your application's process (`w3wp.exe`) or other suspicious processes.
    *   **Dump Process:**  If you identify a problematic process, create a process dump (using Kudu's Process Explorer) and download it. This dump can be analyzed later by developers to pinpoint the root cause.  *Important: Creating dumps impacts performance, so do this judiciously.*
*   **3.5. Check App Service Logs:**
    *   In the Azure portal, go to "App Service Logs" for your Web App.
    *   **Application Logs:**  Look for errors or warnings in the application logs.  Configuration errors or code defects often show up here.
    *   **Web Server Logs:**  Examine the web server logs (IIS logs) for HTTP errors (e.g., 500 errors).  These errors can indicate application problems.
    *   **Failed Request Tracing:** (If enabled) Analyze detailed tracing logs for failed requests to understand the cause of the failures.

**4. Possible Causes:**

*   **Application Code Issues:**
    *   Inefficient algorithms or code loops.
    *   Memory leaks.
    *   Blocking operations (e.g., waiting for I/O).
    *   Unoptimized database queries.
*   **Increased Traffic:**
    *   Sudden surge in user traffic.
    *   DDoS attack (unlikely, but possible).
    *   Crawler or bot activity.
*   **Configuration Issues:**
    *   Incorrect connection strings.
    *   Insufficient resources allocated to the Web App (e.g., small App Service Plan).
*   **External Dependencies:**
    *   Slow or unavailable database server.
    *   Problems with third-party APIs.
*   **Resource Contention:**
    *   Another application on the same App Service Plan consuming resources. (Less likely with dedicated App Service Plans).

**5. Auto-Remediation (Azure Function):**

*   **Function Name:** RestartWebAppFunction
*   **Trigger:** HTTP Trigger (triggered by the Action Group from the Azure Monitor Alert)
*   **Authentication:** System-Assigned Managed Identity (Grant "Contributor" role to the Function App's managed identity on the Web App)
*   **Code (Example - PowerShell):**

```powershell
param($Request, $TriggerMetadata)

#Requires -Modules Az.Websites

try {
    # Connect to Azure (using Managed Identity)
    Connect-AzAccount -Identity

    # Retrieve Web App Name from the Request Body (assuming the alert passes the Web App name in the payload)
    $body = ConvertFrom-Json $Request.Body
    $webAppName = $body.data.context.resourceName
    $resourceGroupName = $body.data.context.resourceGroupName

    Write-Host "Web App Name: $webAppName"
    Write-Host "Resource Group Name: $resourceGroupName"

    # Restart the Web App
    Restart-AzWebApp -ResourceGroupName $resourceGroupName -Name $webAppName

    Write-Host "Web App '$webAppName' restarted successfully."

    # Optionally, log to Application Insights
    Write-Host "##[debug]Restarted Web App: $webAppName"
    [PSCustomObject]@{
        message = "Web App restarted successfully by auto-remediation function."
        webAppName = $webAppName
    } | ConvertTo-Json

    # Return a success code
    Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
        StatusCode = 200
        Body       = "Web App restarted successfully."
    })


}
catch {
    Write-Error "Error restarting Web App: $($_.Exception.Message)"

     # Optionally, log to Application Insights with severity level Error
    Write-Host "##[error]Failed to restart Web App: $webAppName - $($_.Exception.Message)"
    [PSCustomObject]@{
        message = "Failed to restart Web App by auto-remediation function."
        error = $_.Exception.Message
        webAppName = $webAppName
    } | ConvertTo-Json

    # Return an error code
     Push-OutputBinding -Name Response -Value ([HttpResponseContext]@{
        StatusCode = 500
        Body       = "Error restarting Web App: $($_.Exception.Message)"
    })
}
```

*   **Function Configuration:**
    *   **HTTP Trigger:**  Ensure the HTTP Trigger is enabled.
    *   **Application Settings:** Add any necessary application settings (e.g., if you're using different Azure regions).
    *   **Managed Identity:**  Enable System-Assigned Managed Identity and grant the necessary permissions (Contributor role) to the Web App.
*   **Action Group Configuration:**
    *   Create an Action Group in Azure Monitor.
    *   Add an Action of type "Azure Function".
    *   Select the `RestartWebAppFunction` function.
    *   **Important:**  Configure the Action Group to pass the Web App name and Resource Group name in the HTTP request body to the Azure Function.  The exact format depends on your alert configuration, but the function code expects a JSON body like this:

```json
{
    "data": {
        "context": {
            "resourceName": "[Your Web App Name]",
            "resourceGroupName": "[Your Resource Group Name]"
        }
    }
}
```
You should ensure this payload is sent via the "Customize JSON payload" option inside the action group's Azure Function configuration to ensure that the Web App name and Resource Group name is passed to the PowerShell code for restarting the Web App.

**6. Verification of Auto-Remediation:**

*   **Check Function Logs:**  In the Azure portal, go to the `RestartWebAppFunction`.  Check the "Monitor" section to see if the function was triggered and if it completed successfully.  Examine the logs for any errors.
*   **Check Web App Status:** After the function runs, verify that the Web App has been restarted.  You can do this by:
    *   Checking the "Overview" page of the Web App in the Azure portal. The "Status" should indicate that it was recently restarted.
    *   Refreshing the Web App in a browser.  You might see a brief period of unavailability during the restart.
    *   Monitoring the CPU percentage in the Azure portal.  The CPU should decrease after the restart.
*   **Check Azure Monitor:** If the auto-remediation was successful, the "WebAppHighCPU" alert should resolve automatically. If it doesn't, investigate further.

**7. Escalation (If Auto-Remediation Fails):**

*   If the Azure Function fails to restart the Web App, or if the high CPU issue persists after the restart, escalate to the next level of support (e.g., DevOps team, application developers).
*   Provide the support team with the following information:
    *   The alert details from Azure Monitor.
    *   The troubleshooting steps you have already taken.
    *   The logs from the Azure Function.
    *   Any relevant logs or metrics from the Web App and Application Insights.
    *   The process dump (if you created one).

**8. Long-Term Resolution:**

*   **Code Optimization:** If the high CPU is caused by inefficient code, prioritize code optimization.  Use profiling tools to identify performance bottlenecks.
*   **Scaling Up:** If the Web App is consistently reaching its CPU limits, consider scaling up the App Service Plan to a larger size with more CPU cores.
*   **Scaling Out:** If the application is stateless, consider scaling out the Web App to multiple instances. This distributes the load across multiple servers.
*   **Caching:** Implement caching strategies to reduce the load on the application server.  Use Azure Cache for Redis or other caching solutions.
*   **Database Optimization:** Optimize database queries and indexing to improve performance.
*   **Traffic Management:** Implement traffic shaping or throttling to limit the number of requests to the Web App.
*   **Background Tasks:** Offload long-running tasks to background processes (e.g., Azure Functions, Azure Queue Storage).
*   **Regular Monitoring and Tuning:** Continuously monitor the Web App's performance and make adjustments as needed.

**9. Logs:**

*   **Azure Monitor Alert Logs:**  View the history of the "WebAppHighCPU" alert in Azure Monitor.
*   **Azure Function Logs:**  Access the logs of the `RestartWebAppFunction` to see if it was triggered, if it succeeded, and any errors that occurred. Use Application Insights integration within the Function App for detailed log analysis.
*   **App Service Logs:**  Check the application logs, web server logs, and failed request tracing logs for the Web App.
*   **Application Insights Logs:**  If enabled, use Application Insights to monitor performance, failures, and exceptions.
*   **Kudu Console Logs:** While not persistent, the output from commands run in the Kudu console can provide valuable insights during troubleshooting.

**10. Runbook Review:**

*   Review this runbook regularly (e.g., every 6 months) to ensure it is up-to-date and effective.
*   Update the runbook based on lessons learned from past incidents.

This runbook provides a comprehensive guide to address high CPU usage issues in your Azure Web App. Remember to adapt the specific steps and configurations to your environment and application.
