import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def run_command(command):
    """Runs a shell command and returns the output and any error encountered."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, str(e)

def get_subscriptions():
    """Fetches a list of all Azure subscriptions."""
    command = "az account list --all --query '[].{id:id, subscriptionId:id, displayName:name}'"
    output, error = run_command(command)
    
    if output:
        try:
            subscriptions = json.loads(output)
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output: {e}{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve subscriptions. Error: {error}{Style.RESET_ALL}")
    return []

def get_network_security_groups(subscription_id):
    """Lists all network security groups with their corresponding security rules for a specific subscription."""
    command = f'az network nsg list --subscription {subscription_id} --query "[*].[name,securityRules]" --output json'
    output, error = run_command(command)
    
    if output:
        try:
            nsgs = json.loads(output)
            return nsgs if nsgs else []
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing JSON output for NSG list in subscription {subscription_id}.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve network security groups for subscription {subscription_id}. Error: {error}{Style.RESET_ALL}")
    return []

def is_rule_non_compliant(rule):
    """Checks if a given security rule is non-compliant based on specified conditions."""
    access = rule.get("access", "")
    destination_port_range = rule.get("destinationPortRange", "")
    direction = rule.get("direction", "")
    protocol = rule.get("protocol", "")
    source_address_prefix = rule.get("sourceAddressPrefix", "")
    
    
    return (access == "Allow" and
            direction == "Inbound" and
            (protocol == "TCP" or protocol == "*") and
            (destination_port_range == "3389" or destination_port_range == "*" or "3389" in destination_port_range) and
            (source_address_prefix in ["*", "0.0.0.0", "/0", "internet", "any"] or "/0" in source_address_prefix))

def highlight_non_compliant_rule(rule):
    """Highlights non-compliant parts of the rule in red."""
    rule_str = json.dumps(rule, indent=4)
    rule_str = rule_str.replace('"Allow"', f'{Fore.RED}"Allow"{Style.RESET_ALL}')
    rule_str = rule_str.replace('"3389"', f'{Fore.RED}"3389"{Style.RESET_ALL}')
    rule_str = rule_str.replace('"Inbound"', f'{Fore.RED}"Inbound"{Style.RESET_ALL}')
    rule_str = rule_str.replace('"TCP"', f'{Fore.RED}"TCP"{Style.RESET_ALL}')
    rule_str = rule_str.replace('"*"', f'{Fore.RED}"*"{Style.RESET_ALL}')
    rule_str = rule_str.replace('"0.0.0.0"', f'{Fore.RED}"0.0.0.0"{Style.RESET_ALL}')
    rule_str = rule_str.replace('"/0"', f'{Fore.RED}"/0"{Style.RESET_ALL}')
    rule_str = rule_str.replace('"internet"', f'{Fore.RED}"internet"{Style.RESET_ALL}')
    rule_str = rule_str.replace('"any"', f'{Fore.RED}"any"{Style.RESET_ALL}')
    return rule_str

def check_nsg_security_rules(subscription_id, nsgs):
    """Checks each network security group for non-compliant security rules."""
    non_compliant_found = False

    for nsg in nsgs:
        nsg_name = nsg[0]
        security_rules = nsg[1]

        for rule in security_rules:
            if is_rule_non_compliant(rule):
                print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
                print()
                non_compliant_found = True
                print(f"\n{Fore.RED}Non-compliant security rule found in NSG: {nsg_name}{Style.RESET_ALL}")
                highlighted_rule = highlight_non_compliant_rule(rule)
                print(f"{Fore.CYAN}Original command output for non-compliant rule:\n{json.dumps(rule, indent=4)}{Style.RESET_ALL}")
                print(highlighted_rule)
    
    return non_compliant_found

def display_nsg_compliance_status():
    """Iterates through each subscription and checks for non-compliant NSG security rules."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    overall_status = "pass"

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.YELLOW}Checking NSGs for subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        
        nsgs = get_network_security_groups(subscription_id)
        if not nsgs:
            print(f"{Fore.YELLOW}No network security groups found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        
        if check_nsg_security_rules(subscription_id, nsgs):
            overall_status = "fail"

    
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN if overall_status == 'pass' else Fore.RED}{overall_status.upper()}{Style.RESET_ALL}")

def main():
    display_nsg_compliance_status()

if __name__ == "__main__":
    main()
