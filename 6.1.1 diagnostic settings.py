import colorama
import subprocess
import json
import requests
from colorama import Fore, Style


colorama.init(autoreset=True)

resource = "https://management.azure.com/"

def run_command(command):
    """Runs a shell command and returns the output."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_access_token():
    """Retrieve an access token using the Azure CLI."""
    command = 'az account get-access-token --query accessToken -o tsv'
    access_token = run_command(command)
    if not access_token:
        print(f"{Fore.RED}Failed to retrieve access token. Ensure you are logged in with 'az login'.{Style.RESET_ALL}")
    return access_token

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = "az account list --all --query '[].{id:id, subscriptionId:id, displayName:name}' -o json"
    result = run_command(command)
    
    if result:
        try:
            subscriptions = json.loads(result)
            print(f"{Fore.GREEN}Retrieved {len(subscriptions)} subscriptions.{Style.RESET_ALL}")
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output: {e}{Style.RESET_ALL}")
            return []
    return []

def check_diagnostic_settings_subscription(subscription_id, access_token):
    """Checks diagnostic settings for the given subscription."""
    url = f"{resource}subscriptions/{subscription_id}/providers/Microsoft.Insights/diagnosticSettings?api-version=2017-05-01-preview"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        settings = response.json()
        if settings.get("value", []):
            return 'green', "Diagnostic settings enabled", settings
        return 'red', "Diagnostic settings not enabled", settings
    else:
        return 'red', f"Failed to retrieve diagnostic settings ({response.status_code})", response.json()

def get_resources_in_subscription(subscription_id):
    """Fetches the list of all resources in a subscription."""
    command = f'az resource list --subscription {subscription_id} --query "[].id" --output json'
    result = run_command(command)
    
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return []
    return []

def check_diagnostic_settings_resource(resource_id, access_token):
    """Checks diagnostic settings for the given resource."""
    url = f"{resource}{resource_id}/providers/Microsoft.Insights/diagnosticSettings?api-version=2017-05-01-preview"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        settings = response.json()
        if settings.get("value", []):
            return 'green', "Diagnostic settings enabled", settings
        return 'red', "Diagnostic settings not enabled", settings
    else:
        return 'red', f"Failed to retrieve diagnostic settings ({response.status_code})", response.json()

def display_diagnostic_settings_status():
    """Iterates through each subscription and resource to check the diagnostic settings."""
    
    access_token = get_access_token()
    if not access_token:
        print(f"{Fore.RED}Cannot proceed without access token.{Style.RESET_ALL}")
        return

    
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    all_compliant = True
    resources_checked = False

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.YELLOW}Checking diagnostic settings for subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        
        color, status, full_output = check_diagnostic_settings_subscription(subscription_id, access_token)
        if color == 'red':
            all_compliant = False
        print(f"Subscription: {subscription_name} - {Fore.GREEN if color == 'green' else Fore.RED}{status}{Style.RESET_ALL}")
        print(f"Full Output:\n{json.dumps(full_output, indent=4)}\n")

        
        resources = get_resources_in_subscription(subscription_id)
        if not resources:
            print(f"{Fore.YELLOW}No resources found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        
        for resource_id in resources:
            resources_checked = True
            color, status, full_output = check_diagnostic_settings_resource(resource_id, access_token)
            resource_name = resource_id.split('/')[-1]
            if color == 'red':
                all_compliant = False
            print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
            print()
            print(f"Resource: {resource_name} - {Fore.GREEN if color == 'green' else Fore.RED}{status}{Style.RESET_ALL}")
            print(f"Full Output:\n{json.dumps(full_output, indent=4)}\n")

    
    if resources_checked:
        if all_compliant:
            print(f"\n{Fore.GREEN}Final Status: PASS{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}Final Status: FAIL{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}No resources checked. Final Status not applicable.{Style.RESET_ALL}")

def main():
    display_diagnostic_settings_status()

if __name__ == "__main__":
    main()
