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

def check_secure_transport_parameter(server_name, resource_group, subscription_id, overall_compliance):
    """Runs the az postgres flexible-server parameter show command to check the require_secure_transport setting."""
    command = f"az postgres flexible-server parameter show --resource-group {resource_group} --server-name {server_name} --subscription {subscription_id} --name require_secure_transport --query value -o json"
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"{Fore.RED}Failed to retrieve require_secure_transport setting for server {server_name}.{Style.RESET_ALL}")
        print(f"{Fore.RED}Error: {result.stderr.strip()}{Style.RESET_ALL}")
        return overall_compliance

    try:
        secure_transport_status = json.loads(result.stdout)
        color = Fore.GREEN if secure_transport_status == "on" else Fore.RED
        status_text = secure_transport_status
        print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
        print()
        print(f"Server: {server_name} - Require Secure Transport: {color}{status_text}{Style.RESET_ALL}")
        
        
        if secure_transport_status != "on":
            overall_compliance = False

    except json.JSONDecodeError:
        print(f"{Fore.RED}Failed to parse the require_secure_transport setting for server {server_name}.{Style.RESET_ALL}")
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
        print(f"\n{Fore.YELLOW}Checking PostgreSQL secure transport settings for subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()
        print()

        servers = get_postgres_servers(subscription_id)
        if not servers:
            print(f"{Fore.RED}No PostgreSQL servers found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        found_servers = True

        for server in servers:
            server_name = server["name"]
            resource_group = server["resourceGroup"]

            print(f"{Fore.YELLOW}Checking secure transport setting for server '{server_name}'...{Style.RESET_ALL}")
            overall_compliance = check_secure_transport_parameter(server_name, resource_group, subscription_id, overall_compliance)

    
    if found_servers:
        print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if overall_compliance else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
