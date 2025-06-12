```markdown
# Azure Web App High CPU Alert Runbook

This runbook outlines the steps to diagnose and remediate a high CPU usage alert for an Azure Web App. This alert triggers when the CPU usage exceeds 10% for a sustained period. This runbook incorporates an automated remediation step using an Azure Function that restarts the Web App to quickly restore service.

**Alert Name:** WebAppCPUHigh

**Trigger Condition:** CPU Percentage > 10% (Sustained)

**Severity:** Medium

**Owner:** Infrastructure/Development Team

## 1. Symptoms

Users may experience the following symptoms:

*   Slow page load times or general application slowness.
*   Application unresponsive or timing out.
*   Increased latency for API calls.
*   Error messages related to resource exhaustion (e.g., 503 Service Unavailable errors).
*   Possible application crashes or restarts (if CPU usage gets extremely high).

## 2. Troubleshooting

**2.1 Initial Investigation**

*   **Confirm the Alert:** Verify the alert in Azure Monitor, checking the actual CPU percentage and the duration it has been exceeding the threshold.  Check for the exact timestamp of the alert trigger and duration.
*   **Azure Portal Overview:** Navigate to the affected Web App in the Azure Portal.
    *   **Overview Blade:** Review the **CPU Percentage**, **Memory Percentage**, and **Requests** charts on the Overview blade.  Look for any spikes or anomalies around the time the alert triggered.
    *   **Diagnose and Solve Problems Blade:** Use the "Diagnose and Solve Problems" tool. This can automatically detect common issues related to high CPU and suggest solutions. Check sections like "Availability and Performance".
    *   **Metrics Blade:**
        *   Add metrics for **CPU Percentage**, **Memory Percentage**, **Requests**, **HTTP Server Errors**, **Data Out**, and **Average Response Time**.
        *   Increase the time range to at least 1 hour before and after the alert trigger time. This provides context for the CPU spike.
        *   **Correlation:** Look for correlations between CPU spikes and other metrics like increased requests, memory pressure, or errors.
*   **Application Insights (If configured):**
    *   Review the **Performance** section for slow requests, slow dependencies, and any exceptions being thrown.
    *   Check the **Live Metrics Stream** to get real-time CPU usage, request rates, and other telemetry.
    *   Use **Profiler** to collect detailed traces of the CPU-intensive code paths. (Ensure profiler is enabled and configured.)

**2.2 Detailed Investigation**

*   **Kudu (SCM) Site:** Access the Kudu (SCM) site for the Web App using `https://<your-webapp-name>.scm.azurewebsites.net`.
    *   **Process Explorer:** Check the Process Explorer to identify which processes are consuming the most CPU.  Look for w3wp.exe (the worker process for IIS), dotnet.exe (if it's a .NET app), node.exe (if it's a Node.js app), or any other unexpected processes. Note the process ID (PID) of the high CPU-consuming process.
    *   **CMD/PowerShell:** Use the command line interface to investigate further.
        *   `top`:  Use this command (available in the console) to display a real-time list of processes and their CPU usage.
        *   `ps -aux`: (for Linux based apps) Similar to `top`, provides detailed process information.

*   **Web App Diagnostics Logs:**
    *   Enable **Application Logging (Filesystem or Blob Storage)**, **Web Server Logging (Storage)**, and **Detailed Error Messages (Filesystem or Blob Storage)** in the Web App's Diagnostic Logs section.
    *   Review these logs for errors, exceptions, or warnings that may be contributing to the high CPU usage. Pay special attention to the timestamps around the alert trigger.
    *   Look for patterns in the logs that correlate with the CPU spikes.

**2.3 Potential Causes**

*   **Code Issues:**
    *   **Inefficient Algorithms:**  Code using inefficient algorithms or performing complex calculations.
    *   **Memory Leaks:**  Code that leaks memory can lead to increased CPU usage as the garbage collector works harder.
    *   **Deadlocks or Threading Issues:**  Concurrency problems can cause CPU spikes.
    *   **Long-Running Synchronous Operations:**  Blocking I/O operations can tie up threads and increase CPU usage.
