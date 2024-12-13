import json
import subprocess
import colorama
from colorama import Fore, Style
from datetime import datetime, timedelta

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com/"
API_VERSION_SUBSCRIPTIONS = "2020-01-01"
API_VERSION_STORAGE = "2021-08-01"

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
    """Retrieve storage accounts in a specific subscription."""
    url = f"{RESOURCE}subscriptions/{subscription_id}/providers/Microsoft.Storage/storageAccounts?api-version={API_VERSION_STORAGE}"
    command = f"az rest --method get --url {url}"
    response = run_command(command)
    
    if response:
        try:
            return json.loads(response).get("value", [])
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON for storage accounts in subscription {subscription_id}: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve storage accounts for subscription {subscription_id}.{Style.RESET_ALL}")
    return []

def check_key_regeneration(resource_id):
    """Check if the storage account key has been regenerated within the last 90 days."""
    command = f"az monitor activity-log list --namespace Microsoft.Storage --offset 90d --resource-id {resource_id} -o json"
    response = run_command(command)

    if response:
        try:
            events = json.loads(response)
            
            relevant_events = [
                event for event in events
                if 'authorization' in event and 'action' in event['authorization'] and
                   'regenerateKey' in event['authorization']['action'] and
                   event.get('status', {}).get('localizedValue') == 'Succeeded'
            ]
            return bool(relevant_events), None  
        except json.JSONDecodeError:
            print(f"{Fore.RED}Failed to parse the activity log response for resource ID: {resource_id}.{Style.RESET_ALL}")
            return False, {"authorization": "null"}
    else:
        
        return False, {"authorization": "null"}

def check_key_regeneration_for_all_accounts():
    """Check key regeneration status for storage accounts across all subscriptions."""
    if not check_authentication():
        print(f"{Fore.RED}Please authenticate using the main script first.{Style.RESET_ALL}")
        return

    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found.{Style.RESET_ALL}")
        return

    all_keys_regenerated = True  

    for subscription in subscriptions:
        subscription_id = subscription['subscriptionId']
        subscription_name = subscription['displayName']
        print(f"\n{Fore.YELLOW}Checking storage accounts in subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()
        
        storage_accounts = get_storage_accounts(subscription_id)
        if not storage_accounts:
            print(f"{Fore.YELLOW}No storage accounts found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue
        
        for account in storage_accounts:
            account_name = account["name"]
            resource_id = account["id"]
            is_regenerated, minimal_json = check_key_regeneration(resource_id)

            if is_regenerated:
                print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
                print()
                print(f"Storage Account: {account_name} - {Fore.GREEN}Key regenerated in the last 90 days{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
                print()
                print(f"Storage Account: {account_name} - {Fore.RED}Key not regenerated in the last 90 days{Style.RESET_ALL}")
                all_keys_regenerated = False

                
                print(f"{Fore.CYAN}Authorization:{Style.RESET_ALL}")
                print(json.dumps(minimal_json, indent=4))  

    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if all_keys_regenerated else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")

def main():
    """Main function to check key regeneration compliance for storage accounts."""
    check_key_regeneration_for_all_accounts()

if __name__ == "__main__":
    main()