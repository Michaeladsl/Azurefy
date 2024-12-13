import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com"
API_VERSION_SUBSCRIPTIONS = "2020-01-01"
API_VERSION_ACTIVITY_LOG_ALERTS = "2017-04-01"

def run_command(command):
    """Runs a shell command and returns the output or None if the command fails."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Error executing command: {e.stderr}{Style.RESET_ALL}")
        return None

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = f"az rest --method get --url {RESOURCE}/subscriptions?api-version={API_VERSION_SUBSCRIPTIONS}"
    response = run_command(command)

    if response:
        try:
            subscriptions = json.loads(response).get("value", [])
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing subscription JSON: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve subscriptions.{Style.RESET_ALL}")
    return []

def get_activity_log_alerts(subscription_id):
    """Fetches activity log alerts for a specific subscription."""
    print(f"{Fore.YELLOW}Fetching activity log alerts for subscription ID: {subscription_id}...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()
    url = f"{RESOURCE}/subscriptions/{subscription_id}/providers/Microsoft.Insights/activityLogAlerts?api-version={API_VERSION_ACTIVITY_LOG_ALERTS}"
    command = f"az rest --method get --url {url}"
    response = run_command(command)

    if response:
        try:
            return json.loads(response).get("value", [])
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing activity log alert JSON: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve activity log alerts for subscription {subscription_id}.{Style.RESET_ALL}")
    return []

def check_activity_log_alert(alerts, action_type):
    """Checks if a specific action type exists in the activity log alerts."""
    return any(
        any(condition.get("field") == action_type for condition in alert.get("properties", {}).get("condition", {}).get("allOf", []))
        for alert in alerts
    )

def check_activity_log_alerts(subscription_id, action_types):
    """Checks multiple action types for compliance in activity log alerts."""
    alerts = get_activity_log_alerts(subscription_id)
    if not alerts:
        print(f"{Fore.RED}No activity log alerts found for subscription {subscription_id}.{Style.RESET_ALL}")
        return False

    all_compliant = True
    for action_type, message in action_types.items():
        if not check_activity_log_alert(alerts, action_type):
            print(f"{Fore.RED}{message}: {action_type}{Style.RESET_ALL}")
            all_compliant = False
    return all_compliant

def display_activity_log_alert_status():
    print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
    print()
    """Iterates through each subscription and checks activity log alerts for compliance."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found.{Style.RESET_ALL}")
        return

    overall_compliance = True

    action_types = {
        "Microsoft.Authorization/policyAssignments/write": "Missing alert for creating policy assignment",
        "Microsoft.Authorization/policyAssignments/delete": "Missing alert for deleting policy assignment",
        "Microsoft.Network/networkSecurityGroups/write": "Missing alert for creating/updating network security group",
        "Microsoft.Network/networkSecurityGroups/delete": "Missing alert for deleting network security group",
        "Microsoft.Security/securitySolutions/write": "Missing alert for creating/updating security solution",
        "Microsoft.Security/securitySolutions/delete": "Missing alert for deleting security solution",
        "Microsoft.Sql/servers/firewallRules/write": "Missing alert for creating/updating SQL server firewall rule",
        "Microsoft.Sql/servers/firewallRules/delete": "Missing alert for deleting SQL server firewall rule",
        "Microsoft.Network/publicIPAddresses/write": "Missing alert for creating/updating public IP address",
        "Microsoft.Network/publicIPAddresses/delete": "Missing alert for deleting public IP address"
    }

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        compliant = check_activity_log_alerts(subscription_id, action_types)
        if not compliant:
            overall_compliance = False

    
    print("\n" + "-" * 50)
    if overall_compliance:
        print(f"{Fore.GREEN}Final Status: PASS{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Final Status: FAIL{Style.RESET_ALL}")

def main():
    """Entry point for Activity Log Alerts compliance check."""
    display_activity_log_alert_status()

if __name__ == "__main__":
    main()
