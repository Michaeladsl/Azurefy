import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com"
API_VERSION_SUBSCRIPTIONS = "2020-01-01"
API_VERSION_SECURITY_SETTINGS = "2021-06-01"

def run_command(command):
    """Runs a shell command and returns the output or 'null' if the command fails."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = process.stdout.strip()
        return result if result else 'null'
    except subprocess.CalledProcessError:
        return 'null'

def check_authentication():
    """Check if already authenticated with Azure CLI to skip login."""
    try:
        subprocess.run(['az', 'account', 'show'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}Not authenticated. Please authenticate using the main script.{Style.RESET_ALL}")
        return False

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = f"az rest --method get --url {RESOURCE}/subscriptions?api-version={API_VERSION_SUBSCRIPTIONS}"
    response = run_command(command)
    
    if response:
        try:
            subscriptions = json.loads(response).get("value", [])
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for subscriptions: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve subscriptions.{Style.RESET_ALL}")
    return []

def get_defender_for_cloud_apps_integration(subscription_id):
    """Fetches the Defender for Cloud Apps integration status for a specific subscription."""
    url = f"{RESOURCE}/subscriptions/{subscription_id}/providers/Microsoft.Security/settings?api-version={API_VERSION_SECURITY_SETTINGS}"
    command = f"az rest --method get --url {url}"
    
    response = run_command(command)

    if response:
        try:
            data = json.loads(response)
            
            if isinstance(data, dict) and 'value' in data:
                for setting in data['value']:
                    if setting.get('name') == 'MCAS':
                        return setting['properties'].get('enabled', 'Unknown')
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for Defender for Cloud Apps settings: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve Defender for Cloud Apps settings for subscription {subscription_id}.{Style.RESET_ALL}")
    return 'Unknown'

def display_defender_for_cloud_apps_status():
    """Iterates through each subscription and displays Defender for Cloud Apps integration status with color formatting."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    for subscription in subscriptions:
        subscription_id = subscription['subscriptionId']
        subscription_name = subscription['displayName']
        
        mcas_status = get_defender_for_cloud_apps_integration(subscription_id)

        
        print(f"\n{Fore.YELLOW}Subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()
        if mcas_status is True:
            print(f"Defender for Cloud Apps Integration: {Fore.GREEN}true{Style.RESET_ALL}")
            print(f"{Fore.GREEN}\nFinal Status: Pass{Style.RESET_ALL}")
        elif mcas_status is False:
            print(f"Defender for Cloud Apps Integration: {Fore.RED}false{Style.RESET_ALL}")
            print(f"{Fore.RED}\nFinal Status: Fail{Style.RESET_ALL}")
        else:
            print(f"Defender for Cloud Apps Integration: {Fore.RED}{mcas_status}{Style.RESET_ALL}")
            print(f"{Fore.RED}\nFinal Status: Fail{Style.RESET_ALL}")

def main():
    """Entry point for Defender for Cloud Apps integration status check."""
    if not check_authentication():
        print(f"{Fore.RED}Please authenticate using the main script first.{Style.RESET_ALL}")
        return

    
    display_defender_for_cloud_apps_status()

if __name__ == "__main__":
    main()
