import subprocess
import json
import colorama
from colorama import Fore, Style
import argparse

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com"
API_VERSION_SUBSCRIPTIONS = "2020-01-01"
API_VERSION_STORAGE = "2021-09-01"
API_VERSION_BLOB = "2021-04-01"

def run_command(command):
    """Runs a shell command and returns the output or None if the command fails."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Error executing command: {e.stderr}{Style.RESET_ALL}")
        return None

def check_authentication():
    """Check if already authenticated with Azure CLI to skip login."""
    try:
        subprocess.run(['az', 'account', 'show'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}Authentication required. Please login using 'az login'.{Style.RESET_ALL}")
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
            accounts = json.loads(response).get("value", [])
            return [{"name": account["name"], "resourceGroup": account["id"].split("/")[4]} for account in accounts]
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for storage accounts: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve storage accounts for subscription {subscription_id}.{Style.RESET_ALL}")
    return []

def check_soft_delete_policy(storage_account, subscription_id):
    """Checks the soft delete policy for a specific storage account."""
    url = f"{RESOURCE}/subscriptions/{subscription_id}/resourceGroups/{storage_account['resourceGroup']}/providers/Microsoft.Storage/storageAccounts/{storage_account['name']}/blobServices/default?api-version={API_VERSION_BLOB}"
    command = f"az rest --method get --url {url}"
    response = run_command(command)

    if response:
        try:
            data = json.loads(response)
            delete_policy = data.get("properties", {}).get("deleteRetentionPolicy", {})
            enabled = delete_policy.get("enabled", False)
            days = delete_policy.get("days", None)

            if enabled and days:
                return True, Fore.GREEN, f"Soft delete enabled for {days} day(s)"
            elif enabled and not days:
                return False, Fore.YELLOW, "Soft delete enabled but no retention days set"
            else:
                return False, Fore.RED, "Soft delete is disabled"
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for soft delete policy: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve soft delete policy for storage account: {storage_account['name']}.{Style.RESET_ALL}")
    return False, Fore.RED, "Unknown status"

def display_soft_delete_status():
    """Iterates through each subscription and storage account to check the soft delete policy for blob storage."""
    if not check_authentication():
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
            print(f"{Fore.RED}No storage accounts found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        for account in storage_accounts:
            is_compliant, color, status = check_soft_delete_policy(account, subscription_id)
            if not is_compliant:
                all_passed = False
            print(f"Storage Account: {account['name']} - {color}{status}{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if is_compliant else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")


def main():
    """Entry point for Soft Delete policy check."""
    parser = argparse.ArgumentParser(description="Check soft delete policy for blob storage across all storage accounts.")
    parser.add_argument(
        "--auth-method",
        choices=["app", "user"],
        default="user",
        help="Specify the authentication method: 'app' for service principal, 'user' for interactive login."
    )
    args = parser.parse_args()

    if args.auth_method == "user":
        if check_authentication():
            display_soft_delete_status()
    else:
        print(f"{Fore.RED}Service principal authentication is not implemented in this script.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
