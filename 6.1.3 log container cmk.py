import json
import subprocess
import requests
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)
RESOURCE = "https://management.azure.com"

def run_command(command):
    """Runs a shell command and returns the output."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Error executing command: {e}{Style.RESET_ALL}")
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

def get_storage_account_id(subscription_id):
    """Fetches the storage account IDs used in diagnostic settings for the given subscription."""
    command = f"az monitor diagnostic-settings subscription list --subscription {subscription_id} --query 'value[*].storageAccountId' --output json"
    result = run_command(command)
    
    if result:
        try:
            storage_account_ids = json.loads(result)
            return storage_account_ids if storage_account_ids else []
        except json.JSONDecodeError:
            return []
    return []

def check_storage_account_encryption(storage_account_name):
    """Checks if the storage account is encrypted with CMK (Customer-Managed Key)."""
    command = f"az storage account list --query \"[?name=='{storage_account_name}']\" --output json"
    result = run_command(command)

    
    print(f"{Fore.YELLOW}Raw Storage Account JSON Output for '{storage_account_name}':{Style.RESET_ALL}")
    print(result)

    if result:
        try:
            storage_accounts = json.loads(result)
            if storage_accounts:
                account = storage_accounts[0]
                key_source = account.get("encryption", {}).get("keySource", "")
                key_vault_properties = account.get("encryption", {}).get("keyVaultProperties", None)

                if key_source == "Microsoft.Keyvault" and key_vault_properties is not None:
                    return 'green', "Log container encrypted with CMK"
                else:
                    return 'red', account
            else:
                return 'red', f"Storage account {storage_account_name} not found"
        except json.JSONDecodeError:
            return 'red', "Error processing storage account data"
    return 'red', "Error retrieving storage account data"

def highlight_non_compliant(json_data):
    """Highlights non-compliant values in red."""
    json_str = json.dumps(json_data, indent=4)
    json_str = json_str.replace('"keySource": "Microsoft.Storage"', f'{Fore.RED}"keySource": "Microsoft.Storage"{Style.RESET_ALL}')
    json_str = json_str.replace('"keyVaultProperties": null', f'{Fore.RED}"keyVaultProperties": null{Style.RESET_ALL}')
    return json_str

def display_encryption_status():
    """Iterates through each subscription and checks if the log storage accounts are encrypted with CMK."""
    
    access_token = get_access_token()
    if not access_token:
        print(f"{Fore.RED}Cannot proceed without access token.{Style.RESET_ALL}")
        return

    
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    all_compliant = True
    storage_accounts_checked = 0

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.YELLOW}Checking storage account encryption for subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        
        storage_account_ids = get_storage_account_id(subscription_id)
        if not storage_account_ids:
            print(f"{Fore.YELLOW}No storage accounts found in diagnostic settings for subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        
        for storage_account_id in storage_account_ids:
            storage_account_name = storage_account_id.split('/')[-1]  
            color, status = check_storage_account_encryption(storage_account_name)
            storage_accounts_checked += 1
            print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
            print()

            if color == 'green':
                print(f"Storage Account: {storage_account_name} - {Fore.GREEN}{status}{Style.RESET_ALL}")
            else:
                all_compliant = False
                print(f"Storage Account: {storage_account_name} - {Fore.RED}Log container not encrypted with CMK{Style.RESET_ALL}")
                highlighted_output = highlight_non_compliant(status)
                print(f"{highlighted_output}")

    
    if storage_accounts_checked > 0:
        if all_compliant:
            print(f"\n{Fore.GREEN}Final Status: PASS - All storage accounts are encrypted with CMK.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}Final Status: FAIL - Some storage accounts are not encrypted with CMK.{Style.RESET_ALL}")

def main():
    display_encryption_status()

if __name__ == "__main__":
    main()
