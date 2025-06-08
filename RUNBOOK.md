```markdown
# Azure WebApp High CPU Usage Alert & Auto-Recovery Runbook

**Service:** Azure WebApp
**Alert:** High CPU Usage (>10%)
**Auto-Recovery:** Azure Function App Restart
**Document Version:** 1.0
**Last Updated:** 2023-10-27
**Author:** AI Assistant

## 1. Introduction

This runbook details the process for responding to an Azure Monitor alert indicating high CPU usage (greater than 10%) for an Azure WebApp. It outlines the symptoms, troubleshooting steps, automated remediation via an Azure Function App, and where to find relevant logs. The goal is to quickly mitigate the impact of high CPU usage and restore normal application performance.

## 2. Symptoms

*   **User-Reported Issues:**
    *   Slow application response times
    *   Application timeouts or errors
    *   Inability to access certain application features
    *   Intermittent application availability
*   **Alert Indication:**
    *   Azure Monitor alert triggered: "WebApp CPU Usage High"
    *   Alert details include: WebApp name, resource group, timestamp, and CPU percentage.
*   **Performance Metrics:**
    *   High CPU usage (>10%) consistently reported in Azure Monitor.
    *   Increased average response time for WebApp requests.
    *   High number of requests in the queue (if applicable).
    *   Increased memory consumption.

## 3. Troubleshooting Steps

Before triggering the auto-remediation, verify the alert and try basic investigation steps:

1.  **Confirm the Alert:**
    *   Check the Azure Monitor alert rule configuration to ensure the alert threshold is correctly set (10% CPU).
    *   Verify the alert is indeed triggered by the correct WebApp instance.
    *   Examine the alert history to see how long the high CPU usage has persisted.

2.  **Azure Portal Investigation:**
    *   **Azure Monitor Metrics:**
        *   Navigate to the WebApp in the Azure Portal.
        *   Go to the "Monitoring" section and select "Metrics".
        *   Check the following metrics:
            *   `CpuPercentage`: Verify the current CPU percentage matches the alert.
            *   `Requests`: Monitor the number of incoming requests. A sudden spike could be contributing to high CPU.
            *   `AverageResponseTime`: Check for increased latency.
            *   `MemoryWorkingSet`: Investigate memory usage.  High memory usage can lead to increased CPU usage.
        *   Set the time range to match the duration of the alert.
    *   **App Service Diagnostics:**
        *   Navigate to the WebApp in the Azure Portal.
        *   Go to "Diagnose and solve problems".
        *   Run the following diagnostics:
            *   "CPU Analysis" - This can identify CPU-intensive requests or processes.
            *   "Performance Issues" - This provides insights into performance bottlenecks.
    *   **Process Explorer (Kudu):**
        *   Navigate to the Kudu console of the WebApp: `https://<your-webapp-name>.scm.azurewebsites.net`
        *   Go to "Process Explorer".
        *   Identify the processes consuming the most CPU.  This might indicate a specific application component causing the issue (e.g., a long-running SQL query, a memory leak, etc.).  Note the process ID (PID) for further investigation.

3.  **Remote Debugging (If Applicable):**
    *   If enabled, connect a remote debugger to the WebApp to further analyze the CPU-intensive processes. This allows you to step through the code and identify the root cause of the problem.  This requires proper setup and credentials.

4.  **Check Application Logs:**
    *   Review application logs (configured in the WebApp settings) for any errors, warnings, or exceptions that might be contributing to the high CPU usage.  Common locations include:
        *   Azure Storage Blob logs (if configured)
        *   Application Insights logs (if integrated)
        *   Standard output/error logs
    *   Look for patterns or recurring errors that correlate with the high CPU usage period.

## 4. Auto-Remediation Steps (Azure Function App Restart)

If the CPU usage remains above 10% after the initial investigation, proceed with the automated remediation:

