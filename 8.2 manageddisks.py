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

def list_vms(subscription_id):
    """Lists all virtual machines in the current subscription."""
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
        print(f"{Fore.RED}Failed to list VMs. Error: {error}{Style.RESET_ALL}")
    return []

def check_vhd_status(resource_group, vm_name):
    """Checks if a VM is using managed disks or not based on the vhd field."""
    command = f'az vm show -g {resource_group} -n {vm_name} --query "storageProfile.osDisk.vhd" --output json'
    output, error = run_command(command)
    
    if output:
        print(f"{Fore.CYAN}VHD Information for VM {vm_name}:\n{output}{Style.RESET_ALL}")  
        try:
            vhd_info = json.loads(output)
            return vhd_info
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing VHD JSON output for VM {vm_name}.{Style.RESET_ALL}")
            return None
    else:
        print(f"{Fore.GREEN}VM {vm_name} is using managed disks.{Style.RESET_ALL}")
    return None

def highlight_vhd(vhd_info):
    """Highlights the vhd key in the JSON output in red."""
    vhd_str = json.dumps(vhd_info, indent=4)
    vhd_str = vhd_str.replace('"vhd"', f'{Fore.RED}"vhd"{Style.RESET_ALL}')
    return vhd_str

def check_vm_disks(subscription_id, subscription_name):
    """Checks if each VM in the subscription uses managed disks or not."""
    print(f"\n{Fore.YELLOW}Checking VMs for subscription: {subscription_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()

    
    if not set_subscription(subscription_id):
        return False

    
    vms = list_vms(subscription_id)
    if not vms:
        print(f"{Fore.YELLOW}No virtual machines found in subscription {subscription_name}.{Style.RESET_ALL}")
        return True

    all_compliant = True

    
    for vm in vms:
        vm_name = vm['name']
        resource_group = vm['resourceGroup']

        vhd_info = check_vhd_status(resource_group, vm_name)
        print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
        print()
        if vhd_info:
            print(f"{Fore.RED}Managed disk not used in VM: {vm_name}{Style.RESET_ALL}")
            highlighted_vhd = highlight_vhd(vhd_info)
            print(f"{highlighted_vhd}")
            all_compliant = False
        else:
            print(f"{Fore.GREEN}Managed disks used in VM: {vm_name}{Style.RESET_ALL}")

    return all_compliant

def main():
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        print("Final Status: FAIL")  
        return

    overall_compliant = True

    for subscription in subscriptions:
        subscription_id = subscription["subscriptionId"]
        subscription_name = subscription["displayName"]
        compliant = check_vm_disks(subscription_id, subscription_name)
        if not compliant:
            overall_compliant = False

    
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN if overall_compliant else Fore.RED}{'PASS' if overall_compliant else 'FAIL'}{Style.RESET_ALL}")

    
    print("Final Status: PASS" if overall_compliant else "Final Status: FAIL")


if __name__ == "__main__":
    main()
