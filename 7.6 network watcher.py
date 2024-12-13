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

def get_network_watchers():
    """Lists all network watchers and their provisioning state."""
    command = 'az network watcher list --query "[].{Location:location,State:provisioningState}" -o json'
    output, error = run_command(command)
    
    if output:
        try:
            network_watchers = json.loads(output)
            return network_watchers if network_watchers else []
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing Network Watchers JSON output.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve network watchers. Error: {error}{Style.RESET_ALL}")
    return []

def get_physical_regions():
    """Lists all physical regions for the subscription."""
    command = "az account list-locations --query \"[?metadata.regionType=='Physical'].{Name:name,DisplayName:regionalDisplayName}\" -o json"
    output, error = run_command(command)
    
    if output:
        try:
            regions = json.loads(output)
            return regions if regions else []
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing Regions JSON output.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve physical regions. Error: {error}{Style.RESET_ALL}")
    return []

def check_network_watcher_status(subscription_id, subscription_name):
    """Checks if Network Watcher is enabled for each region with provisioningState set to 'Succeeded'."""
    print(f"\n{Fore.YELLOW}Checking Network Watcher for subscription: {subscription_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()
    
    
    if not set_subscription(subscription_id):
        print(f"{Fore.RED}Failed to set subscription {subscription_name}{Style.RESET_ALL}")
        return "fail"
    
    
    network_watchers = get_network_watchers()
    if not network_watchers:
        print(f"{Fore.RED}No network watchers found in subscription {subscription_name}.{Style.RESET_ALL}")
        return "fail"

    
    regions = get_physical_regions()
    if not regions:
        print(f"{Fore.RED}No physical regions found in subscription {subscription_name}.{Style.RESET_ALL}")
        return "fail"

    non_compliant_regions = []  
    for region in regions:
        region_name = region["Name"]
        watcher_found = False
        region_data = None
        
        for watcher in network_watchers:
            if watcher["Location"] == region_name and watcher["State"] == "Succeeded":
                watcher_found = True
                region_data = watcher
                break
        print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
        print()
        print(f"{Fore.YELLOW}Region: {region_name}{Style.RESET_ALL}")
        if watcher_found:
            print(f"{Fore.GREEN}Network Watcher enabled in {region_name}{Style.RESET_ALL}")
            print(f"\n{json.dumps(region_data, indent=4)}")
        else:
            print(f"{Fore.RED}Network Watcher not enabled in {region_name}{Style.RESET_ALL}")
            non_compliant_regions.append(region_name)

    
    if non_compliant_regions:
        print()
        return "fail"
    return "pass"

def main():
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    overall_status = "pass"  

    
    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        status = check_network_watcher_status(subscription_id, subscription_name)
        
        if status == "fail":
            overall_status = "fail"

    
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN if overall_status == 'pass' else Fore.RED}{overall_status.upper()}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
