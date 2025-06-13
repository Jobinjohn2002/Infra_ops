```markdown
# Azure Web App High CPU Usage Alert Runbook

**Alert:** AzureWebAppHighCPUUsage

**Threshold:** CPU Usage > 10%

**Impact:** Potential performance degradation for the web application, slow response times, potential errors.

**Target Audience:** Operations Team, DevOps Engineers, Application Support Team

**Document Version:** 1.0

---

## 1. Symptoms

*   **Elevated CPU usage:** Web App CPU metrics consistently exceeding the 10% threshold.
*   **Slow application response times:** Users experience delays when interacting with the web application.
*   **Application errors:** Potential timeouts, exceptions, or other errors due to resource constraints.
*   **High server response time:** Reported by application monitoring tools.
*   **Increased queue lengths:** If the Web App relies on background processing via queues, the queue length might increase.
*   **Degraded performance in dependent services:** The high CPU usage in the Web App might impact the performance of downstream services if they are dependent.

## 2. Troubleshooting

### 2.1. Initial Investigation

1.  **Acknowledge the Alert:** Acknowledge the alert in the monitoring system (e.g., Azure Monitor).
2.  **Verify the Alert:** Confirm that the alert is still active and the CPU usage remains high.
3.  **Check Azure Service Health:**  Rule out any underlying Azure platform issues that might be contributing to the problem:  [https://status.azure.com/](https://status.azure.com/)
4.  **Web App Overview Page:** Navigate to the Azure Web App in the Azure Portal.
    *   Review the **Overview** page. Look at the CPU percentage, memory percentage, and active requests chart. This provides a quick overview of the current resource utilization.
    *   Check the **Recent Operations** section to identify any recent deployments or configuration changes that might have triggered the high CPU usage.
5.  **App Service Diagnostics:** Use App Service Diagnostics to automatically analyze and diagnose common issues.
    *   In the Azure Portal, navigate to your Web App.
    *   In the left navigation, click **Diagnose and solve problems**.
    *   Use the available analyzers (e.g., **Performance Issues**, **Availability and Performance**, **Crash Diagnostics**) to identify potential root causes.  Pay close attention to CPU analysis results.

### 2.2. Detailed Investigation

1.  **Kudu (SCM) Console:** Access the Kudu (Service Control Manager) console for deeper insights.
    *   Go to `https://<your-web-app-name>.scm.azurewebsites.net/` (replace `<your-web-app-name>` with your Web App name).
    *   Authenticate with your Azure credentials (or deployment credentials if configured).
    *   **Process Explorer:** Use Process Explorer to identify the processes consuming the most CPU. This can help pinpoint the offending application code or external dependencies.
    *   **Debug Console (CMD/PowerShell):** Use the debug console to execute commands and gather additional information.
    *   **Environment:** Review environment variables for unexpected configurations.
    *   **Log Stream:**  Use the log stream in the Kudu console to see live logs from the application and potentially identify error messages related to the high CPU usage. This is more basic than Application Insights but good for quick checks.

2.  **Application Insights:** Use Application Insights for detailed performance monitoring and root cause analysis (if Application Insights is configured for the Web App).
    *   **Performance Blade:** Examine the **Performance** blade for slow requests, dependencies, and exceptions. Focus on requests with long duration.  Look for areas with high CPU time.
    *   **Live Metrics Stream:**  Use the Live Metrics Stream for near real-time monitoring of CPU usage, memory usage, requests, and exceptions. This helps visualize the impact of the high CPU usage on the application.
    *   **Profiler (if enabled):**  If the Application Insights Profiler is enabled, use it to capture detailed performance traces of the code. This helps pinpoint the exact lines of code that are consuming the most CPU.
    *   **Failure Analysis:**  Check for recent failures and related exceptions that could be causing the high CPU usage.
    *   **Dependencies:** Review the performance of the web app's dependencies (databases, APIs, etc.).  Slow dependency calls can often contribute to high CPU utilization.

3.  **Azure Monitor Metrics:** Analyze historical CPU usage data using Azure Monitor metrics explorer.
    *   Navigate to your Web App in the Azure Portal.
    *   In the left navigation, click **Metrics**.
    *   Select the **CPU Percentage** metric.
    *   Analyze the trend of CPU usage over time to identify patterns and correlations. Compare the current CPU usage with historical data.
    *   Check other relevant metrics like memory percentage, disk queue length, and network traffic.

4.  **Log Analytics:** Query application logs using Log Analytics if the Web App is configured to send logs to Log Analytics workspace.
    *   Use KQL (Kusto Query Language) to search for specific events, errors, or warnings that might be related to the high CPU usage.
    *   Example query:
        ```kusto
        AppServiceHTTPLogs
        | where TimeGenerated > ago(1h)
        | summarize count() by ResultDescription, bin(TimeGenerated, 5m)
        | render timechart
        ```
    *   Investigate custom logs emitted by the application to uncover potential issues.

