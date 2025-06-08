```markdown
# Azure Web App High CPU Usage Alert Runbook (Auto-Recovered)

**Alert Name:** WebAppHighCPU
**Trigger Condition:** Average CPU usage greater than 10% for 5 minutes
**Impact:** Potential performance degradation, slow response times, application unavailability.
**Auto-Recovery Action:** Restart Web App

## 1. Symptoms

*   **Users report slow response times:** Customers may complain about web pages loading slowly or transactions taking longer to complete.
*   **Application errors:** You may see increased error rates in your application logs. Common errors include timeouts, failed requests, or server overload errors.
*   **Monitoring dashboard displays high CPU usage:** The Azure Monitor dashboard shows consistent CPU utilization exceeding the threshold (10%).
*   **Application unresponsive:**  The Web App might become completely unresponsive, requiring a restart.
*   **Increased latency:**  End-to-end latency monitoring shows a significant increase.
*   **Auto-recovery triggered notification:** You receive a notification (e.g., email, SMS, Teams message) that the Azure Function responsible for restarting the Web App has been triggered.

## 2. Troubleshooting

### 2.1 Initial Assessment

*   **Confirm the Alert:** Verify that the alert is still active in the Azure portal. Navigate to Azure Monitor > Alerts and filter for active alerts with the name "WebAppHighCPU."
*   **Check Web App Status:** Verify that the Web App is running and healthy.  Go to the Azure portal > App Services > [YourWebAppName] > Overview. Check the "Status" and "Health check" status.
*   **Review Recent Activity:** Check the Activity Log for any recent deployments, configuration changes, or scaling operations that might have contributed to the high CPU usage.
    *   Go to Azure portal > App Services > [YourWebAppName] > Activity log. Filter for relevant operations.

### 2.2 Deeper Investigation (If CPU remains high after auto-recovery)

*   **Diagnose and Solve Problems:**
    *   Use the "Diagnose and solve problems" blade in the Azure portal for the Web App.
        *   Go to Azure portal > App Services > [YourWebAppName] > Diagnose and solve problems.
        *   Run the "Availability and Performance" detector.
        *   Review the "High CPU" detector if it is available.
*   **Collect Memory Dumps:**
    *   If the application is still running, collect a memory dump to analyze the application's state.  This will require access to the Kudu console.
        *   Go to Azure portal > App Services > [YourWebAppName] > Development Tools > Kudu.
        *   Navigate to `Debug Console` > `CMD`.
        *   Use the `procdump` utility (already available) to capture a memory dump.
        *   Example: `procdump -ma w3wp.exe  C:\Dumps\w3wp.dmp` (This captures a full memory dump of the `w3wp.exe` process).
        *   Download the dump file and analyze it using tools like WinDbg.
*   **Investigate Application Logs:**  Examine application logs for errors, warnings, or unexpected behavior.
    *   **Streaming Logs:** Use the Azure portal or the Azure CLI to stream the Web App's logs in real-time.
        *   Azure portal > App Services > [YourWebAppName] > App Service logs >  Enable "Application Logging (Filesystem)" and "Web server logging".
        *   Azure CLI:  `az webapp log tail --name [YourWebAppName] --resource-group [YourResourceGroupName]`
    *   **Log Analytics Workspace:**  If configured, query the Log Analytics workspace for relevant events related to the Web App.  Use Kusto Query Language (KQL) to search for errors, exceptions, and performance issues.
        *   Example KQL query:
          ```kql
          AppServiceAppLogs
          | where AppName == "[YourWebAppName]"
          | where TimeGenerated > ago(1h)
          | where Level == "Error"
          | project TimeGenerated, Message, Source
          ```
*   **Profiling:** Use the Azure Profiler to identify CPU-intensive methods in your application.
    *   Go to Azure portal > App Services > [YourWebAppName] > Performance blade > Profiler.
    *   Start a profiling session.  The profiler captures stack traces and CPU usage data over a period of time.
    *   Analyze the profiling data to identify the methods that are consuming the most CPU.

### 2.3 Resource Contention

*   **Check Database:**  If the Web App relies on a database, check the database CPU, memory, and I/O utilization. High database load can often contribute to high Web App CPU usage.
*   **External Dependencies:** Investigate any external services or APIs that the Web App depends on.  Slow or overloaded external dependencies can cause the Web App to consume more CPU.
*   **Network Issues:** Check for network connectivity issues that might be causing the Web App to retry requests, leading to increased CPU usage.

## 3. Auto-Remediation

*   **Azure Function Triggered:**  An Azure Function is triggered when the CPU usage alert is fired.  This function is responsible for restarting the Web App.
*   **Function Code (Example - PowerShell):**

    ```powershell
    param($Timer)

    # Get the Web App name from environment variable (recommended for security)
    $WebAppName = $env:WebAppName
    $ResourceGroupName = $env:ResourceGroupName

    # Ensure variables are set
    if (-not $WebAppName) {
        Write-Error "WebAppName environment variable not set."
        exit
    }

    if (-not $ResourceGroupName) {
        Write-Error "ResourceGroupName environment variable not set."
        exit
    }

    try {
        # Stop the Web App
        Write-Host "Stopping Web App: $WebAppName in Resource Group: $ResourceGroupName"
        Stop-AzWebApp -Name $WebAppName -ResourceGroupName $ResourceGroupName -Force

        # Wait a few seconds to allow the app to fully stop
        Start-Sleep -Seconds 15

        # Start the Web App
        Write-Host "Starting Web App: $WebAppName in Resource Group: $ResourceGroupName"
        Start-AzWebApp -Name $WebAppName -ResourceGroupName $ResourceGroupName -Force

        Write-Host "Web App restarted successfully."
    }
    catch {
        Write-Error "Failed to restart Web App: $($_.Exception.Message)"
    }

    Write-Host "Auto-remediation function completed."

    ```

    **Important:**

    *   Replace `[YourWebAppName]` and `[YourResourceGroupName]` with the actual values.  **Ideally store these in the Function App's Application Settings as `WebAppName` and `ResourceGroupName` and access them through `$env:WebAppName` and `$env:ResourceGroupName`.  This is more secure than hardcoding the values.**
    *   Ensure the Function App has the necessary permissions to manage the Web App.  Assign the `Contributor` role or a custom role with appropriate permissions (e.g., `Microsoft.Web/sites/stop/action`, `Microsoft.Web/sites/start/action`) to the Function App's Managed Identity on the Web App's Resource Group.
    *   **Use Managed Identity for authentication.**  Do not store credentials in the Function App code.
    *   Install the `Az.Websites` module in the Function App.  You can do this by adding it to the `requirements.psd1` file (for PowerShell functions).

*   **Verify Restart:** After the Azure Function runs, verify that the Web App has been successfully restarted in the Azure portal.
*   **Monitor CPU Usage:**  After the restart, closely monitor CPU usage to ensure that it has returned to normal levels.

## 4. Logs

### 4.1. Azure Function Logs

*   **Access Function Logs:** View the Azure Function's logs to verify that the restart operation was successful.
    *   Go to Azure portal > Function App > [YourFunctionName] > Monitor.
    *   Check the "Invocation count" and "Function executions" to see if the function was triggered.
    *   Examine the logs for any errors or warnings.

### 4.2. Azure Monitor Logs

*   **Alert History:** Review the alert history in Azure Monitor to see when the alert was triggered and resolved.
    *   Go to Azure Monitor > Alerts > History.  Filter for the "WebAppHighCPU" alert.
*   **Metrics:**  Examine CPU usage metrics in Azure Monitor to see the trend over time.
    *   Go to Azure Monitor > Metrics.  Select the "App Service" resource and the "CpuPercentage" metric.
*   **Activity Log:** The Activity Log records the Azure Function's actions (stopping and starting the Web App).
    *   Go to Azure Monitor > Activity log.  Filter for operations performed by the Function App's Managed Identity.

### 4.3 Web App Logs (If further investigation is needed after auto-recovery)

*   Refer to section 2.2 for details on Web App logs (streaming logs, Log Analytics workspace).

## 5. Root Cause Analysis (If auto-recovery is frequently triggered)

If the CPU usage alert is triggered frequently, it's important to perform a root cause analysis to identify the underlying issue. Consider the following:

*   **Code Optimization:** Analyze your application code for performance bottlenecks and areas for optimization.  Use profiling tools to identify CPU-intensive methods.
*   **Scaling:**  Consider scaling up your App Service plan to provide more CPU resources.
*   **Inefficient Queries:**  Optimize database queries to reduce the load on the database server.
*   **Caching:**  Implement caching strategies to reduce the number of database calls and external API requests.
*   **Background Tasks:**  Offload long-running tasks to background processes or queues to prevent them from blocking the main thread.
*   **Resource Leaks:**  Identify and fix any memory leaks or resource leaks in your application.
*   **Deployment Frequency:**  Analyze whether recent deployments are contributing to performance degradation.  Consider implementing more rigorous testing and staging environments before deploying to production.
*   **DDoS Mitigation:** If the Web App is under a DDoS attack, implement DDoS mitigation measures.

## 6. Escalation

If the auto-remediation fails to resolve the issue, or if the problem persists after a restart, escalate to the appropriate support team according to your organization's escalation procedures.  Provide the following information:

*   Alert name ("WebAppHighCPU")
*   Web App name
*   Resource Group name
*   Symptoms
*   Troubleshooting steps taken
*   Azure Function logs
*   Web App logs (if available)
*   Memory dumps (if available)
*   Root cause analysis findings (if available)

## 7. Prevention

*   **Proactive Monitoring:** Implement comprehensive monitoring and alerting to detect performance issues early.
*   **Capacity Planning:** Regularly review resource utilization and adjust App Service plan size as needed.
*   **Performance Testing:** Conduct performance testing during development and before deploying new releases to identify potential performance bottlenecks.
*   **Code Reviews:**  Conduct thorough code reviews to identify and prevent performance-related issues.
*   **Regular Maintenance:** Perform regular maintenance tasks such as database optimization, log cleanup, and security patching.
*   **Auto-Scaling:** Configure auto-scaling rules for your App Service plan to automatically scale up or down based on CPU usage.  This can help prevent high CPU usage events in the first place.

This runbook provides a detailed guide for responding to high CPU usage alerts for Azure Web Apps with an automated restart remediation strategy. Remember to customize this runbook with specific details about your application, infrastructure, and organizational procedures.  Regularly review and update the runbook to ensure that it remains effective.

## Architecture Diagram (Mermaid)
```mermaid
```mermaid
graph LR
    subgraph Azure Subscription
        subgraph Resource Group
            A[App Service (Web App)] -- "CPU Usage > 10%" --> B(Azure Monitor Alert);
            B -- Triggers --> C(Action Group);
            C -- Executes --> D(Function App (Restart Web App));
            D -- Restarts --> A;

            style A fill:#f9f,stroke:#333,stroke-width:2px
            style B fill:#ccf,stroke:#333,stroke-width:2px
            style C fill:#ccf,stroke:#333,stroke-width:2px
            style D fill:#fcf,stroke:#333,stroke-width:2px

            subgraph "Optional: Logic App (Complex Actions)"
                E(Logic App)
                C -- Optionally Executes --> E
                E -- Can take other actions --> F[Other Azure Resources]
            end
            style E fill:#cff,stroke:#333,stroke-width:2px
        end
    end

    linkStyle 0 stroke:#f66,stroke-width:2px,color:red;
    linkStyle 3 stroke:#6f6,stroke-width:2px,color:green;
```

