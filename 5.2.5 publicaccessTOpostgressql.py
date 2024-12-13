import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def run_command(command):
    """Runs a shell command and returns the output and error."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, e.stderr.strip()

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = "az account list --query '[].{id:id, name:name}' -o json"
    output, error = run_command(command)
    if error:
        print(f"{Fore.RED}Failed to retrieve subscriptions: {error}{Style.RESET_ALL}")
        return []
    
    return json.loads(output)

def get_postgres_servers(subscription_id):
    """Fetches the list of PostgreSQL Flexible Servers for a specific subscription."""
    command = f"az postgres flexible-server list --subscription {subscription_id} --query '[].{{name:name, resourceGroup:resourceGroup}}' -o json"
    output, error = run_command(command)
    if error:
        print(f"{Fore.RED}Failed to retrieve PostgreSQL servers for subscription {subscription_id}: {error}{Style.RESET_ALL}")
        return []
    
    return json.loads(output)

def check_firewall_rules(server_name, resource_group, subscription_id, overall_compliance):
    """Checks the firewall rules for a specific PostgreSQL server."""
    print(f"{Fore.CYAN}Checking firewall rules for server '{server_name}'...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
    print()
    command = f"az postgres flexible-server firewall-rule list --resource-group {resource_group} --name {server_name} --subscription {subscription_id} -o json"
    output, error = run_command(command)

    if error:
        
        if "Firewall rule operations cannot be requested for a private access enabled server" in error:
            print(f"{Fore.GREEN}Server '{server_name}' is private-access only. No public access rules.{Style.RESET_ALL}")
            return overall_compliance
        else:
            print(f"{Fore.RED}Failed to retrieve firewall rules for server {server_name}: {error}{Style.RESET_ALL}")
            return False

    try:
        rules = json.loads(output)
        for rule in rules:
            rule_name = rule.get("name", "Unknown")
            start_ip = rule.get("startIpAddress", "")
            end_ip = rule.get("endIpAddress", "")
            
            
            if rule_name.startswith("AllowAllAzureServicesAndResourcesWithinAzureIps") or start_ip == "0.0.0.0" or end_ip == "0.0.0.0":
                print(f"{Fore.RED}Non-compliant Rule: {rule_name} - Start IP: {start_ip} - End IP: {end_ip}{Style.RESET_ALL}")
                overall_compliance = False
            else:
                print(f"{Fore.GREEN}Compliant Rule: {rule_name} - Start IP: {start_ip} - End IP: {end_ip}{Style.RESET_ALL}")
    except json.JSONDecodeError:
        print(f"{Fore.RED}Failed to parse firewall rules for server {server_name}.{Style.RESET_ALL}")
        overall_compliance = False

    return overall_compliance

def main():
    """Main script function."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found. Exiting.{Style.RESET_ALL}")
        return

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

            overall_compliance = check_firewall_rules(server_name, resource_group, subscription_id, overall_compliance)

    
    if found_servers:
        print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if overall_compliance else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
