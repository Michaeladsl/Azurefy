import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

FORBIDDEN_ERROR_MESSAGE = "ERROR: (Forbidden) Caller is not authorized to perform action on resource."

def run_command(command):
    """Runs a shell command and returns the output."""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        if FORBIDDEN_ERROR_MESSAGE in e.stderr:
            print(f"{Fore.RED}{FORBIDDEN_ERROR_MESSAGE}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Error executing command: {e.stderr}{Style.RESET_ALL}")
        return None

def get_key_vaults():
    """Retrieve a list of all key vaults in the Azure environment."""
    print(f"{Fore.YELLOW}Retrieving list of Key Vaults...{Style.RESET_ALL}")
    command = 'az keyvault list -o json'
    result = run_command(command)
    if result:
        try:
            key_vaults = json.loads(result)
            return key_vaults
        except json.JSONDecodeError:
            print(f"{Fore.RED}Failed to parse Key Vault list JSON.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve Key Vaults.{Style.RESET_ALL}")
        return []

def get_keys_for_vault(vault_name):
    """Retrieve a list of keys for a specific Key Vault."""
    print(f"{Fore.YELLOW}Retrieving keys for Key Vault: {vault_name}{Style.RESET_ALL}")
    command = f'az keyvault key list --vault-name {vault_name} --query "[*].{{kid:kid,enabled:attributes.enabled,expires:attributes.expires}}" -o json'
    result = run_command(command)
    if result:
        try:
            keys = json.loads(result)
            return keys
        except json.JSONDecodeError:
            print(f"{Fore.RED}Failed to parse Key list JSON for vault: {vault_name}.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve keys for vault: {vault_name}.{Style.RESET_ALL}")
        return []

def display_key_info(vault_name, key):
    """Displays information for a specific key with color-coded formatting."""
    print(f"{Fore.CYAN}Vault: {vault_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Key ID:{Style.RESET_ALL} {key['kid']}")

    
    enabled_status = key["enabled"]
    if enabled_status:
        print(f"{Fore.GREEN}Enabled: {enabled_status}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Enabled: {enabled_status}{Style.RESET_ALL}")

    
    expiration = key.get("expires")
    if expiration:
        print(f"{Fore.GREEN}Expiration: {expiration}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Expiration: Not set{Style.RESET_ALL}")

    print("-" * 40)

def main():
    
    key_vaults = get_key_vaults()

    if not key_vaults:
        print(f"{Fore.RED}No Key Vaults found or unable to retrieve Key Vaults.{Style.RESET_ALL}")
        return

    
    for vault in key_vaults:
        vault_name = vault["name"]
        
        
        keys = get_keys_for_vault(vault_name)
        
        if keys is None:  
            continue
        
        if not keys:
            print(f"{Fore.RED}No keys found or unable to retrieve keys for vault: {vault_name}{Style.RESET_ALL}")
            continue
        
        
        for key in keys:
            display_key_info(vault_name, key)

if __name__ == "__main__":
    main()
