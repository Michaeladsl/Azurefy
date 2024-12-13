import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def get_subscriptions():
    command = "az account list --query '[].{id:id, name:name}' -o json"
    result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE)
    subscriptions = json.loads(result.stdout)
    return subscriptions

def get_postgres_servers(subscription_id):
    command = f"az postgres flexible-server list --subscription {subscription_id} --query '[].{{name:name, resourceGroup:resourceGroup}}' -o json"
    result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE)
    servers = json.loads(result.stdout)
    return servers

def check_log_checkpoints_parameter(server_name, resource_group, subscription_id):
    command = f"az postgres flexible-server parameter show --resource-group {resource_group} --server-name {server_name} --subscription {subscription_id} --name log_checkpoints --query value -o json"
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"{Fore.RED}Failed to retrieve log_checkpoints setting for server {server_name}.{Style.RESET_ALL}")
        print(f"{Fore.RED}Error: {result.stderr.strip()}{Style.RESET_ALL}")
        return None

    try:
        log_checkpoints_status = json.loads(result.stdout)
        color = Fore.GREEN if log_checkpoints_status == "on" else Fore.RED
        status_text = log_checkpoints_status
        print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
        print()
        print(f"Server: {server_name} - Log Checkpoints: {color}{status_text}{Style.RESET_ALL}")
        return log_checkpoints_status
    except json.JSONDecodeError:
        print(f"{Fore.RED}Failed to parse the log_checkpoints setting for server {server_name}.{Style.RESET_ALL}")
        return None

def main():
    subscriptions = get_subscriptions()

    for subscription in subscriptions:
        subscription_id = subscription["id"]
        subscription_name = subscription["name"]
        print(f"\n{Fore.YELLOW}Checking PostgreSQL log checkpoints in subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        servers = get_postgres_servers(subscription_id)
        if not servers:
            print(f"{Fore.RED}No PostgreSQL servers found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        for server in servers:
            server_name = server["name"]
            resource_group = server["resourceGroup"]

            print(f"{Fore.YELLOW}Checking log checkpoint setting for PostgreSQL server '{server_name}'...{Style.RESET_ALL}")
            check_log_checkpoints_parameter(server_name, resource_group, subscription_id)

if __name__ == "__main__":
    main()