*   **External Dependencies:**
    *   **Slow Database Queries:**  Slow database queries can put a strain on the application and increase CPU usage.
    *   **Network Latency:**  High network latency to external services can cause delays and increase CPU usage.
    *   **API Throttling:**  Being throttled by external APIs can lead to retries and increased CPU load.
*   **Traffic Spikes:**  A sudden increase in traffic can overwhelm the application and cause CPU spikes.
*   **Denial of Service (DoS) Attacks:**  A DoS attack can flood the application with requests, leading to high CPU usage.
*   **Configuration Issues:**
    *   **Incorrect Connection String:**  An invalid connection string can cause the application to repeatedly try to connect to the database, increasing CPU usage.
    *   **Excessive Logging:**  Overly verbose logging can consume significant CPU resources.
*   **Platform Issues:**
    *   **Outdated SDKs/Frameworks:**  Using outdated SDKs or frameworks can expose the application to performance issues.
    *   **Under-Provisioned App Service Plan:** The chosen service plan does not provide enough resources for the application's workload.

## 3. Auto-Remediation

The following auto-remediation action will be triggered by the alert:

*   **Action:** Restart the Web App.
*   **Mechanism:** Azure Function triggered by the Azure Monitor Alert.
*   **Azure Function Details:**

    *   **Function App Name:** `[YourFunctionAppName]`
    *   **Function Name:** `RestartWebApp`
    *   **Trigger:** HTTP Trigger (WebHook from Azure Monitor Alert)
    *   **Required Permissions:** The Function App's Managed Identity (System Assigned) or a Service Principal needs the `Microsoft.Web/sites/restart/action` permission on the targeted Web App.

    **Example Azure Function (C# - .NET 6):**

    ```csharp
    using System;
    using System.IO;
    using System.Threading.Tasks;
    using Microsoft.AspNetCore.Mvc;
    using Microsoft.Azure.WebJobs;
    using Microsoft.Azure.WebJobs.Extensions.Http;
    using Microsoft.AspNetCore.Http;
    using Microsoft.Extensions.Logging;
    using Newtonsoft.Json;
    using Azure.Identity;
    using Azure.ResourceManager;
    using Azure.ResourceManager.AppService;
    using Azure.ResourceManager.AppService.Models;

    public static class RestartWebApp
    {
        [FunctionName("RestartWebApp")]
        public static async Task<IActionResult> Run(
            [HttpTrigger(AuthorizationLevel.Function, "post", Route = null)] HttpRequest req,
            ILogger log)
        {
            log.LogInformation("RestartWebApp function triggered.");

            string requestBody = await new StreamReader(req.Body).ReadToEndAsync();
            dynamic data = JsonConvert.DeserializeObject(requestBody);

            // Extract necessary information from the Azure Monitor Alert payload
            string webAppName = data?.data?.context?.resourceName;
            string resourceGroupName = data?.data?.context?.resourceGroupName;
            string subscriptionId = data?.data?.context?.subscriptionId;

            log.LogInformation($"Web App Name: {webAppName}");
            log.LogInformation($"Resource Group Name: {resourceGroupName}");
            log.LogInformation($"Subscription ID: {subscriptionId}");

            if (string.IsNullOrEmpty(webAppName) || string.IsNullOrEmpty(resourceGroupName) || string.IsNullOrEmpty(subscriptionId))
            {
                log.LogError("Missing required information from the alert payload.");
                return new BadRequestObjectResult("Missing required information from the alert payload.");
            }

            try
            {
                // Authenticate to Azure using Managed Identity or Service Principal
                var credential = new DefaultAzureCredential();
                var armClient = new ArmClient(credential, subscriptionId);

                // Get the resource group
                var resourceGroupResource = armClient.GetResourceGroupResource(Azure.Core.ResourceIdentifier.Create(subscriptionId, resourceGroupName));
                var webAppCollection = resourceGroupResource.GetWebApps();
                var webAppResource = await webAppCollection.GetAsync(webAppName);

                //Restart the webapp
                await webAppResource.Value.RestartAsync();

                log.LogInformation($"Successfully restarted Web App: {webAppName}");
                return new OkObjectResult($"Successfully restarted Web App: {webAppName}");

            }
            catch (Exception ex)
            {
                log.LogError($"Error restarting Web App: {webAppName}. Error: {ex.Message}");
                return new StatusCodeResult(500); //InternalServerError
            }
        }
    }
    ```

    **Configuration:**

    *   **Function App Settings:**
        *   Ensure the `FUNCTIONS_EXTENSION_VERSION` app setting is set to `~4` or higher (depending on your .NET version).
        *   Configure the Managed Identity or Service Principal with the appropriate role assignment (Contributor or custom role).
    *   **Azure Monitor Alert Action Group:**  Configure the Action Group to call the HTTP Trigger URL of the Azure Function.

**3.1 Post Auto-Remediation Verification**

*   **Check Web App Status:**  Verify that the Web App has been restarted successfully in the Azure Portal.
*   **Monitor CPU Usage:**  Monitor the CPU percentage of the Web App for the next 30 minutes to ensure it has returned to a normal level.
*   **Check Application Health:**  Confirm that the application is responding to requests and that users are no longer experiencing issues.
*   **Review Function Logs:** Review the Azure Function logs to ensure the restart was successful and to identify any errors that may have occurred during the process.
*   **Escalate if Necessary:**  If the CPU usage remains high or the issue persists, escalate to the development team for further investigation.

## 4. Logs

*   **Azure Activity Log:**  Review the Azure Activity Log for any events related to the Web App, such as restarts, deployments, or configuration changes.
*   **Web App Diagnostic Logs:** Analyze the Application Logs, Web Server Logs, and Detailed Error Messages as described in the Troubleshooting section.
*   **Kudu (SCM) Site Logs:**  Check the Kudu site's `LogFiles` directory for any logs generated by the application or the Web App environment.
*   **Azure Function Logs:**  Review the Azure Function logs to see if the restart was successful and if there were any errors.  Access logs through the Azure Portal's Function App section, or configure Application Insights for deeper analysis.
*   **Application Insights (If configured):** Review Application Insights for performance metrics, exceptions, and traces.

## 5. Escalation

If the auto-remediation fails or the issue persists after the Web App has been restarted, escalate to the development team and/or infrastructure team with the following information:

*   **Alert Details:**  Include the alert name, trigger time, and CPU percentage.
*   **Troubleshooting Steps:**  Describe the troubleshooting steps that have been taken and the findings.
*   **Logs:**  Provide relevant logs from the Web App, Kudu site, and Azure Function.
*   **Potential Causes:**  Share any potential causes that have been identified.

## 6. Prevention

*   **Code Optimization:** Regularly review and optimize application code to identify and address any performance bottlenecks.
*   **Performance Testing:** Conduct regular performance testing to identify and address performance issues before they impact users.
*   **Monitoring and Alerting:**  Fine-tune monitoring and alerting rules to ensure that issues are detected and addressed promptly. Consider lower threshold alerts for CPU and memory to proactively identify issues before they become critical.
*   **Auto-Scaling:**  Configure auto-scaling for the App Service Plan to automatically increase resources during periods of high demand.
*   **Regular Updates:**  Keep the application and its dependencies up to date with the latest security patches and performance improvements.
*   **Resource Allocation:** Ensure the App Service Plan and Web App are adequately provisioned for the expected workload.  Monitor resource usage and adjust as needed.
*   **Database Optimization:** Regularly review and optimize database queries to improve performance. Ensure proper indexing.
*   **Content Delivery Network (CDN):** Use a CDN to cache static content and reduce the load on the Web App.
*   **Connection Pooling:** Implement connection pooling to reduce the overhead of establishing new connections to external resources.

This runbook will be updated periodically based on lessons learned from past incidents.
```

## Architecture Diagram

![Diagram](diagram.png)