**Explanation:**

* **Azure Subscription:**  The top-level container.
* **Resource Group:**  A logical container for Azure resources.
* **App Service (Web App):** The web application being monitored.  It's visually styled to indicate it's the target.
* **Azure Monitor Alert:** Monitors the CPU usage of the App Service. When CPU usage exceeds 10%, it triggers the Action Group.
* **Action Group:**  Defines the actions to be taken when the alert is triggered.  In this case, it executes the Azure Function.
* **Function App (Restart Web App):** An Azure Function that contains the code to restart the App Service.  It receives the alert notification and triggers the restart.
* **Optional: Logic App (Complex Actions):** An optional Logic App that can be triggered by the Action Group instead of or in addition to the Function App. This allows for more complex workflows, such as sending notifications, logging information, or taking other actions before or after restarting the Web App.  It illustrates that other Azure resources can be incorporated into this process via the Logic App.
* **Arrows and Labels:**  Arrows indicate the flow of events, and labels clarify the relationship between components.
* **Styling:** Styles highlight important resources (App Service, Function App) and connections (triggering, restart). The red link highlights the condition that triggers the alert. The green link shows the action that restores the web app.
* **Optional Component:** The Logic App section is marked as optional to indicate that it's not a required part of the core monitoring and restart process, but it can be added for enhanced functionality.
* **Link Styles:**  `linkStyle` attributes are used to visually distinguish the trigger (red, indicating a high CPU condition) and the restart action (green, indicating remediation).

This diagram provides a clear visual representation of the monitoring and restart process, making it easier to understand the relationships between the Azure resources involved.  The use of colors and labels further enhances clarity. Remember to replace the placeholders with your actual resource names and configure the alerts, action groups, and function app code appropriately in your Azure environment.
```
