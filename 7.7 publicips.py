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

def list_public_ips():
    """Lists all public IP addresses in the current subscription."""
    command = 'az network public-ip list --output json'
    output, error = run_command(command)
    
    if output:
        try:
            public_ips = json.loads(output)
            print(f"{Fore.CYAN}Public IPs output:\n{output}{Style.RESET_ALL}")
            return public_ips if public_ips else []
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing Public IPs JSON output.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve public IPs. Error: {error}{Style.RESET_ALL}")
    return []

def check_public_ips(subscription_id, subscription_name):
    """Checks for public IPs in the current subscription."""
    print(f"\n{Fore.YELLOW}Checking public IPs for subscription: {subscription_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()

    
    if not set_subscription(subscription_id):
        print(f"{Fore.RED}Failed to set subscription {subscription_name}{Style.RESET_ALL}")
        return False  

    
    public_ips = list_public_ips()
    
    if public_ips:
        print(f"{Fore.RED}Public IPs found in subscription {subscription_name}:{Style.RESET_ALL}")
        for ip in public_ips:
            print(f"{Fore.RED}IP Address: {ip.get('ipAddress', 'Unknown IP')}, Name: {ip.get('name', 'Unnamed')}{Style.RESET_ALL}")
        return False  
    else:
        print(f"{Fore.GREEN}No public IPs exist in subscription {subscription_name}.{Style.RESET_ALL}")
        return True  

def main():
    
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    overall_status = True  

    
    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        compliant = check_public_ips(subscription_id, subscription_name)
        if not compliant:
            overall_status = False

    
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN if overall_status else Fore.RED}{'PASS' if overall_status else 'FAIL'}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
