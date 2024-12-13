import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

RESOURCE = "https://management.azure.com"
API_VERSION_ENCRYPTION_PROTECTOR = "2015-05-01-preview"
API_VERSION_SUBSCRIPTIONS = "2020-01-01"
API_VERSION_SQL_SERVERS = "2021-02-01-preview"
EXPECTED_KIND = "azurekeyvault"
EXPECTED_SERVER_KEY_TYPE = "AzureKeyVault"

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

def get_sql_servers(subscription_id):
    """Fetches the list of SQL servers for a specific subscription."""
    url = f"{RESOURCE}/subscriptions/{subscription_id}/providers/Microsoft.Sql/servers?api-version={API_VERSION_SQL_SERVERS}"
    command = f"az rest --method get --url {url}"
    response = run_command(command)

    if response:
        try:
            return json.loads(response).get("value", [])
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for SQL servers: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve SQL servers for subscription ID {subscription_id}.{Style.RESET_ALL}")
    return []

def check_encryption_protector(resource_group, sql_server, subscription_id, overall_compliance):
    """Checks the encryption protector settings for a specific SQL server."""
    url = f"{RESOURCE}/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Sql/servers/{sql_server}/encryptionProtector?api-version={API_VERSION_ENCRYPTION_PROTECTOR}"
    command = f"az rest --method get --url {url}"
    response = run_command(command)

    if response:
        try:
            encryption_data = json.loads(response).get("properties", {})
            kind = encryption_data.get("kind", "Unknown")
            server_key_type = encryption_data.get("serverKeyType", "Unknown")
            uri = encryption_data.get("uri", "None")
            print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
            print()

            if kind == EXPECTED_KIND and server_key_type == EXPECTED_SERVER_KEY_TYPE and uri:
                print(f"{Fore.GREEN}Compliant - Kind: {kind}, ServerKeyType: {server_key_type}, URI: {uri}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Non-Compliant - Kind: {kind}, ServerKeyType: {server_key_type}, URI: {uri}{Style.RESET_ALL}")
                overall_compliance = False
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing encryption protector JSON: {e}{Style.RESET_ALL}")
            overall_compliance = False
    else:
        print(f"{Fore.RED}Failed to retrieve encryption protector for SQL server {sql_server}.{Style.RESET_ALL}")
        overall_compliance = False

    return overall_compliance

def display_encryption_protector_compliance():
    """Iterates through each subscription and SQL server to check encryption protector settings."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found.{Style.RESET_ALL}")
        return

    found_sql_servers = False
    overall_compliance = True

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.YELLOW}Checking SQL servers CMK for TDE in subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        sql_servers = get_sql_servers(subscription_id)
        if not sql_servers:
            print(f"{Fore.RED}No SQL servers found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        found_sql_servers = True

        for server in sql_servers:
            sql_server_name = server["name"]
            resource_group = server["id"].split("/")[4]  
            overall_compliance = check_encryption_protector(resource_group, sql_server_name, subscription_id, overall_compliance)

    
    if found_sql_servers:
        print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if overall_compliance else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")


def main():
    """Entry point for Encryption Protector compliance check."""
    display_encryption_protector_compliance()

if __name__ == "__main__":
    main()
