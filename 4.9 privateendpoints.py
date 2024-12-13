import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com/"
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
    command = f"az rest --method get --url {RESOURCE}subscriptions?api-version={API_VERSION_SUBSCRIPTIONS}"
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

def check_private_endpoint_connections(account_name, resource_group, subscription_id):
    """Checks if a storage account has private endpoint connections."""
    url = f"{RESOURCE}subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Storage/storageAccounts/{account_name}?api-version={API_VERSION_STORAGE}"
    command = f"az rest --method get --url {url}"
    response = run_command(command)
    
    if response:
        try:
            storage_data = json.loads(response)
            private_endpoint_connections = storage_data.get("properties", {}).get("privateEndpointConnections", [])
            if private_endpoint_connections:
                return True, Fore.GREEN, "Private endpoints enabled", None
            else:
                return False, Fore.RED, "Private endpoints not used", storage_data.get("properties", {}).get("privateEndpointConnections")
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for private endpoint connections: {e}{Style.RESET_ALL}")
            return False, Fore.RED, "Unknown status", None
    else:
        print(f"{Fore.RED}Failed to check private endpoint connections for {account_name}.{Style.RESET_ALL}")
        return False, Fore.RED, "Unknown status", None

def display_private_endpoint_status():
    """Iterates through each subscription and storage account to check for private endpoint connections."""
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
        print(f"\n{Fore.YELLOW}Checking private endpoints in subscription...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        storage_accounts = get_storage_accounts(subscription_id)
        if not storage_accounts:
            print(f"{Fore.RED}No storage accounts found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        for account in storage_accounts:
            account_name = account["name"]
            try:
                resource_group = account["id"].split("/")[4]  
                
                compliant, color, status, proof = check_private_endpoint_connections(account_name, resource_group, subscription_id)
                print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
                print()
                print(f"Storage Account: {account_name} - Private Endpoint Connections: {color}{status}{Style.RESET_ALL}")

                
                if not compliant:
                    all_compliant = False
                    print(f"{Fore.CYAN}Sample JSON {account_name}:{Style.RESET_ALL}")
                    print(json.dumps(proof, indent=4))
            except IndexError:
                print(f"{Fore.RED}Error extracting resource group for account {account_name}. Invalid account ID format.{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if all_compliant else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")


def main():
    """Entry point for private endpoint connections check."""
    display_private_endpoint_status()

if __name__ == "__main__":
    main()
