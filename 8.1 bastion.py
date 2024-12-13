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
            return subscriptions if subscriptions else []
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output: {e}{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve subscriptions. Error: {error}{Style.RESET_ALL}")
    return []

def set_subscription(subscription_id):
    """Sets the current Azure subscription."""
    command = f'az account set --subscription {subscription_id}'
    output, error = run_command(command)
    if error:
        print(f"{Fore.RED}Failed to set subscription {subscription_id}. Error: {error}{Style.RESET_ALL}")
    return output is not None

def list_bastion_hosts():
    """Lists all Azure Bastion hosts in the current subscription."""
    command = 'az network bastion list --output json'
    output, error = run_command(command)
    
    if output:
        try:
            bastions = json.loads(output)
            return bastions if bastions else []
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing Bastion Hosts JSON output.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve Bastion Hosts. Error: {error}{Style.RESET_ALL}")
    return []

def check_bastion_hosts(subscription_id, subscription_name):
    """Checks if Azure Bastion is configured in the current subscription."""
    print(f"\n{Fore.YELLOW}Checking Azure Bastion for subscription: {subscription_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()

    
    if not set_subscription(subscription_id):
        print(f"{Fore.RED}Failed to set subscription {subscription_name}{Style.RESET_ALL}")
        return False

    
    bastions = list_bastion_hosts()
    print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
    print()
    if bastions:
        print(f"{Fore.GREEN}Azure Bastion configured in subscription {subscription_name}{Style.RESET_ALL}")
        for bastion in bastions:
            print(f"{Fore.GREEN}Bastion Name: {bastion.get('name', 'Unnamed')}, Location: {bastion.get('location', 'Unknown')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}\n{json.dumps(bastion, indent=4)}{Style.RESET_ALL}")
        return True
    else:
        print(f"{Fore.RED}Azure Bastion not configured in subscription {subscription_name}{Style.RESET_ALL}")
        return False

def main():
    
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    overall_compliant = True

    
    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        compliant = check_bastion_hosts(subscription_id, subscription_name)
        if not compliant:
            overall_compliant = False

    
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN if overall_compliant else Fore.RED}{'PASS' if overall_compliant else 'FAIL'}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
