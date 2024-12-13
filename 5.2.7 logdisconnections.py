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

def get_postgres_single_servers(subscription_id):
    """Fetches the list of PostgreSQL Single Servers for a specific subscription."""
    command = f"az postgres server list --subscription {subscription_id} --query '[].{{name:name, resourceGroup:resourceGroup}}' -o json"
    result = run_command(command)
    if result:
        try:
            servers = json.loads(result)
            return servers
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing server JSON: {e}{Style.RESET_ALL}")
    return []

def check_log_disconnections_setting(server_name, resource_group, subscription_id):
    """Checks if 'log_disconnections' is set to 'on' for a PostgreSQL Single Server."""
    command = f"az postgres server configuration show --resource-group {resource_group} --server-name {server_name} --subscription {subscription_id} --name log_disconnections -o json"
    result = run_command(command)
    
    if result:
        try:
            config = json.loads(result)
            log_disconnections = config.get("value", "off")
            print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
            print()

            
            if log_disconnections.lower() == "on":
                print(f"PostgreSQL Server: {server_name} - log_disconnections: {Fore.GREEN}ON{Style.RESET_ALL}")
                return True
            else:
                print(f"PostgreSQL Server: {server_name} - log_disconnections: {Fore.RED}OFF{Style.RESET_ALL}")
                return False
        except json.JSONDecodeError:
            print(f"{Fore.RED}Failed to parse log_disconnections setting for server {server_name}.{Style.RESET_ALL}")
            return False
    else:
        print(f"{Fore.RED}Failed to retrieve log_disconnections setting for server {server_name}.{Style.RESET_ALL}")
        return False

def main():
    """Main function to check the 'log_disconnections' setting for all PostgreSQL Single Servers across subscriptions."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found.{Style.RESET_ALL}")
        return

    overall_compliance = True
    found_servers = False

    for subscription in subscriptions:
        subscription_id = subscription["id"]
        subscription_name = subscription["name"]
        print(f"\n{Fore.YELLOW}Checking PostgreSQL Single Servers in subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()
        
        
        servers = get_postgres_single_servers(subscription_id)
        if not servers:
            print(f"{Fore.YELLOW}No PostgreSQL Single Servers found in subscription: {subscription_name}.{Style.RESET_ALL}")
            continue

        for server in servers:
            found_servers = True
            server_name = server["name"]
            resource_group = server["resourceGroup"]

            is_compliant = check_log_disconnections_setting(server_name, resource_group, subscription_id)
            if not is_compliant:
                overall_compliance = False

    
    if found_servers:
        print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if overall_compliance else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
