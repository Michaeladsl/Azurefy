import json
import subprocess
import colorama
import requests
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

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = "az account list --all --query '[].{id:id, subscriptionId:id, displayName:name}'"
    result = run_command(command)
    
    if result:
        try:
            subscriptions = json.loads(result)
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output: {e}{Style.RESET_ALL}")
            return []
    return []

def get_key_vaults(subscription_id):
    """Lists all key vaults for a specific subscription."""
    command = f'az keyvault list --subscription {subscription_id} --output json'
    result = run_command(command)
    
    if result:
        try:
            key_vaults = json.loads(result)
            return key_vaults if key_vaults else []
        except json.JSONDecodeError:
            return []
    return []

def check_key_vault_diagnostic_settings(key_vault_id):
    """Checks diagnostic settings for a given key vault."""
    command = f'az monitor diagnostic-settings list --resource {key_vault_id} --output json'
    result = run_command(command)
    
    
    print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
    print()
    print(result)

    if result:
        try:
            diagnostic_settings = json.loads(result)
            return diagnostic_settings if diagnostic_settings else []
        except json.JSONDecodeError:
            return []
    return []

def highlight_non_compliant(json_data):
    """Highlights non-compliant configurations in red."""
    json_str = json.dumps(json_data, indent=4)
    json_str = json_str.replace('"categoryGroup": "allLogs", "enabled": false', f'{Fore.RED}"categoryGroup": "allLogs", "enabled": false{Style.RESET_ALL}')
    json_str = json_str.replace('"categoryGroup": "audit", "enabled": false', f'{Fore.RED}"categoryGroup": "audit", "enabled": false{Style.RESET_ALL}')
    json_str = json_str.replace('"storageAccountId": null', f'{Fore.RED}"storageAccountId": null{Style.RESET_ALL}')
    return json_str

def check_diagnostic_settings(settings):
    """Checks if the diagnostic settings are compliant."""
    storage_account_id = settings.get("storageAccountId", None)
    logs = settings.get("logs", [])
    
    compliant = True
    non_compliant_logs = []

    
    if storage_account_id is None:
        compliant = False

    for log in logs:
        category_group = log.get("categoryGroup")
        enabled = log.get("enabled")
        if (category_group in ["audit", "allLogs"]) and not enabled:
            non_compliant_logs.append(log)
            compliant = False

    if compliant:
        return True, None
    else:
        return False, {"storageAccountId": storage_account_id, "logs": non_compliant_logs}

def display_key_vault_logging_status():
    """Iterates through each subscription and key vault to check diagnostic settings."""
    
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    all_compliant = True
    key_vaults_checked = 0

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.YELLOW}Checking key vault logging for subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        
        key_vaults = get_key_vaults(subscription_id)
        if not key_vaults:
            print(f"{Fore.YELLOW}No key vaults in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        
        for key_vault in key_vaults:
            key_vault_name = key_vault["name"]
            key_vault_id = key_vault["id"]
            diagnostic_settings = check_key_vault_diagnostic_settings(key_vault_id)
            key_vaults_checked += 1
            
            if not diagnostic_settings:
                print(f"Key Vault: {key_vault_name} - {Fore.RED}No diagnostic settings found{Style.RESET_ALL}")
                all_compliant = False
                continue

            
            for setting in diagnostic_settings:
                compliant, non_compliant_data = check_diagnostic_settings(setting)
                if compliant:
                    print(f"Key Vault: {key_vault_name} - {Fore.GREEN}Key vault logging enabled{Style.RESET_ALL}")
                else:
                    all_compliant = False
                    print(f"Key Vault: {key_vault_name} - {Fore.RED}Key vault logging disabled{Style.RESET_ALL}")
                    highlighted_output = highlight_non_compliant(non_compliant_data)
                    print(f"{highlighted_output}")

    
    if key_vaults_checked > 0:
        
        if all_compliant:
            print(f"\n{Fore.GREEN}Final Status: PASS - All Key Vaults have logging enabled.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}Final Status: FAIL - Some Key Vaults do not have logging enabled.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}No Key Vaults found. Final status not applicable.{Style.RESET_ALL}")

def main():
    display_key_vault_logging_status()

if __name__ == "__main__":
    main()
