```markdown
# Azure WebApp High CPU Usage Alert & Auto-Recovery Runbook

**Document Version:** 1.0
**Last Updated:** October 26, 2023
**Author:** AI Assistant

## 1. Introduction

This runbook outlines the steps to take when an Azure WebApp triggers an alert indicating high CPU usage (above 10%). It provides guidance for investigating the issue, performing auto-remediation using an Azure Function, and gathering relevant logs for further analysis.

## 2. Alerting Information

*   **Alert Name:** WebAppHighCPUUsage
*   **Alert Description:** CPU usage for the Azure WebApp has exceeded 10%.
*   **Trigger Criteria:**
    *   Metric: `CpuPercentage`
    *   Resource: `<WebApp_Resource_Name>`
    *   Aggregation Type: `Average`
    *   Threshold: `10`
    *   Operator: `GreaterThan`
    *   Time Window: `5 Minutes`
*   **Severity:** Medium
*   **Notification Channels:** Email, PagerDuty (configure within Azure Monitor)
*   **Runbook Location:** This document
*   **Escalation Contact:** On-call engineer, team lead

## 3. Symptoms

*   Users experience slow response times when accessing the WebApp.
*   Increased error rates (HTTP 5xx errors).
*   WebApp resource utilization metrics (CPU, Memory) are high in Azure Monitor.
*   Potential delays in processing background tasks or scheduled jobs.
*   Increased latency in database queries, potentially due to CPU contention.

## 4. Troubleshooting

### 4.1 Initial Triage

1.  **Acknowledge the Alert:**  Acknowledge the alert in Azure Monitor to indicate that the issue is being investigated.

2.  **Verify the Alert:**
    *   Go to the Azure Portal: [https://portal.azure.com/](https://portal.azure.com/)
    *   Navigate to **Monitor** > **Alerts**.
    *   Find the `WebAppHighCPUUsage` alert instance.
    *   Confirm that the alert is active and the CPU usage is above the threshold.
    *   Check the timestamp of the alert to understand when the issue started.

3.  **Check Azure Service Health:** Before proceeding, check the Azure Service Health dashboard for any known Azure-wide issues that might be affecting the WebApp.  Navigate to the Azure Portal and select "Service Health".

4.  **WebApp Overview Blade:**
    *   Navigate to your WebApp in the Azure Portal.
    *   Review the **Overview** blade for a quick snapshot of CPU usage, memory usage, and other key metrics.
    *   Look for any recent deployments or configuration changes that might have contributed to the increased CPU usage.

### 4.2 Detailed Investigation

1.  **Azure Metrics Explorer:**
    *   Navigate to your WebApp in the Azure Portal.
    *   Select **Metrics** under **Monitoring**.
    *   **Select Metric:** Choose `CpuPercentage`, `MemoryPercentage`, `Http Queue Length`, `Requests`.
    *   **Aggregation:**  `Average`, `Maximum`, `Sum` (experiment to understand the trend)
    *   **Time Range:** Start with the time range when the alert triggered and expand as needed.
    *   **Investigate:**
        *   **CPU Percentage:** Confirm sustained high CPU usage.
        *   **Memory Percentage:** High memory usage can contribute to CPU load.
        *   **Http Queue Length:** A growing queue length indicates the WebApp is unable to handle incoming requests quickly, potentially due to CPU bottlenecks.
        *   **Requests:** Monitor request volume; a sudden spike in requests could be the root cause.

2.  **Kudu Console (Advanced Tools):**
    *   Navigate to your WebApp in the Azure Portal.
    *   Select **Advanced Tools** under **Development Tools**.
    *   Click **Go**. This will open the Kudu console in a new browser tab.
    *   **Process Explorer:**
        *   Navigate to **Process Explorer**.
        *   Identify the process(es) consuming the most CPU.  Look for your application's main process and any related worker processes.
    *   **Debug Console (CMD or PowerShell):**
        *   Navigate to **Debug console** > **CMD** or **PowerShell**.
        *   Use command-line tools to investigate further (examples below).

    *   **Collect a Memory Dump (if applicable):** If you suspect a memory leak is contributing to CPU usage, you can collect a memory dump using Kudu.  Analyze the dump with tools like Visual Studio or DebugDiag to identify the source of the leak.  This requires a more in-depth debugging skillset.

3.  **Application Insights (if configured):**
    *   If Application Insights is integrated with your WebApp, use it to analyze request performance, dependencies, and exceptions.
    *   **Performance Blade:** Identify slow-running requests or operations that are consuming significant CPU time.
    *   **Live Metrics Stream:** Get a real-time view of key metrics, including CPU usage, request rates, and dependency calls.
    *   **Exceptions Blade:** Look for any exceptions that might be contributing to the increased CPU load.  Exceptions often indicate code issues or resource constraints.
    *   **Profiler:** If available, use the Profiler to collect detailed traces of your application's execution.  This can help identify specific lines of code that are causing performance bottlenecks.

4.  **Log Stream:**
    *   Navigate to your WebApp in the Azure Portal.
    *   Select **Log stream** under **Monitoring**.
    *   Observe the real-time logs to identify any errors, warnings, or unusual activity. Filter by severity level to focus on critical issues.

### 4.3 Command-Line Examples (Kudu Console)

*   **Check CPU usage by process (PowerShell):**

    ```powershell
    Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 | Format-Table ID, ProcessName, CPU, WorkingSet -AutoSize
    ```

*   **Get the list of running processes (CMD):**

    ```cmd
    tasklist
    ```

*   **Check the contents of the application's log directory (CMD):**

    ```cmd
    dir d:\home\LogFiles
    ```

*   **Show environment variables (CMD):**

    ```cmd
    set
    ```

## 5. Auto-Remediation

This section describes the auto-remediation process using an Azure Function to restart the WebApp.

### 5.1 Azure Function Details

*   **Function Name:** RestartWebAppFunction
*   **Resource Group:** `<Resource_Group_Name>`
*   **Function App Name:** `<Function_App_Name>`
*   **Trigger:** HTTP Trigger (Can also be triggered by a Logic App based on the Alert)
*   **Authentication:** Managed Identity (Recommended) or Service Principal with appropriate permissions to restart the WebApp.
*   **Function Code (Example C#):**

    ```csharp
    using System;
    using Microsoft.AspNetCore.Mvc;
    using Microsoft.Azure.WebJobs;
    using Microsoft.Azure.WebJobs.Extensions.Http;
    using Microsoft.AspNetCore.Http;
    using Microsoft.Extensions.Logging;
    using Azure.Identity;
    using Azure.ResourceManager;
    using Azure.ResourceManager.AppService;
    using Azure.ResourceManager.Resources;

    public static class RestartWebAppFunction
    {
        [FunctionName("RestartWebAppFunction")]
        public static async Task<IActionResult> Run(
            [HttpTrigger(AuthorizationLevel.Function, "get", "post", Route = null)] HttpRequest req,
            ILogger log)
        {
            log.LogInformation("RestartWebAppFunction triggered.");

            // Replace with your WebApp's details
            string subscriptionId = "<Subscription_ID>";
            string resourceGroupName = "<Resource_Group_Name>";
            string webAppName = "<WebApp_Resource_Name>";

            try
            {
                // Authenticate using Managed Identity
                var credential = new DefaultAzureCredential();
                var armClient = new ArmClient(credential, subscriptionId);

                // Get the Resource Group
                ResourceGroupResource resourceGroup = await armClient.GetResourceGroupAsync(resourceGroupName);

                // Get the WebApp
                WebSiteResource webApp = await resourceGroup.GetWebSiteAsync(webAppName);

                // Restart the WebApp
                await webApp.RestartAsync();
                log.LogInformation($"WebApp {webAppName} restarted successfully.");

                return new OkObjectResult($"WebApp {webAppName} restarted successfully.");
            }
            catch (Exception ex)
            {
                log.LogError($"Error restarting WebApp: {ex.Message}");
                return new BadRequestObjectResult($"Error restarting WebApp: {ex.Message}");
            }
        }
    }
    ```

*   **Function Configuration:**
    *   **Managed Identity:**  Enable System-assigned managed identity for the Function App.  Grant the managed identity the `Contributor` role or a custom role with `Microsoft.Web/sites/restart/action` permission on the WebApp resource or resource group.
    *   **Subscription ID:**  Configure the `SubscriptionId` as an App Setting.  This allows the function to know which subscription to operate within.

### 5.2 Execution

1.  **Alert Action Group:** The `WebAppHighCPUUsage` alert should be configured to trigger an Action Group.
2.  **Action Group Configuration:** The Action Group should be configured to call the `RestartWebAppFunction` via an HTTP Webhook action.  Use the Function's HTTP Trigger URL (obtainable from the Azure Function Portal).  Consider using Key Vault to store the Function's key (if using Function-level authentication).
3.  **Verification:** After the alert triggers and the Action Group executes, verify the following:
    *   The Azure Function execution history shows a successful execution.
    *   The WebApp has been restarted (check the WebApp's activity log in the Azure Portal).
    *   The CPU usage has decreased after the restart.
    *   End-users can access the WebApp successfully.

### 5.3 Important Considerations

*   **Authentication:**  Using Managed Identity is highly recommended for security.  Avoid storing credentials directly in the Function code or configuration.
*   **Idempotency:**  Design the Function to be idempotent, meaning it can be executed multiple times without causing unintended side effects.  In this case, restarting a WebApp that is already restarting is generally safe.
*   **Error Handling:** Implement robust error handling in the Function code to catch exceptions and log relevant information.  Consider retrying the restart operation if it fails initially.
*   **Monitoring:** Monitor the Azure Function itself to ensure it is healthy and executing correctly.
*   **Cooldown Period:** After a successful restart, consider implementing a cooldown period before allowing the Action Group to trigger the Function again. This can prevent excessive restarts if the underlying issue persists.  This can be done with the Action Group settings.
*   **Alternatives:** Consider scaling out the WebApp instead of restarting it as a recovery option.  This may be a better solution for high-traffic applications. However, this may have a financial implication.
*   **Logging:** Ensure the function logs successful and unsuccessful attempts to restart the WebApp, including timestamps and relevant error messages.

## 6. Logs

Collect logs from the following sources for further analysis:

*   **Azure Monitor Activity Log:** Tracks all operations performed on the WebApp, including restarts.
    *   Go to the Azure Portal: [https://portal.azure.com/](https://portal.azure.com/)
    *   Navigate to **Monitor** > **Activity log**.
    *   Filter by resource type (`Microsoft.Web/sites`) and operation type (`Restart Web Site`).
*   **WebApp Logs:** Collect logs generated by your application.
    *   **Log Stream (Azure Portal):** Provides real-time access to the application logs.
    *   **Log Files (Kudu Console):** Logs are typically stored in `d:\home\LogFiles`.
    *   **Azure Blob Storage (if configured):**  You can configure the WebApp to stream logs to Azure Blob Storage for long-term retention and analysis.
*   **Azure Function Logs:** Collect logs generated by the `RestartWebAppFunction`.
    *   Navigate to your Function App in the Azure Portal.
    *   Select **Monitor** under **Monitoring**.
    *   View the invocation history and function logs for each execution.
    *   Enable Application Insights for the Function App for more detailed monitoring and analysis.
*   **Application Insights (if configured):** Provides detailed telemetry data for your application, including request performance, exceptions, and dependencies.  Search for the timestamps around the alert triggering.
*   **IIS Logs:** IIS logs can provide information about requests to the WebApp, which can be useful for identifying patterns and troubleshooting issues.
    *   Located in `d:\home\LogFiles\http\RawLogs` (accessible via Kudu).

## 7. Root Cause Analysis

After resolving the immediate issue, perform a root cause analysis to identify the underlying cause of the high CPU usage. Consider the following:

*   **Code Issues:**  Inefficient algorithms, memory leaks, or unoptimized database queries.
*   **Resource Constraints:**  Insufficient resources (CPU, memory) allocated to the WebApp.  Consider scaling up or scaling out the App Service Plan.
*   **Increased Traffic:** A sudden surge in user traffic.
*   **External Dependencies:**  Slow or unreliable external services or databases.
*   **Configuration Issues:**  Incorrect or suboptimal WebApp configuration settings.
*   **Security Vulnerabilities:**  Malicious attacks or vulnerabilities that are consuming resources.

## 8. Prevention

Implement the following measures to prevent future occurrences of high CPU usage:

*   **Code Optimization:** Regularly review and optimize application code to improve performance.
*   **Performance Testing:** Conduct load and performance testing to identify bottlenecks and areas for improvement.
*   **Resource Monitoring:** Continuously monitor WebApp resource utilization metrics using Azure Monitor.
*   **Auto-Scaling:** Configure auto-scaling rules to automatically scale out the WebApp based on CPU usage or other metrics.
*   **Caching:** Implement caching mechanisms to reduce database load and improve response times.
*   **Security Audits:** Regularly perform security audits to identify and address potential vulnerabilities.
*   **Update Dependencies:** Keep application dependencies up-to-date to benefit from performance improvements and security patches.
*   **Proactive Scaling:** If predictable traffic increases are expected, proactively scale the App Service Plan *before* the traffic spike.

## 9. Escalation

If the auto-remediation fails to resolve the issue, or if the issue persists after the WebApp restart, escalate the incident to the on-call engineer or team lead according to the escalation contact information provided in the Alerting Information section. Provide all collected logs and troubleshooting steps performed.

## 10. Appendix

*   **Azure Monitor Documentation:** [https://docs.microsoft.com/en-us/azure/azure-monitor/](https://docs.microsoft.com/en-us/azure/azure-monitor/)
*   **Azure Web Apps Documentation:** [https://docs.microsoft.com/en-us/azure/app-service/](https://docs.microsoft.com/en-us/azure/app-service/)
*   **Azure Functions Documentation:** [https://docs.microsoft.com/en-us/azure/azure-functions/](https://docs.microsoft.com/en-us/azure/azure-functions/)
*   **Kudu Console Documentation:** [https://github.com/projectkudu/kudu/wiki](https://github.com/projectkudu/kudu/wiki)
*   **Azure Resource Manager (ARM) Documentation:** [https://docs.microsoft.com/en-us/azure/azure-resource-manager/](https://docs.microsoft.com/en-us/azure/azure-resource-manager/)

**Note:** This runbook provides a general framework. You may need to customize it to fit your specific environment and application requirements. Replace the placeholder values (e.g., `<WebApp_Resource_Name>`, `<Subscription_ID>`, `<Resource_Group_Name>`, `<Function_App_Name>`) with the actual values for your resources. Remember to test this runbook in a non-production environment before implementing it in production.  Always exercise caution when making changes to production systems.
```
