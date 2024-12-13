import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = "az account list --query '[].{id:id, name:name}' -o json"
    result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE)
    subscriptions = json.loads(result.stdout)
    return subscriptions

def get_postgres_servers(subscription_id):
    """Fetches the list of PostgreSQL Flexible Servers for a specific subscription."""
    command = f"az postgres flexible-server list --subscription {subscription_id} --query '[].{{name:name, resourceGroup:resourceGroup}}' -o json"
    result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE)
    servers = json.loads(result.stdout)
    return servers

def check_retention_days(server_name, resource_group, subscription_id, overall_compliance):
    """Runs the az postgres flexible-server parameter show command to check the logfiles.retention_days setting."""
    command = f"az postgres flexible-server parameter show --resource-group {resource_group} --server-name {server_name} --subscription {subscription_id} --name logfiles.retention_days --query value -o json"
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"{Fore.RED}Failed to retrieve logfiles.retention_days setting for server {server_name}.{Style.RESET_ALL}")
        print(f"{Fore.RED}Error: {result.stderr.strip()}{Style.RESET_ALL}")
        return overall_compliance

    try:
        retention_days = int(json.loads(result.stdout))
        color = Fore.GREEN if retention_days > 3 else Fore.RED
        print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
        print()
        print(f"Server: {server_name} - logfiles.retention_days: {color}{retention_days}{Style.RESET_ALL}")

        
        if retention_days <= 3:
            overall_compliance = False

    except (json.JSONDecodeError, ValueError):
        print(f"{Fore.RED}Failed to parse the logfiles.retention_days setting for server {server_name}.{Style.RESET_ALL}")
        overall_compliance = False

    return overall_compliance

def main():
    """Main script function."""
    subscriptions = get_subscriptions()
    overall_compliance = True
    found_servers = False

    for subscription in subscriptions:
        subscription_id = subscription["id"]
        subscription_name = subscription["name"]
        print(f"\n{Fore.YELLOW}Checking PostgreSQL Flexible Servers in subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        servers = get_postgres_servers(subscription_id)
        if not servers:
            print(f"{Fore.RED}No PostgreSQL servers found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        found_servers = True

        for server in servers:
            server_name = server["name"]
            resource_group = server["resourceGroup"]

            print(f"{Fore.CYAN}Checking logfiles.retention_days setting for PostgreSQL server '{server_name}'...{Style.RESET_ALL}")
            overall_compliance = check_retention_days(server_name, resource_group, subscription_id, overall_compliance)

    
    if found_servers:
        print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if overall_compliance else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
