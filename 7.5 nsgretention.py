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

def get_nsgs(subscription_id):
    """Fetches all NSGs and resource groups for a specific subscription."""
    command = f'az network nsg list --subscription {subscription_id} --query "[*].[name,resourceGroup]" --output json'
    output, error = run_command(command)
    
    if output:
        try:
            nsgs = json.loads(output)
            return nsgs if nsgs else []
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing JSON output for NSG list in subscription {subscription_id}.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve NSGs for subscription {subscription_id}. Error: {error}{Style.RESET_ALL}")
    return []

def check_nsg_flow_logs(resource_group, nsg_name):
    """Checks NSG flow logs and retention policy for a specific NSG."""
    command = f'az network watcher flow-log show --resource-group {resource_group} --nsg {nsg_name} --query "retentionPolicy" --output json'
    output, error = run_command(command)
    
    if error:
        return 'not_enabled', None
    elif output:
        try:
            flow_log_data = json.loads(output)
            enabled = flow_log_data.get("enabled", False)
            retention_days = flow_log_data.get("days", 0)

            if enabled and retention_days >= 90:
                return 'compliant', flow_log_data
            elif enabled and retention_days < 90:
                return 'non_compliant', flow_log_data
            else:
                return 'not_enabled', flow_log_data
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing flow log data for NSG {nsg_name}.{Style.RESET_ALL}")
            return 'not_enabled', None
    return 'not_enabled', None

def display_nsg_flow_log_status():
    """Iterates through each subscription and NSG to check flow log and retention policy."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    overall_status = "pass"  

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        print(f"\n{Fore.YELLOW}Checking NSG flow logs for subscription: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        nsgs = get_nsgs(subscription_id)
        if not nsgs:
            print(f"{Fore.YELLOW}No network security groups found in subscription {subscription_name}.{Style.RESET_ALL}")
            continue

        for nsg in nsgs:
            nsg_name = nsg[0]
            resource_group = nsg[1]
            status, flow_log_data = check_nsg_flow_logs(resource_group, nsg_name)
            print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
            print()

            if status == 'compliant':
                print(f"{Fore.GREEN}NSG flow logs enabled and retention is 90 days or more for NSG: {nsg_name}{Style.RESET_ALL}")
            elif status == 'non_compliant':
                overall_status = "fail"
                print(f"{Fore.RED}NSG flow logs retention is less than 90 days for NSG: {nsg_name}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}\n{json.dumps(flow_log_data, indent=4)}{Style.RESET_ALL}")
            else:
                overall_status = "fail"
                print(f"{Fore.RED}NSG flow logs not enabled for NSG: {nsg_name}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}\n{json.dumps(flow_log_data, indent=4)}{Style.RESET_ALL}")

    
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN if overall_status == 'pass' else Fore.RED}{overall_status.upper()}{Style.RESET_ALL}")

def main():
    display_nsg_flow_log_status()

if __name__ == "__main__":
    main()
