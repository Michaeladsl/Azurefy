import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def run_command(command):
    """Runs a shell command and returns the output."""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Error executing command: {e.stderr}{Style.RESET_ALL}")
        return None

def get_key_vaults():
    """Retrieve a list of all resources of type Key Vaults in the Azure environment."""
    command = "az resource list --query \"[?type=='Microsoft.KeyVault/vaults']\" -o json"
    result = run_command(command)
    if result:
        try:
            key_vaults = json.loads(result)
            return key_vaults
        except json.JSONDecodeError:
            print(f"{Fore.RED}Failed to parse Key Vault list JSON.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve Key Vault resources.{Style.RESET_ALL}")
        return []

def extract_vault_name(vault_id):
    """Extract the vault name from the full resource ID."""
    return vault_id.split("/")[-1]

def check_purge_protection(vault_id):
    """Check if enablePurgeProtection is set to true for a specific Key Vault."""
    vault_name = extract_vault_name(vault_id)
    print(f"\n{Fore.YELLOW}Checking enablePurgeProtection for Key Vault: {vault_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()
    command = f'az resource show --id {vault_id} -o json'
    result = run_command(command)
    if result:
        try:
            resource_data = json.loads(result)
            properties = resource_data.get("properties", {})
            enable_purge_protection = properties.get("enablePurgeProtection", None)

            
            relevant_json = {
                "enablePurgeProtection": enable_purge_protection,
                "enableSoftDelete": properties.get("enableSoftDelete", None),
                "enabledForDeployment": properties.get("enabledForDeployment", None),
            }
            print(json.dumps(relevant_json, indent=4).replace(
                f'"enablePurgeProtection": {enable_purge_protection}',
                f'"enablePurgeProtection": {Fore.GREEN if enable_purge_protection else Fore.RED}{enable_purge_protection}{Style.RESET_ALL}'
            ))

            
            if enable_purge_protection is True:
                final_status = f"{Fore.GREEN}Pass{Style.RESET_ALL}"
            else:
                final_status = f"{Fore.RED}Fail{Style.RESET_ALL}"

            
            print(f"\nFinal Status: {final_status}")

        except json.JSONDecodeError:
            print(f"{Fore.RED}Failed to parse JSON output for Key Vault: {vault_name}.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve details for Key Vault: {vault_name}.{Style.RESET_ALL}")

def main():
    """Main function to retrieve Key Vaults and check enablePurgeProtection."""
    key_vaults = get_key_vaults()

    if not key_vaults:
        print(f"{Fore.RED}No Key Vault resources found or unable to retrieve Key Vaults.{Style.RESET_ALL}")
        return

    
    for vault in key_vaults:
        vault_id = vault["id"]
        check_purge_protection(vault_id)

if __name__ == "__main__":
    main()
