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

def get_mysql_flexible_servers(subscription_id):
    """Fetches the list of MySQL flexible servers for a specific subscription."""
    command = f"az mysql flexible-server list --subscription {subscription_id} --query '[].{{name:name, resourceGroup:resourceGroup}}' -o json"
    result = run_command(command)
    if result:
        try:
            servers = json.loads(result)
            return servers
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing server JSON: {e}{Style.RESET_ALL}")
    return []

def check_require_secure_transport(server_name, resource_group, subscription_id):
    """Checks if 'require_secure_transport' is set to 'ON' for a specific MySQL flexible server."""
    command = f"az mysql flexible-server parameter show --resource-group {resource_group} --server-name {server_name} --subscription {subscription_id} --name require_secure_transport -o json"
    result = run_command(command)
    
    if result:
        try:
            config = json.loads(result)
            secure_transport = config.get("value", "off")
            print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
            print()

            
            if secure_transport.lower() == "on":
                print(f"MySQL Flexible Server: {server_name} - require_secure_transport: {Fore.GREEN}ON{Style.RESET_ALL}")
                return True
            else:
                print(f"MySQL Flexible Server: {server_name} - require_secure_transport: {Fore.RED}OFF{Style.RESET_ALL}")
                return False
        except json.JSONDecodeError:
            print(f"{Fore.RED}Failed to parse require_secure_transport setting for server {server_name}.{Style.RESET_ALL}")
            return False
    else:
        print(f"{Fore.RED}Failed to retrieve require_secure_transport setting for server {server_name}.{Style.RESET_ALL}")
        return False

def main():
    """Main function to check the 'require_secure_transport' setting for all MySQL flexible servers across subscriptions."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found.{Style.RESET_ALL}")
        return

    overall_compliance = True
    found_servers = False

    for subscription in subscriptions:
        subscription_id = subscription["id"]
        subscription_name = subscription["name"]
        print(f"\n{Fore.YELLOW}Checking MySQL Flexible Servers in subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()
        
        
        servers = get_mysql_flexible_servers(subscription_id)
        if not servers:
            print(f"{Fore.RED}No MySQL flexible servers found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        
        for server in servers:
            found_servers = True
            server_name = server["name"]
            resource_group = server["resourceGroup"]

            is_compliant = check_require_secure_transport(server_name, resource_group, subscription_id)
            if not is_compliant:
                overall_compliance = False

    
    if found_servers:
        print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if overall_compliance else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
