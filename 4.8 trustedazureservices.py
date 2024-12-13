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
        print(f"{Fore.RED}Error executing command: {e.stderr}{Style.RESET_ALL}")
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
            return json.loads(response).get("value", [])
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON for storage accounts in subscription {subscription_id}: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve storage accounts for subscription {subscription_id}.{Style.RESET_ALL}")
    return []

def check_bypass_setting(storage_account):
    """Checks if the 'AzureServices' bypass setting is included in a specific storage account's network ACLs."""
    network_acls = storage_account.get("properties", {}).get("networkAcls", {})
    bypass = network_acls.get("bypass", "Unknown")
    
    if "AzureServices" in bypass:
        return True, Fore.GREEN, "Trusted Azure Services Allowed", None
    else:
        return False, Fore.RED, f"Bypass: {bypass}", network_acls

def display_bypass_status():
    """Iterates through each subscription and checks the bypass setting for each storage account."""
    if not check_authentication():
        print(f"{Fore.RED}Please authenticate using the main script first.{Style.RESET_ALL}")
        print("Final Status: FAIL")  
        return

    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found.{Style.RESET_ALL}")
        print("Final Status: FAIL")  
        return

    all_compliant = True

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.YELLOW}Checking allow Azure Services...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        storage_accounts = get_storage_accounts(subscription_id)
        if not storage_accounts:
            print(f"{Fore.RED}No storage accounts found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        for account in storage_accounts:
            account_name = account["name"]
            compliant, color, status, proof = check_bypass_setting(account)
            print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
            print()
            print(f"Storage Account: {account_name} - {color}{status}{Style.RESET_ALL}")

            if not compliant:
                all_compliant = False
                print(f"{Fore.CYAN}Sample JSON Proof for {account_name}:{Style.RESET_ALL}")
                print(json.dumps(proof, indent=4))

    
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if all_compliant else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")

    
    print("Final Status: PASS" if all_compliant else "Final Status: FAIL")



def main():
    """Entry point for bypass compliance check."""
    display_bypass_status()

if __name__ == "__main__":
    main()
