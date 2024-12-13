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

def list_managed_disks():
    """Lists all managed disks in the current subscription."""
    command = 'az disk list --query "[].{name:name, resourceGroup:resourceGroup}" --output json'
    output, error = run_command(command)
    
    if output:
        try:
            disks = json.loads(output)
            return disks if disks else []
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing managed disks JSON output.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve managed disks. Error: {error}{Style.RESET_ALL}")
    return []

def check_disk_access_settings(resource_group, disk_name):
    """Checks the access settings for a managed disk."""
    command = f'az disk show --resource-group {resource_group} --name {disk_name} --query "{{publicNetworkAccess:publicNetworkAccess, networkAccessPolicy:networkAccessPolicy}}" -o json'
    output, error = run_command(command)
    
    if output:
        try:
            settings = json.loads(output)
            return settings
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing disk access settings JSON output.{Style.RESET_ALL}")
            return None
    else:
        print(f"{Fore.RED}Failed to retrieve settings for disk {disk_name} in resource group {resource_group}. Error: {error}{Style.RESET_ALL}")
    return None

def highlight_json(json_data):
    """Highlights the JSON data for better visualization."""
    json_str = json.dumps(json_data, indent=4)
    return f"{Fore.CYAN}{json_str}{Style.RESET_ALL}"

def check_compliance(subscription_id, subscription_name):
    """Checks compliance of each managed disk in the subscription."""
    print(f"\n{Fore.YELLOW}Checking managed disks for subscription: {subscription_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()

    
    if not set_subscription(subscription_id):
        return

    
    managed_disks = list_managed_disks()
    if not managed_disks:
        print(f"{Fore.YELLOW}No managed disks found in subscription {subscription_name}.{Style.RESET_ALL}")
        return

    non_compliant_disks = False

    
    for disk in managed_disks:
        disk_name = disk["name"]
        resource_group = disk["resourceGroup"]
        print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
        print()
        settings = check_disk_access_settings(resource_group, disk_name)
        if settings:
            public_access = settings.get("publicNetworkAccess", "Unknown")
            access_policy = settings.get("networkAccessPolicy", "Unknown")

            
            if public_access == "Disabled" and access_policy in ["AllowPrivate", "DenyAll"]:
                print(f"{Fore.GREEN} Disk: {disk_name} - Public Access: {public_access}, Access Policy: {access_policy}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Disk: {disk_name}{Style.RESET_ALL}")
                print(f"\n{highlight_json(settings)}")
                non_compliant_disks = True
        else:
            print(f"{Fore.RED}Failed to retrieve settings for disk: {disk_name}{Style.RESET_ALL}")

    
    final_status = "PASS" if not non_compliant_disks else "FAIL"
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN if final_status == 'PASS' else Fore.RED}{final_status}{Style.RESET_ALL}")

def main():
    
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    
    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        check_compliance(subscription_id, subscription_name)

if __name__ == "__main__":
    main()
