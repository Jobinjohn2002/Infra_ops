## Azure WebApp High CPU Alert Runbook

**Alert Name:** WebApp CPU Utilization Exceeding 10%

**WebApp Name:** `<YourWebAppName>` (Replace with your WebApp's Name)

**Resource Group:** `<YourResourceGroupName>` (Replace with your WebApp's Resource Group)

**Alerting Threshold:** CPU Usage > 10%

**Auto-Recovery Mechanism:** Azure Function triggered by Azure Monitor Alert, restarts the WebApp.

**Document Version:** 1.0

**Last Updated:** October 26, 2023

**Purpose:** This runbook provides a detailed procedure for responding to Azure WebApp CPU utilization alerts exceeding 10%. It outlines the symptoms, troubleshooting steps, auto-remediation process, and how to review relevant logs.

---

### 1. Symptoms

*   **Alert Triggered:**  An alert notification is received from Azure Monitor indicating high CPU utilization (greater than 10%) for the WebApp. This notification might be received via email, SMS, or configured webhooks.
*   **WebApp Performance Degradation:** Users may experience slow response times, increased loading times, and potential errors when accessing the WebApp.
*   **Metrics:**  CPU percentage graphs in the Azure Portal show a sustained period of high CPU usage above the defined threshold (10%).  Other related metrics like Memory usage, Active Requests, and Response Time may also show anomalies.

### 2. Initial Assessment

*   **Acknowledge the Alert:** Acknowledge the alert in Azure Monitor to indicate that the issue is being investigated. This helps prevent multiple teams from working on the same problem simultaneously.
*   **Verify the Alert:** Confirm that the alert is genuine. Examine the CPU utilization metric in the Azure Portal for the WebApp to ensure it is indeed exceeding the threshold. Check the alert history for flapping (repeated triggering and resolution) which could indicate intermittent issues or a misconfigured alert rule.
*   **Check Associated Alerts:**  Look for other alerts related to the WebApp or its dependencies (e.g., database, storage) that may be contributing to the high CPU usage.

### 3. Troubleshooting Steps

**3.1. Monitor App Service Metrics:**

*   **Access Azure Portal:** Navigate to the Azure Portal: [https://portal.azure.com](https://portal.azure.com)
*   **Find the WebApp:** Locate your WebApp (`<YourWebAppName>`) within its Resource Group (`<YourResourceGroupName>`).
*   **Navigate to 'Monitoring' -> 'Metrics':**  This section displays a wealth of performance data.
*   **Key Metrics to Examine:**
    *   **CPU Percentage:** Confirm the high CPU usage reported by the alert.  Zoom in on the timeline to identify the exact period of high CPU usage.
    *   **Memory Percentage:** High memory usage can sometimes indirectly contribute to high CPU usage (e.g., due to frequent garbage collection).
    *   **Requests:**  Increased request rates can explain higher CPU usage. Look for sudden spikes or unexpected increases in traffic.
    *   **Average Response Time:** High response times often correlate with high CPU usage.
    *   **Threads:**  A large number of threads can indicate a potential threading issue, resource contention, or memory leak.  Monitor the thread count.
    *   **Handles:** A large number of handles could indicate resource leaks.
*   **Correlate Metrics:**  Look for correlations between different metrics. For example, a sudden spike in requests followed by high CPU and memory usage might point to a denial-of-service (DoS) attack or unexpected surge in legitimate traffic.

**3.2. Diagnose Performance Issues with App Service Diagnostics:**

*   **Access 'Diagnose and Solve Problems':**  In the WebApp's left-hand menu, click on "Diagnose and solve problems".
*   **Use the 'Performance' Tile:**  Select the "Performance" tile to access performance-related diagnostic tools.
*   **Explore Available Tools:**
    *   **CPU Analysis:**  This tool can identify the top CPU-consuming processes and threads within the WebApp.
    *   **Memory Analysis:**  Analyzes memory usage patterns to identify potential leaks or excessive memory allocation.
    *   **Dumps:**  Captures memory dumps of the WebApp process, which can be analyzed using tools like Visual Studio to identify the root cause of performance issues (requires familiarity with debugging and code analysis).
    *   **Profiler:** (Requires Azure App Service Premium plan) A powerful tool that allows you to profile the WebApp's code in real-time to identify performance bottlenecks.

**3.3. Check Application Logs:**

*   **Access 'App Service logs':**  In the WebApp's left-hand menu, under "Monitoring", click on "App Service logs".
*   **Enable Logging (if not already enabled):** Ensure that the necessary logging options are enabled.  At a minimum, enable "Application logging (Filesystem)" and configure the logging level to "Information" or "Warning".  Consider enabling "Detailed error messages" and "Failed request tracing" for more in-depth analysis, but be aware that these can generate a lot of logs.
*   **Examine Log Files:**  Navigate back to the WebApp Overview and go to **Advanced Tools** then select **Go**. You will now be in the Kudu Services page. Select **Debug console** then **CMD**. Browse to the `LogFiles` directory.  Examine the application logs (e.g., in the `LogFiles\Application` directory) for errors, warnings, or unusual activity that might be contributing to the high CPU usage.
    *   **Search for Errors/Exceptions:**  Look for any exceptions or error messages in the logs that might indicate a bug or issue in the application code.
    *   **Identify Slow Queries:**  If the application interacts with a database, look for slow-running queries in the logs that might be consuming excessive CPU resources.
    *   **Check for Loops or Recursive Calls:**  Examine the logs for patterns that might indicate infinite loops or excessively recursive function calls.
    *   **Review Audit Logs:** If auditing is enabled, review the audit logs for any suspicious activity that might be causing high CPU usage (e.g., unauthorized access attempts).

**3.4. Check Kudu Console (Advanced Users):**

*   **Access Kudu Console:** Navigate to the Kudu console by browsing to `<YourWebAppName>.scm.azurewebsites.net`.
*   **Process Explorer:** Use the Process Explorer to view running processes and their CPU/Memory usage.  Identify the process (w3wp.exe) associated with your WebApp and see which threads are consuming the most CPU. (This requires deeper debugging knowledge)
*   **Diagnostics:** Use the Kudu diagnostics tools to collect more detailed information about the WebApp's performance.

**3.5. Investigate Potential Security Issues:**

*   **Review Security Center Recommendations:**  Check the Azure Security Center for any security recommendations related to the WebApp.
*   **Monitor Network Traffic:** Analyze network traffic to the WebApp for any unusual patterns that might indicate a security breach (e.g., a Distributed Denial-of-Service (DDoS) attack).

### 4. Auto-Remediation

**4.1. Azure Function Triggered Restart:**

*   **Function Name:** `<YourRestartFunctionName>` (Replace with your Function App's Name)
*   **Function Resource Group:** `<YourFunctionResourceGroupName>` (Replace with your Function App's Resource Group)
*   **Mechanism:**  The Azure Monitor Alert triggers an Azure Function. This function is configured with an Managed Identity that has the Contributor role on the WebApp or using a Service Principal with appropriate permissions.  The function uses the Azure SDK to restart the WebApp.
*   **Function Code (Example - PowerShell):**

```powershell
param($request, $TriggerMetadata)

# Import the AzureRm module if it's not already imported
try {
    Import-Module AzureRM.Resources -Force
    Import-Module AzureRM.Websites -Force
}
catch {
    Write-Host "Error importing Azure modules: $($_.Exception.Message)"
    exit 1
}

# Get WebApp details from the Alert payload (assuming it's passed in the request body)
$AlertContext = ConvertFrom-Json -InputObject $request.Content

# Verify alert is for the target web app
if ($AlertContext.data.context.resourceName -notlike "*<YourWebAppName>*") {
  Write-Host "Alert is not for the specified web app. Exiting."
  exit 0
}

$ResourceGroupName = $AlertContext.data.context.resourceGroupName
$WebAppName = $AlertContext.data.context.resourceName

# Authenticate to Azure
try {
    Disable-AzureRMAlias -Scope Process
    Connect-AzureRmAccount -Identity
}
catch {
    Write-Host "Error authenticating to Azure: $($_.Exception.Message)"
    exit 1
}

# Restart the WebApp
try {
    Write-Host "Restarting Web App: $WebAppName in Resource Group: $ResourceGroupName"
    Restart-AzureRmWebApp -ResourceGroupName $ResourceGroupName -Name $WebAppName -Force
    Write-Host "Web App restarted successfully."
}
catch {
    Write-Host "Error restarting Web App: $($_.Exception.Message)"
    exit 1
}

Write-Host "Function completed."
```

*   **Trigger Configuration:** The Azure Function should be triggered by an "HTTP trigger" and secured with an "App Key" or configured with Managed Identity and RBAC roles.  The Azure Monitor Alert action group should be configured to call the Function's HTTP endpoint with the appropriate App Key (if used) in the header and the alert context in the body (JSON format).

**4.2. Monitor Function Execution:**

*   **Access Function App:** Navigate to the Azure Portal, find your Function App (`<YourRestartFunctionName>`), and go to the "Functions" blade.
*   **Select Function:** Select the specific function responsible for restarting the WebApp.
*   **Monitor 'Monitor' Blade:**  Review the "Monitor" blade to see the execution history of the function.  Check for any errors or failures in the function execution.  Examine the logs for details about the function execution.

**4.3. Post-Restart Verification:**

*   **WebApp Accessibility:** Verify that the WebApp is accessible after the restart. Try accessing the WebApp's URL in a browser.
*   **CPU Utilization:** Monitor the CPU utilization metric for the WebApp after the restart to ensure that it has returned to normal levels.
*   **Application Health:**  Check the WebApp's health endpoint (if configured) to ensure that the application is healthy.

### 5. Manual Intervention (If Auto-Remediation Fails)

If the auto-remediation fails to resolve the issue, manual intervention is required.

**5.1. Scaling Up the App Service Plan:**

*   **Access App Service Plan:** In the Azure Portal, navigate to the App Service Plan associated with your WebApp.
*   **Scale Up:**  Increase the size of the App Service Plan to provide more CPU and memory resources.  Consider using a higher pricing tier if necessary.  This should be a short-term fix while the root cause is found.

**5.2. Debugging Application Code (Advanced):**

*   **Remote Debugging:** Use Visual Studio or other debugging tools to remotely debug the application code running on the WebApp.  This allows you to step through the code and identify the source of the high CPU usage.
*   **Profiling:**  If you have an Azure App Service Premium plan, use the Profiler tool to profile the WebApp's code in real-time and identify performance bottlenecks.

**5.3. Scale Out (Horizontal Scaling):**

*   **Access Scale Out:**  In the WebApp's left-hand menu, click on "Scale out (App Service plan)".
*   **Configure Scale Out Rules:**  Configure scale-out rules based on CPU utilization or other metrics.  This will automatically add more instances of the WebApp when the CPU usage exceeds the configured threshold.

**5.4. Code Optimization:**

*   **Identify and Optimize Slow Queries:** If database queries are contributing to the high CPU usage, optimize the queries or database schema.
*   **Improve Application Code:** Review the application code for any performance bottlenecks, inefficient algorithms, or memory leaks.
*   **Implement Caching:** Implement caching to reduce the load on the WebApp and database.

### 6. Logs

*   **WebApp Application Logs (Filesystem):**  `/LogFiles/Application/`
*   **WebApp HTTP Logs:** `/LogFiles/http/RawLogs/`
*   **Kudu Logs:** Access the Kudu Console and navigate to the `LogFiles` directory.
*   **Azure Function Logs:**  Monitor the Azure Function's "Monitor" blade in the Azure Portal.  Configure Application Insights for the Function App for more detailed logging and monitoring.
*   **Azure Monitor Activity Logs:** Review the Azure Monitor Activity Logs for any events related to the WebApp or its dependencies.

### 7. Post-Incident Review

*   After resolving the incident, conduct a post-incident review to identify the root cause of the high CPU usage.
*   Document the root cause and the steps taken to resolve the issue.
*   Identify any preventative measures that can be taken to prevent similar incidents from occurring in the future.
*   Update this runbook with any new information or procedures learned during the incident.

### 8. Contact Information

*   **On-Call Engineer:** `<OnCallEngineerName>`
*   **Application Development Team:** `<AppDevTeamEmail>`
*   **Infrastructure Team:** `<InfraTeamEmail>`

---

**Note:** This runbook provides a general framework.  You may need to adapt it to your specific environment and application requirements. Remember to replace the placeholder values (e.g., `<YourWebAppName>`, `<YourResourceGroupName>`) with your actual values.  Regularly review and update this runbook to ensure it remains accurate and effective.  Consider using Infrastructure as Code (IaC) practices to automate the deployment and configuration of your Azure resources, including the Azure Function and Alert rules.
