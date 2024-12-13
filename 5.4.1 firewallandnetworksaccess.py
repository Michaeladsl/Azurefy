import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def run_command(command):
    """Runs a shell command and returns the output or None if the command fails."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Error executing command: {e.stderr}{Style.RESET_ALL}")
        return None

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = "az account list --query '[].{id:id, name:name}' -o json"
    result = run_command(command)
    if result:
        try:
            subscriptions = json.loads(result)
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve subscriptions.{Style.RESET_ALL}")
    return []

def get_cosmosdb_accounts(subscription_id):
    """Fetches the list of CosmosDB accounts for a specific subscription."""
    command = f"az cosmosdb list --subscription {subscription_id} -o json"
    result = run_command(command)
    if result:
        try:
            cosmosdb_accounts = json.loads(result)
            return cosmosdb_accounts
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing CosmosDB accounts JSON: {e}{Style.RESET_ALL}")
    return []

def check_virtual_network_filter(account_id, subscription_id):
    """Checks if the isVirtualNetworkFilterEnabled setting is enabled for a specific CosmosDB account."""
    command = f"az cosmosdb show --id {account_id} --subscription {subscription_id} -o json"
    result = run_command(command)
    
    if result:
        try:
            config = json.loads(result)
            vnet_filter_enabled = config.get("isVirtualNetworkFilterEnabled", False)
            print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
            print()
            
            
            if vnet_filter_enabled:
                print(f"CosmosDB Account: {config['name']} - isVirtualNetworkFilterEnabled: {Fore.GREEN}true{Style.RESET_ALL}")
                return True
            else:
                print(f"CosmosDB Account: {config['name']} - isVirtualNetworkFilterEnabled: {Fore.RED}false{Style.RESET_ALL}")
                return False
        except json.JSONDecodeError:
            print(f"{Fore.RED}Failed to parse isVirtualNetworkFilterEnabled setting for CosmosDB account {account_id}.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve isVirtualNetworkFilterEnabled setting for CosmosDB account {account_id}.{Style.RESET_ALL}")
    return False

def main():
    """Main function to check isVirtualNetworkFilterEnabled setting for all CosmosDB accounts across subscriptions."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found.{Style.RESET_ALL}")
        return

    overall_compliance = True
    found_accounts = False

    for subscription in subscriptions:
        subscription_id = subscription["id"]
        subscription_name = subscription["name"]
        print(f"\n{Fore.YELLOW}Checking CosmosDB accounts in subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()
        
        
        cosmosdb_accounts = get_cosmosdb_accounts(subscription_id)
        if not cosmosdb_accounts:
            print(f"{Fore.RED}No CosmosDB accounts found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        
        for account in cosmosdb_accounts:
            found_accounts = True
            account_id = account["id"]
            compliant = check_virtual_network_filter(account_id, subscription_id)
            if not compliant:
                overall_compliance = False

    
    if found_accounts:
        print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if overall_compliance else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
