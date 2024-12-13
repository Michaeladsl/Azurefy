import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com"
API_VERSION_SUBSCRIPTIONS = "2020-01-01"
API_VERSION_STORAGE = "2021-09-01"

def run_command(command):
    """Runs a shell command and returns the output or None if the command fails."""
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
            return [{"name": account["name"], "id": account["id"]} for account in storage_accounts]
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for storage accounts: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve storage accounts for subscription {subscription_id}.{Style.RESET_ALL}")
    return []

def check_public_storage_access(account_name, resource_group, subscription_id):
    """Checks the public network access setting for a specific storage account."""
    url = f"{RESOURCE}/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{account_name}?api-version={API_VERSION_STORAGE}"
    command = f"az rest --method get --url {url}"
    
    response = run_command(command)
    
    if response:
        try:
            account_data = json.loads(response)
            public_network_access = account_data.get("properties", {}).get("publicNetworkAccess", "Unknown")
            return public_network_access, account_data
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for public network access: {e}{Style.RESET_ALL}")
            return "Unknown", None
    else:
        print(f"{Fore.RED}Failed to check public network access for {account_name}.{Style.RESET_ALL}")
        return "Unknown", None

def display_public_storage_access_status():
    """Iterates through each subscription and checks public network access status for each storage account."""
    if not check_authentication():
        print(f"{Fore.RED}Please authenticate using the main script first.{Style.RESET_ALL}")
        return

    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found.{Style.RESET_ALL}")
        return

    all_compliant = True  

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
            try:
                resource_group = account["id"].split("/")[4]  
                public_network_access, account_data = check_public_storage_access(account_name, resource_group, subscription_id)
                
                
                if public_network_access == "Enabled":
                    print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
                    print()
                    print(f"Storage Account: {account_name} - Public Network Access: {Fore.RED}Enabled{Style.RESET_ALL}")
                    all_compliant = False

                    
                    if account_data:
                        print(f"{Fore.CYAN}\n{Style.RESET_ALL}")
                        proof_snippet = {
                            "id": account_data.get("id", ""),
                            "publicNetworkAccess": public_network_access
                        }
                        print(json.dumps(proof_snippet, indent=4))
                elif public_network_access == "Disabled":
                    print(f"Storage Account: {account_name} - Public Network Access: {Fore.GREEN}Disabled{Style.RESET_ALL}")
                else:
                    print(f"Storage Account: {account_name} - Public Network Access: {Fore.RED}Unknown{Style.RESET_ALL}")
                    all_compliant = False
            except IndexError:
                print(f"{Fore.RED}Error extracting resource group for account {account_name}. Invalid account ID format.{Style.RESET_ALL}")

    
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if all_compliant else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")


def main():
    """Entry point for public network access check."""
    display_public_storage_access_status()

if __name__ == "__main__":
    main()
