import colorama
import json
import requests
from colorama import Fore, Style
import subprocess

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com"
API_VERSION_DIAGNOSTICS = "2017-05-01-preview"  

def run_command(command):
    """Runs a shell command and returns the output."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_access_token():
    """Retrieve an access token using Azure CLI."""
    command = 'az account get-access-token --query accessToken -o tsv'
    access_token = run_command(command)
    if access_token:
        print()
    else:
        print(f"{Fore.RED}Failed to retrieve access token. Ensure you are logged in with 'az login'.{Style.RESET_ALL}")
    return access_token

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = "az account list --all --query '[].{id:id, subscriptionId:id, displayName:name}' -o json"
    result = run_command(command)
    
    if result:
        try:
            subscriptions = json.loads(result)
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output: {e}{Style.RESET_ALL}")
            return []
    return []

def check_diagnostic_settings_subscription(subscription_id, access_token):
    """Checks diagnostic settings for the given subscription and returns the full JSON output."""
    url = f"{RESOURCE}/subscriptions/{subscription_id}/providers/Microsoft.Insights/diagnosticSettings?api-version={API_VERSION_DIAGNOSTICS}"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            return response.json().get("value", [])
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing diagnostic settings JSON for subscription {subscription_id}.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve diagnostic settings for subscription {subscription_id}. Status code: {response.status_code}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Response content: {response.text}{Style.RESET_ALL}")
    return []

def check_appropriate_categories(settings):
    """Checks if the required diagnostic categories are enabled."""
    required_categories = ["Administrative", "Alert", "Policy", "Security"]
    
    logs = settings.get("logs", [])
    non_compliant = []

    for category in logs:
        if category["category"] in required_categories and not category["enabled"]:
            non_compliant.append(category["category"])

    if non_compliant:
        return False, non_compliant
    else:
        return True, None

def display_diagnostic_settings_status():
    """Iterates through each subscription to check if the required diagnostic categories are enabled."""
    
    access_token = get_access_token()
    if not access_token:
        print(f"{Fore.RED}Cannot proceed without access token.{Style.RESET_ALL}")
        return

    
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    all_compliant = True
    diagnostic_settings_found = False

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.YELLOW}Checking diagnostic settings for subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        
        diagnostic_settings = check_diagnostic_settings_subscription(subscription_id, access_token)
        
        
        print(json.dumps(diagnostic_settings, indent=4))  
        
        if not diagnostic_settings:
            print(f"{Fore.RED}No diagnostic settings found for subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        diagnostic_settings_found = True
        
        for setting in diagnostic_settings:
            if isinstance(setting, dict):
                print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
                print()
                compliant, non_compliant_categories = check_appropriate_categories(setting)
                if compliant:
                    print(f"Subscription: {subscription_name} - {Fore.GREEN}Diagnostic Setting captures appropriate categories{Style.RESET_ALL}")
                else:
                    all_compliant = False
                    print(f"Subscription: {subscription_name} - {Fore.RED}Diagnostic Setting does not capture all categories{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}Missing categories: {', '.join(non_compliant_categories)}{Style.RESET_ALL}")

    
    if diagnostic_settings_found:
        if all_compliant:
            print(f"\n{Fore.GREEN}Final Status: PASS - All diagnostic settings are compliant.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}Final Status: FAIL - Some diagnostic settings are non-compliant.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}No diagnostic settings found. Final Status not applicable.{Style.RESET_ALL}")

def main():
    display_diagnostic_settings_status()

if __name__ == "__main__":
    main()
