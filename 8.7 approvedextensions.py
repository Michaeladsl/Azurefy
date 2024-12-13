import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)


approved_extensions = ["CustomScriptExtension", "DependencyAgentLinux", "OmsAgentForLinux"]

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

def list_vms(subscription_id):
    """Lists all VMs in the current subscription."""
    command = f'az vm list --subscription {subscription_id} --query "[].{{name:name, resourceGroup:resourceGroup}}" --output json'
    output, error = run_command(command)
    
    if output:
        try:
            vms = json.loads(output)
            return vms if vms else []
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing VM list JSON output.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve VMs. Error: {error}{Style.RESET_ALL}")
    return []

def list_vm_extensions(resource_group, vm_name):
    """Lists the extensions attached to a specific VM."""
    command = f'az vm extension list --resource-group {resource_group} --vm-name {vm_name} --query "[].name" -o json'
    output, error = run_command(command)
    
    if output:
        try:
            extensions = json.loads(output)
            return extensions if extensions else []
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing VM extensions JSON output for VM {vm_name}.{Style.RESET_ALL}")
            return []
    else:
        print(f"{Fore.RED}Failed to retrieve extensions for VM {vm_name}. Error: {error}{Style.RESET_ALL}")
    return []

def check_vm_extensions(subscription_id, subscription_name):
    """Checks if each VM in the subscription has approved extensions."""
    print(f"\n{Fore.YELLOW}Checking VM extensions for subscription: {subscription_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()

    
    if not set_subscription(subscription_id):
        return

    
    vms = list_vms(subscription_id)
    if not vms:
        print(f"{Fore.YELLOW}No virtual machines found in subscription {subscription_name}.{Style.RESET_ALL}")
        return

    non_compliant_found = False

    
    for vm in vms:
        vm_name = vm['name']
        resource_group = vm['resourceGroup']

        extensions = list_vm_extensions(resource_group, vm_name)
        print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
        print()
        
        non_compliant = [ext for ext in extensions if ext not in approved_extensions]
        compliant = all(ext in approved_extensions for ext in extensions)

        if compliant:
            print(f"{Fore.GREEN}VM: {vm_name} - Approved extensions only{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}VM: {vm_name}{Style.RESET_ALL}")
            print(f"\n{json.dumps(extensions, indent=4)}{Style.RESET_ALL}")
            non_compliant_found = True

    
    final_status = "PASS" if not non_compliant_found else "FAIL"
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN if final_status == 'PASS' else Fore.RED}{final_status}{Style.RESET_ALL}")

def main():
    
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    
    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        check_vm_extensions(subscription_id, subscription_name)

if __name__ == "__main__":
    main()
