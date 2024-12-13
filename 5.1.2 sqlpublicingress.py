import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)


RESOURCE = "https://management.azure.com"
API_VERSION_SQL = "2021-02-01-preview"
API_VERSION_SUBSCRIPTIONS = "2020-01-01"

def run_command(command):
    """Runs a shell command and returns the output or None if the command fails."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Error executing command: {e.stderr.strip()}{Style.RESET_ALL}")
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
            print(f"{Fore.RED}Error parsing subscriptions JSON: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve subscriptions.{Style.RESET_ALL}")
    return []

def get_sql_servers(subscription_id):
    """Fetches the list of SQL servers for a specific subscription."""
    url = f"{RESOURCE}/subscriptions/{subscription_id}/providers/Microsoft.Sql/servers?api-version={API_VERSION_SQL}"
    command = f"az rest --method get --url {url}"
    response = run_command(command)

    if response:
        try:
            sql_servers = json.loads(response).get("value", [])
            return sql_servers
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing SQL servers JSON: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve SQL servers for subscription ID {subscription_id}.{Style.RESET_ALL}")
    return []

def get_firewall_rules(resource_group, sql_server, subscription_id):
    """Fetches the firewall rules for a specific SQL server."""
    url = f"{RESOURCE}/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Sql/servers/{sql_server}/firewallRules?api-version={API_VERSION_SQL}"
    command = f"az rest --method get --url {url}"
    response = run_command(command)

    if response:
        try:
            return json.loads(response).get("value", [])
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing firewall rules JSON: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve firewall rules for SQL server {sql_server}.{Style.RESET_ALL}")
    return []

def check_firewall_rules(firewall_rules):
    """Checks if any firewall rules allow traffic from '0.0.0.0/0' or are named 'AllowAllWindowsAzureIps'."""
    non_compliant_rules = []
    compliant_rules = []

    for rule in firewall_rules:
        rule_name = rule.get("name", "Unknown")
        start_ip = rule.get("properties", {}).get("startIpAddress", "")
        end_ip = rule.get("properties", {}).get("endIpAddress", "")

        if start_ip == "0.0.0.0" or end_ip == "0.0.0.0" or rule_name == "AllowAllWindowsAzureIps":
            non_compliant_rules.append((rule_name, start_ip, end_ip))
        else:
            compliant_rules.append((rule_name, start_ip, end_ip))

    return non_compliant_rules, compliant_rules

def display_firewall_rules_status(subscription_name, sql_server, resource_group, subscription_id, overall_compliance):
    """Displays the compliance status of firewall rules for a specific SQL server."""
    firewall_rules = get_firewall_rules(resource_group, sql_server, subscription_id)

    if not firewall_rules:
        print(f"{Fore.RED}No firewall rules found for SQL server: {sql_server}.{Style.RESET_ALL}")
        return overall_compliance

    non_compliant_rules, compliant_rules = check_firewall_rules(firewall_rules)
    print(f"\n{Fore.CYAN}Firewall rules for SQL server: {sql_server}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
    print()

    for rule_name, start_ip, end_ip in non_compliant_rules:
        print(f"{Fore.RED}Non-compliant Rule: {rule_name}, Start IP: {start_ip}, End IP: {end_ip}{Style.RESET_ALL}")
        overall_compliance = False

    for rule_name, start_ip, end_ip in compliant_rules:
        print(f"{Fore.GREEN}Compliant Rule: {rule_name}, Start IP: {start_ip}, End IP: {end_ip}{Style.RESET_ALL}")

    return overall_compliance

def display_sql_firewall_compliance_status():
    """Iterates through each subscription, SQL server, and firewall rule to check for compliance."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found.{Style.RESET_ALL}")
        return

    found_sql_servers = False
    overall_compliance = True

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.YELLOW}Checking SQL servers for public access...{Style.RESET_ALL}")
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
            overall_compliance = display_firewall_rules_status(subscription_name, sql_server_name, resource_group, subscription_id, overall_compliance)

    
    if found_sql_servers:
        print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if overall_compliance else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")


def main():
    """Entry point for SQL Server firewall rule compliance check."""
    display_sql_firewall_compliance_status()

if __name__ == "__main__":
    main()