### 2.3. Possible Root Causes

*   **Code Issues:**
    *   Inefficient code algorithms (e.g., nested loops, large data processing).
    *   Memory leaks leading to increased garbage collection activity.
    *   Excessive logging or tracing.
    *   Unoptimized database queries.
*   **Configuration Issues:**
    *   Incorrect application settings or configurations.
    *   Insufficient resources allocated to the Web App (e.g., small App Service Plan).
    *   High concurrency or traffic load.
*   **External Dependencies:**
    *   Slow or unresponsive external dependencies (databases, APIs, etc.).
    *   Network issues causing delays in communication with external services.
*   **Security Issues:**
    *   Malicious attacks or code injection leading to excessive CPU usage.  (Less likely if the web app is properly secured).
*   **Deployment Issues:**
    *   Recent deployments introducing performance regressions.

## 3. Auto-Remediation

**Mechanism:** Azure Function App triggered by the Azure Monitor Alert

**Function App Name:** `AutoRecoverWebAppCPU`

**Function Trigger:** HTTP Trigger (Webhook from Azure Monitor Alert)

**Function Code (PowerShell example):**

```powershell
param($Request, $TriggerMetadata)

# Replace with your Web App Name and Resource Group Name
$WebAppName = "your-web-app-name"
$ResourceGroupName = "your-resource-group-name"

# Log the alert details
Write-Host "Received Alert: $($Request.body)"

try {
    # Restart the Web App
    Write-Host "Restarting Web App: $WebAppName"
    Restart-AzWebApp -ResourceGroupName $ResourceGroupName -Name $WebAppName -Force

    Write-Host "Web App restarted successfully."

    #Optional: Write to Log Analytics for auditing and tracking
    #$LogAnalyticsWorkspaceId = "your-log-analytics-workspace-id"
    #$LogAnalyticsCustomLogName = "WebAppAutoRecovery"
    #$LogData = @{
    #    WebAppName = $WebAppName
    #    Action = "WebAppRestarted"
    #    AlertDetails = $Request.body
    #}
    #$LogData | ConvertTo-Json | Out-File -FilePath "C:\Temp\logdata.json"
    #Invoke-AzRestMethod -Path "/workspaces/$LogAnalyticsWorkspaceId/ingestion/dataCollections/$LogAnalyticsCustomLogName/json" -Method Post -Payload @{"body" = Get-Content -Path "C:\Temp\logdata.json"}
    #Remove-Item -Path "C:\Temp\logdata.json"
}
catch {
    Write-Error "Failed to restart Web App: $($_.Exception.Message)"
    throw
}

```

**Function Configuration:**

*   **Managed Identity:** Enable System Assigned Managed Identity for the Azure Function and grant it the `Contributor` role on the Web App's resource group. This allows the Function to restart the Web App.  (Alternatively, use a Service Principal).
*   **App Settings:**
    *   `AzureWebJobsStorage`:  The connection string for the Function App's storage account.
*   **PowerShell Modules:**  Make sure the `Az.Websites` module is available to the function.  This is usually configured during Function App creation.

**Azure Monitor Alert Rule Configuration:**

*   **Signal Logic:**
    *   **Signal:** CPU Percentage
    *   **Resource:** Your Azure Web App
    *   **Aggregation type:** Average
    *   **Aggregation granularity (period):** 1 Minute (adjust as needed)
    *   **Threshold:** Greater than
    *   **Threshold value:** 10
*   **Action Groups:**
    *   Create or use an existing Action Group that calls the Azure Function's HTTP trigger URL.  Use the `Webhook` action type.
    *   Configure the Action Group to include the alert payload in the webhook body using the `Enable common alert schema` option. This makes alert details accessible within the function.

**Auto-Remediation Workflow:**

1.  Azure Monitor detects that the Web App's CPU usage has exceeded the 10% threshold.
2.  Azure Monitor triggers the alert rule.
3.  The alert rule executes the Action Group, which makes an HTTP POST request to the Azure Function's trigger URL.
4.  The Azure Function receives the alert payload.
5.  The Azure Function authenticates and restarts the Web App using the `Restart-AzWebApp` cmdlet (or equivalent).
6.  The Azure Function logs the restart action.
7.  After the restart, the Web App should ideally return to a normal CPU usage level.
8.  The alert is automatically resolved by Azure Monitor (if the CPU usage drops below the threshold).

**Important Considerations for Auto-Remediation:**

