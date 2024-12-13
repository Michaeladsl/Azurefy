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

def get_sql_servers(subscription_id):
    """Fetches the list of SQL servers for a specific subscription."""
    command = f"az sql server list --subscription {subscription_id} --query '[].{{name:name, resourceGroup:resourceGroup}}' -o json"
    result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE)
    sql_servers = json.loads(result.stdout)
    return sql_servers

def check_audit_settings(resource_group, server_name, subscription_id):
    """Checks the audit settings for a specific SQL server."""
    command = f"az sql server audit-policy show --resource-group {resource_group} --server-name {server_name} --subscription {subscription_id} -o json"
    result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"{Fore.RED}Failed to retrieve audit settings for server {server_name}.{Style.RESET_ALL}")
        print(f"{Fore.RED}Error: {result.stderr.strip()}{Style.RESET_ALL}")
        return None

    try:
        audit_settings = json.loads(result.stdout)
        
        blob_storage_state = audit_settings.get("blobStorageTargetState", "Disabled")
        event_hub_state = audit_settings.get("eventHubTargetState", "Disabled")
        log_analytics_state = audit_settings.get("logAnalyticsTargetState", "Disabled")

        
        compliant = "Enabled" in [blob_storage_state, event_hub_state, log_analytics_state]
        if compliant:
            print(f"Server: {server_name} - Audit Setting: {Fore.GREEN}Compliant (At least one target is enabled){Style.RESET_ALL}")
        else:
            print(f"Server: {server_name} - Audit Setting: {Fore.RED}Non-Compliant (No target enabled){Style.RESET_ALL}")
            print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
            print()
        return compliant
    except json.JSONDecodeError:
        print(f"{Fore.RED}Failed to parse the audit settings for server {server_name}.{Style.RESET_ALL}")
        return None

def main():
    """Main script function."""
    subscriptions = get_subscriptions()
    overall_compliance = True
    found_sql_servers = False

    for subscription in subscriptions:
        subscription_id = subscription["id"]
        subscription_name = subscription["name"]
        print(f"\n{Fore.YELLOW}Checking SQL servers auditing status...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        sql_servers = get_sql_servers(subscription_id)
        if not sql_servers:
            print(f"{Fore.RED}No SQL servers found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        found_sql_servers = True  

        for server in sql_servers:
            server_name = server["name"]
            resource_group = server["resourceGroup"]

            print(f"{Fore.YELLOW}Checking audit settings for SQL server '{server_name}'...{Style.RESET_ALL}")
            compliant = check_audit_settings(resource_group, server_name, subscription_id)
            if compliant is False:  
                overall_compliance = False

    
    if found_sql_servers:
        print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if overall_compliance else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
