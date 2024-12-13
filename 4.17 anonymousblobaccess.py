import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = "az account list --query '[].{id:id, name:name}' -o json"
    result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE)
    subscriptions = json.loads(result.stdout)
    return subscriptions

def get_storage_accounts(subscription_id):
    """Fetches the list of storage accounts for a specific subscription."""
    command = f"az storage account list --subscription {subscription_id} --query '[].{{name:name, resourceGroup:resourceGroup}}' -o json"
    result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE)
    storage_accounts = json.loads(result.stdout)
    return storage_accounts

def check_blob_public_access(storage_account, resource_group, subscription_id):
    """Runs the az storage account show command to check the allowBlobPublicAccess setting."""
    command = f"az storage account show --name {storage_account} --resource-group {resource_group} --subscription {subscription_id} --query allowBlobPublicAccess -o json"
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"{Fore.RED}Failed to retrieve allowBlobPublicAccess setting for {storage_account}.{Style.RESET_ALL}")
        print(f"{Fore.RED}Error: {result.stderr.strip()}{Style.RESET_ALL}")
        return None
    
    try:
        allow_blob_public_access = json.loads(result.stdout)
        color = Fore.GREEN if allow_blob_public_access is False else Fore.RED
        status = "false" if allow_blob_public_access is False else "true"
        print(f"Storage Account: {storage_account} - Allow Blob Public Access: {color}{status}{Style.RESET_ALL}")
        return allow_blob_public_access
    except json.JSONDecodeError:
        print(f"{Fore.RED}Failed to parse the allowBlobPublicAccess setting for {storage_account}.{Style.RESET_ALL}")
        return None

def display_final_status(all_passed):
    """Displays the final status based on the compliance of all storage accounts."""
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if all_passed else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")

def main():
    """Main script function."""
    subscriptions = get_subscriptions()
    all_passed = True  

    for subscription in subscriptions:
        subscription_id = subscription["id"]
        subscription_name = subscription["name"]
        print(f"\n{Fore.YELLOW}Checking storage accounts in subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        storage_accounts = get_storage_accounts(subscription_id)
        if not storage_accounts:
            print(f"{Fore.RED}No storage accounts found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        for account in storage_accounts:
            storage_account_name = account["name"]
            resource_group = account["resourceGroup"]

            result = check_blob_public_access(storage_account_name, resource_group, subscription_id)
            if result is not False:  
                all_passed = False

    
    display_final_status(all_passed)

if __name__ == "__main__":
    main()