1.  **Trigger the Azure Function App:**
    *   The Azure Monitor alert should be configured to automatically trigger the Azure Function App.  Verify the connection between the alert rule and the function app is active.
    *   **Function App Name:** `YourWebAppRestartFunction` (Example, adjust accordingly)
    *   **Resource Group:** `YourResourceGroup` (Example, adjust accordingly)
    *   **Function App Endpoint (If not triggered automatically, manual execution option):**  `https://yourwebrestartfunction.azurewebsites.net/api/RestartWebAppFunction?code=YOUR_FUNCTION_KEY&webappName=YOUR_WEBAPP_NAME&resourceGroupName=YOUR_RESOURCE_GROUP` (Replace placeholders.  The code is the function's authorization key, which can be found in the Azure Portal under the Function App -> Function -> App Keys).
2.  **Function App Logic:** (This is a simplified example; adapt to your specific environment)

    ```csharp
    #r "Newtonsoft.Json"

    using System;
    using Microsoft.AspNetCore.Mvc;
    using Microsoft.Azure.WebJobs;
    using Microsoft.Azure.WebJobs.Extensions.Http;
    using Microsoft.AspNetCore.Http;
    using Microsoft.Extensions.Logging;
    using Newtonsoft.Json;
    using Microsoft.Azure.Management.WebSites.Models;
    using Microsoft.Azure.Management.WebSites;
    using Microsoft.Rest;
    using Microsoft.Azure.Services.AppAuthentication;

    public static class RestartWebAppFunction
    {
        [FunctionName("RestartWebAppFunction")]
        public static async Task<IActionResult> Run(
            [HttpTrigger(AuthorizationLevel.Function, "get", "post", Route = null)] HttpRequest req,
            ILogger log)
        {
            log.LogInformation("C# HTTP trigger function processed a request.");

            string webappName = req.Query["webappName"];
            string resourceGroupName = req.Query["resourceGroupName"];

            string requestBody = await new StreamReader(req.Body).ReadToEndAsync();
            dynamic data = JsonConvert.DeserializeObject(requestBody);
            webappName = webappName ?? data?.webappName;
            resourceGroupName = resourceGroupName ?? data?.resourceGroupName;

            if (string.IsNullOrEmpty(webappName) || string.IsNullOrEmpty(resourceGroupName))
            {
                return new BadRequestObjectResult("Please pass webappName and resourceGroupName in the query string or in the request body");
            }

            try
            {
                // Authenticate to Azure using Managed Identity or Service Principal
                var azureServiceTokenProvider = new AzureServiceTokenProvider();
                string accessToken = await azureServiceTokenProvider.GetAccessTokenAsync("https://management.azure.com/");
                var creds = new TokenCredentials(accessToken);

                // Create a WebSites client
                var webSiteClient = new WebSiteManagementClient(creds);
                webSiteClient.SubscriptionId = Environment.GetEnvironmentVariable("SubscriptionId"); // Replace with your subscription ID or set as App Setting

                // Restart the Web App
                log.LogInformation($"Restarting WebApp: {webappName} in Resource Group: {resourceGroupName}");
                await webSiteClient.WebApps.RestartAsync(resourceGroupName, webappName);
                log.LogInformation($"WebApp: {webappName} restarted successfully.");

                return new OkObjectResult($"WebApp {webappName} restarted successfully.");
            }
            catch (Exception ex)
            {
                log.LogError($"Error restarting WebApp: {webappName}. Error: {ex.Message}");
                return new StatusCodeResult(StatusCodes.Status500InternalServerError); // Return 500 for failures
            }
        }
    }
    ```

    *   **Important:**
        *   Replace `YOUR_FUNCTION_KEY`, `YOUR_WEBAPP_NAME`, and `YOUR_RESOURCE_GROUP` placeholders with the actual values.
        *   Set the `SubscriptionId` environment variable in the Function App's configuration.
        *   Configure Managed Identity for the Function App or use a Service Principal for authentication to manage Azure resources.  The example code uses Managed Identity via the `AzureServiceTokenProvider`.
        *   Ensure the Function App has the necessary permissions (e.g., Contributor role) on the WebApp to perform the restart operation.
3.  **Monitor the Function App Execution:**
    *   Check the Function App's logs in the Azure Portal (Function App -> Monitor) to ensure it executed successfully and restarted the WebApp.
    *   Look for any errors or exceptions during the function execution.

4.  **Verify WebApp Recovery:**
    *   After the Function App executes, monitor the WebApp's CPU usage in Azure Monitor.
    *   Verify the CPU usage has decreased to acceptable levels (below 10%).
    *   Confirm the application is responsive and functioning correctly.

## 5. Logs

*   **Azure Monitor Alert Logs:**
    *   Azure Portal -> Monitor -> Alerts -> History
    *   Provides details of when the alert was triggered and its severity.
*   **WebApp Application Logs:**
    *   Location depends on the configured logging settings:
        *   Azure Storage Blob logs: Azure Portal -> WebApp -> App Service logs
        *   Application Insights logs: Azure Portal -> Application Insights -> Search/Logs
        *   Standard output/error logs: Kudu console -> Debug console -> LogFiles
    *   Search for errors, warnings, and exceptions that occurred during the high CPU usage period.
*   **WebApp System Logs:**
    *   Kudu console -> Debug console -> LogFiles
    *   Provides information about system events and errors.
*   **Azure Function App Logs:**
    *   Azure Portal -> Function App -> Monitor
    *   Provides logs for the Function App execution, including successful restarts and any errors encountered.  Use Application Insights integrated with the Function App for more detailed logging.
*   **Kudu Console Logs:**
    *   `https://<your-webapp-name>.scm.azurewebsites.net/DebugConsole`
    *   Useful for debugging deployment issues and accessing application logs.

## 6. Escalation

If the auto-remediation fails to resolve the high CPU usage within a reasonable timeframe (e.g., 30 minutes) or if the underlying cause is not immediately apparent, escalate the issue to the next level of support:

1.  **Escalate to:** [Your Team Name/Contact Person]
2.  **Provide the following information:**
    *   Alert details (WebApp name, resource group, timestamp, CPU percentage)
    *   Troubleshooting steps taken
    *   Results of the auto-remediation
    *   Relevant logs (application logs, Function App logs)
    *   Any observations or patterns identified

## 7. Root Cause Analysis

After the incident is resolved, conduct a root cause analysis to determine the underlying cause of the high CPU usage. This may involve:

*   Analyzing application code for performance bottlenecks.
*   Optimizing database queries.
*   Scaling up the WebApp service plan (if resources are consistently insufficient).
*   Identifying and addressing any security vulnerabilities.
*   Reviewing application architecture and identifying areas for improvement.

## 8. Preventative Measures

Based on the root cause analysis, implement preventative measures to prevent similar incidents from occurring in the future. These measures may include:

*   Implementing code optimizations and performance testing.
*   Scaling up the WebApp service plan proactively.
*   Setting up more granular monitoring and alerting rules.
*   Implementing security best practices to prevent attacks.
*   Automating deployments and configuration management.

## 9. Configuration Settings

*   **WebApp CPU Usage Alert Rule:**
    *   **Metric:** `CpuPercentage`
    *   **Threshold:** 10%
    *   **Aggregation Type:** Average
    *   **Aggregation Granularity:** 5 minutes
    *   **Evaluation Frequency:** 1 minute
    *   **Action Group:** Triggers the Azure Function App.
*   **Azure Function App:**
    *   **Function App Name:** `YourWebAppRestartFunction` (Example, adjust accordingly)
    *   **Runtime Stack:**  .NET (or relevant stack)
    *   **Authentication:** Managed Identity or Service Principal (recommended)
    *   **Permissions:** Contributor role on the WebApp
    *   **SubscriptionId:** Set as an App Setting
*   **WebApp Logging:**
    *   Enabled and configured to collect relevant application logs.

## 10. Appendices

*   **Azure Monitor Alert Rule Configuration:**  Screenshot of the alert rule configuration.
*   **Azure Function App Code (Full Version):**  Full, commented code of the restart function.
*   **Troubleshooting Checklist:** A printable checklist of the troubleshooting steps outlined in this runbook.
