import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com/"
API_VERSION_SUBSCRIPTIONS = "2020-01-01"
API_VERSION_KEYVAULT = "2021-06-01-preview"

def run_command(command):
    """Runs a shell command and returns the output or 'null' if the command fails."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = process.stdout.strip()
        return result if result else 'null'
    except subprocess.CalledProcessError:
        return 'null'

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
    
    if response != 'null':
        try:
            subscriptions = json.loads(response).get("value", [])
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for subscriptions: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve subscriptions.{Style.RESET_ALL}")
    return []

def get_key_vaults(subscription_id):
    """Retrieve a list of all Key Vaults in a specific subscription."""
    url = f"{RESOURCE}subscriptions/{subscription_id}/providers/Microsoft.KeyVault/vaults?api-version={API_VERSION_KEYVAULT}"
    command = f"az rest --method get --url {url}"
    
    response = run_command(command)

    if response != 'null':
        try:
            key_vaults = json.loads(response).get("value", [])
            return key_vaults
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing Key Vault data: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve Key Vaults for subscription {subscription_id}.{Style.RESET_ALL}")
    return []

def extract_vault_name(vault_id):
    """Extract the vault name from the full resource ID."""
    return vault_id.split("/")[-1]

def check_private_endpoint_connections(vault_id):
    """Check if privateEndpointConnections is set for a specific Key Vault."""
    vault_name = extract_vault_name(vault_id)
    print(f"\n{Fore.YELLOW}Checking privateEndpointConnections for Key Vault: {vault_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()
    url = f"{RESOURCE}{vault_id}?api-version={API_VERSION_KEYVAULT}"
    command = f"az rest --method get --url {url}"
    
    response = run_command(command)
    
    if response != 'null':
        try:
            resource_data = json.loads(response)
            private_endpoint_connections = resource_data.get("properties", {}).get("privateEndpointConnections", None)

            
            relevant_json = {
                "privateEndpointConnections": private_endpoint_connections,
                "vaultName": vault_name
            }
            if private_endpoint_connections:
                print(json.dumps(relevant_json, indent=4).replace(
                    f'"privateEndpointConnections": {private_endpoint_connections}',
                    f'"privateEndpointConnections": {Fore.GREEN}{private_endpoint_connections}{Style.RESET_ALL}'
                ))
                final_status = f"{Fore.GREEN}Pass{Style.RESET_ALL}"
            else:
                print(json.dumps(relevant_json, indent=4).replace(
                    f'"privateEndpointConnections": null',
                    f'"privateEndpointConnections": {Fore.RED}null{Style.RESET_ALL}'
                ))
                final_status = f"{Fore.RED}Fail{Style.RESET_ALL}"

            
            print(f"\nFinal Status: {final_status}")

        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing Key Vault details for {vault_name}: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve details for Key Vault: {vault_name}.{Style.RESET_ALL}")

def display_key_vault_private_endpoint_connections():
    """Iterates through each subscription and retrieves Key Vault information with color-coded privateEndpointConnections settings."""
    if not check_authentication():
        print(f"{Fore.RED}Please authenticate using the main script first.{Style.RESET_ALL}")
        return

    subscriptions = get_subscriptions()

    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found.{Style.RESET_ALL}")
        return

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]

        
        key_vaults = get_key_vaults(subscription_id)
        if not key_vaults:
            print(f"{Fore.YELLOW}No Key Vaults found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        
        for vault in key_vaults:
            vault_id = vault["id"]
            check_private_endpoint_connections(vault_id)

def main():
    """Main function to display Key Vault privateEndpointConnections for all subscriptions."""
    display_key_vault_private_endpoint_connections()

if __name__ == "__main__":
    main()
