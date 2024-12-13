import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com"
API_VERSION_SUBSCRIPTIONS = "2020-01-01"
API_VERSION_STORAGE = "2021-08-01"

def run_command(command):
    """Runs a shell command and returns the output or 'null' if the command fails."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Error executing command: {e}{Style.RESET_ALL}")
        return None

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

def get_storage_accounts(subscription_id):
    """Fetches the list of storage accounts for a specific subscription."""
    url = f"{RESOURCE}/subscriptions/{subscription_id}/providers/Microsoft.Storage/storageAccounts?api-version={API_VERSION_STORAGE}"
    command = f"az rest --method get --url {url}"
    
    response = run_command(command)

    if response:
        try:
            storage_accounts = json.loads(response).get("value", [])
            return storage_accounts
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for storage accounts: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve storage accounts for subscription {subscription_id}.{Style.RESET_ALL}")
    return []

def display_secure_transfer_status():
    """Iterates through each subscription and displays storage accounts' secure transfer status with color formatting."""
    if not check_authentication():
        print(f"{Fore.RED}Authentication required. Please authenticate using the main script first.{Style.RESET_ALL}")
        print("Final Status: FAIL")  
        return

    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found.{Style.RESET_ALL}")
        print("Final Status: FAIL")  
        return

    all_passed = True  

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]

        print(f"\n{Fore.YELLOW}Checking storage accounts in subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}\n")

        storage_accounts = get_storage_accounts(subscription_id)

        if not storage_accounts:
            print(f"{Fore.YELLOW}No storage accounts found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        for account in storage_accounts:
            account_name = account["name"]
            https_enabled = account.get("properties", {}).get("supportsHttpsTrafficOnly", False)

            
            color = Fore.GREEN if https_enabled else Fore.RED
            status_text = "Enabled (Secure Transfer Required)" if https_enabled else "Secure Transfer Not Required"
            print(f"Storage Account: {account_name} - {color}{status_text}{Style.RESET_ALL}")

            
            if not https_enabled:
                all_passed = False

    
    if all_passed:
        print(f"\n{Fore.GREEN}All storage accounts are compliant.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}Some storage accounts are non-compliant.{Style.RESET_ALL}")

    
    print("Final Status: PASS" if all_passed else "Final Status: FAIL")



def main():
    """Main function to display secure transfer status for all storage accounts."""
    display_secure_transfer_status()

if __name__ == "__main__":
    main()
