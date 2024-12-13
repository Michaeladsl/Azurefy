import subprocess
import json
import colorama
from colorama import Fore, Style
import argparse

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com"
API_VERSION_SUBSCRIPTIONS = "2020-01-01"
API_VERSION_STORAGE = "2021-08-01"

def run_command(command):
    """Runs a shell command and returns the output or 'null' if the command fails."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = process.stdout.strip()
        return result if result else 'null'
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}Error executing command: {command}{Style.RESET_ALL}")
        return 'null'

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = f"az rest --method get --url {RESOURCE}/subscriptions?api-version={API_VERSION_SUBSCRIPTIONS}"
    response = run_command(command)

    if response != 'null':
        try:
            subscriptions = json.loads(response).get("value", [])
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for subscriptions: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve subscriptions.{Style.RESET_ALL}")
    return []

def get_storage_accounts_with_replication_status(subscription_id):
    """Fetches storage accounts and their cross-tenant replication status for a specific subscription."""
    url = f"{RESOURCE}/subscriptions/{subscription_id}/providers/Microsoft.Storage/storageAccounts?api-version={API_VERSION_STORAGE}"
    command = f"az rest --method get --url {url}"
    response = run_command(command)

    if response != 'null':
        try:
            storage_accounts = json.loads(response).get("value", [])
            return [(account["name"], account.get("properties", {}).get("allowCrossTenantReplication", False)) for account in storage_accounts]
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON for storage accounts in subscription {subscription_id}: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve storage accounts for subscription {subscription_id}.{Style.RESET_ALL}")
        return []

def check_cross_tenant_replication(storage_account_info):
    """Checks if cross-tenant replication is enabled or disabled."""
    account_name, allow_cross_tenant = storage_account_info

    if not allow_cross_tenant:
        return True, Fore.GREEN, account_name, "Cross-tenant replication disabled"
    else:
        return False, Fore.RED, account_name, "Cross-tenant replication enabled"

def display_cross_tenant_replication_status():
    """Iterates through each subscription and storage account to check the cross-tenant replication status."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        print("Final Status: FAIL")  
        return

    all_passed = True  

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.YELLOW}Checking storage accounts in subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        storage_accounts = get_storage_accounts_with_replication_status(subscription_id)
        if not storage_accounts:
            print(f"{Fore.RED}No storage accounts found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        for account_info in storage_accounts:
            is_compliant, color, account_name, status = check_cross_tenant_replication(account_info)
            if not is_compliant:
                all_passed = False  
            print(f"Storage Account: {account_name} - {color}{status}{Style.RESET_ALL}")

    
    if all_passed:
        print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")

    
    print("Final Status: PASS" if all_passed else "Final Status: FAIL")



def main():
    """Entry point for cross-tenant replication status check."""
    parser = argparse.ArgumentParser(description="Check cross-tenant replication status for all storage accounts.")
    args = parser.parse_args()

    display_cross_tenant_replication_status()

if __name__ == "__main__":
    main()
