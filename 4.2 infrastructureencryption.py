import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com/"
API_VERSION_SUBSCRIPTIONS = "2020-01-01"
API_VERSION_STORAGE = "2021-09-01"

def run_command(command):
    """Runs a shell command and returns the output or 'None' if the command fails."""
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
    url = f"{RESOURCE}subscriptions/{subscription_id}/providers/Microsoft.Storage/storageAccounts?api-version={API_VERSION_STORAGE}"
    command = f"az rest --method get --url {url}"
    
    response = run_command(command)

    if response:
        try:
            return json.loads(response).get("value", [])
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for storage accounts: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve storage accounts for subscription {subscription_id}.{Style.RESET_ALL}")
    return []

def check_infrastructure_encryption(subscription_id, account_name, resource_group):
    """Checks if infrastructure encryption is enabled for a specific storage account."""
    url = f"{RESOURCE}subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{account_name}?api-version={API_VERSION_STORAGE}"
    command = f"az rest --method get --url {url}"
    
    response = run_command(command)
    
    if response:
        try:
            account_data = json.loads(response)
            return account_data.get("properties", {}).get("encryption", {}).get("requireInfrastructureEncryption", False)
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for infrastructure encryption: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve encryption status for {account_name}.{Style.RESET_ALL}")
    return None

def display_infrastructure_encryption_status():
    """Iterates through each subscription and checks infrastructure encryption status for each storage account."""
    if not check_authentication():
        print(f"{Fore.RED}Please authenticate using the main script first.{Style.RESET_ALL}")
        return

    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found.{Style.RESET_ALL}")
        return

    all_passed = True  

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.YELLOW}Checking storage accounts in subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        storage_accounts = get_storage_accounts(subscription_id)
        if not storage_accounts:
            print(f"{Fore.YELLOW}No storage accounts found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        for account in storage_accounts:
            account_name = account["name"]
            resource_group = account["id"].split("/")[4]  
            encryption_status = check_infrastructure_encryption(subscription_id, account_name, resource_group)
            
            if encryption_status is None:
                print(f"{Fore.RED}Could not determine encryption status for storage account {account_name}.{Style.RESET_ALL}")
                all_passed = False  
            else:
                color = Fore.GREEN if encryption_status else Fore.RED
                status_text = "Enabled" if encryption_status else "Not Enabled"
                print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
                print()
                print(f"Storage Account: {account_name} - Infrastructure Encryption: {color}{status_text}{Style.RESET_ALL}")
                if not encryption_status:
                    all_passed = False  

    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if all_passed else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")

def main():
    """Main function to display infrastructure encryption status for all storage accounts."""
    display_infrastructure_encryption_status()

if __name__ == "__main__":
    main()