*   **Impact:** Restarting a Web App can cause temporary service interruption.  Weigh the benefits of auto-remediation against the potential downtime.
*   **Escalation:** If auto-remediation fails to resolve the issue, the alert should be escalated to an on-call engineer.  Consider adding other actions to the Action Group, such as sending an email or SMS notification to the on-call engineer if the Function fails or the alert persists after the restart.
*   **Rate Limiting:** Implement rate limiting in the Azure Function to prevent excessive restarts in a short period.  For example, add a check to see if the Web App has been restarted recently and skip the restart if it has.
*   **Testing:** Thoroughly test the auto-remediation workflow in a non-production environment before deploying it to production.
*   **Monitoring:** Monitor the success rate of the auto-remediation workflow and investigate any failures.

## 4. Manual Remediation (If Auto-Remediation Fails or is not configured)

If the auto-remediation process fails or is not configured, follow these steps:

1.  **Restart the Web App Manually:**  Navigate to the Web App in the Azure Portal and click the **Restart** button. This is the first and simplest step to try.
2.  **Scale Up/Out:** If the Web App is consistently running at high CPU usage, consider scaling up the App Service Plan to a higher tier with more CPU resources or scaling out by increasing the number of instances.
    *   **Scale Up:** Change the App Service Plan to a higher pricing tier (e.g., from Standard to Premium).  This provides more CPU, memory, and other resources.
    *   **Scale Out:** Increase the instance count for the App Service Plan.  This distributes the load across multiple instances.  Enable auto-scaling based on CPU usage to automatically adjust the instance count.
3.  **Optimize Application Code:**  Address the identified code inefficiencies or performance bottlenecks.  This might involve:
    *   Optimizing database queries.
    *   Reducing memory leaks.
    *   Improving algorithm efficiency.
    *   Reducing logging verbosity.
4.  **Update Dependencies:**  Ensure that the Web App's dependencies are up-to-date.  Outdated dependencies can sometimes cause performance issues.
5.  **Review Application Configuration:**  Double-check the Web App's configuration settings to ensure that they are optimal for performance.
6.  **Investigate Third-Party Integrations:**  If the Web App integrates with third-party services, investigate whether any of these integrations are causing performance issues.
7.  **Rollback Deployments:** If the high CPU usage started after a recent deployment, consider rolling back to a previous version of the application.
8.  **Contact Microsoft Support:** If all other troubleshooting steps fail, contact Microsoft Support for assistance.  Provide them with detailed information about the issue, including the symptoms, troubleshooting steps taken, and any relevant logs.

## 5. Logs

*   **Azure Activity Log:** Track all management operations performed on the Web App (e.g., restarts, scale operations).
*   **App Service Logs:** Contains application logs, web server logs, and deployment logs.
    *   **Application Logs:**  Detailed logs generated by the application itself.  Enable application logging in the Azure Portal (App Service -> App Service Logs).
    *   **Web Server Logs (IIS Logs):** Logs generated by the IIS web server. Enable web server logging in the Azure Portal (App Service -> App Service Logs).  These logs can be helpful for identifying request patterns and errors.
    *   **Deployment Logs:** Logs generated during deployments. These logs can be helpful for troubleshooting deployment-related issues.
*   **Application Insights Logs:** Detailed telemetry data collected by Application Insights (if configured).
*   **Azure Function Logs:**  Logs generated by the auto-remediation Azure Function.  Monitor these logs to track the success rate of the auto-remediation process.  Use Application Insights for the function for more comprehensive logging.
*   **Kudu Console Logs (Log Stream):** Real-time log stream accessible through the Kudu console.

## 6. Prevention

*   **Proactive Monitoring:** Implement robust monitoring and alerting to detect and respond to performance issues before they impact users.
*   **Performance Testing:** Conduct regular performance testing to identify potential bottlenecks and performance regressions.
*   **Code Reviews:** Conduct thorough code reviews to ensure that the code is efficient and well-optimized.
*   **Configuration Management:**  Use configuration management tools to ensure that the Web App's configuration is consistent and optimal across environments.
*   **Continuous Integration and Continuous Delivery (CI/CD):**  Implement a CI/CD pipeline with automated testing to prevent performance regressions from being introduced into production.
*   **Resource Optimization:** Regularly review and optimize the Web App's resource utilization to ensure that it is not over-provisioned or under-provisioned.
*   **Security Hardening:** Implement security best practices to protect the Web App from malicious attacks that could lead to high CPU usage.
*   **Right-Sizing:** Choose the correct App Service Plan Tier based on the web app requirements.  Regularly review this plan to ensure it meets the growing demands of the application.
*   **Auto-Scaling:** Configure Auto-Scaling for the App Service Plan based on CPU usage.  This will dynamically adjust the number of instances based on load, preventing resource exhaustion.

---

This runbook provides a comprehensive guide for troubleshooting and resolving high CPU usage alerts in Azure Web Apps. Remember to customize the specific configurations and steps based on your environment and application requirements.  Regularly review and update this runbook to ensure its effectiveness.
```
