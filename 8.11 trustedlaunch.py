import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def run_command(command):
    """Runs a shell command and returns the output."""
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
        print(f"{Fore.RED}Failed to retrieve VMs. Error: {error}{Style.RESET_ALL}")
    return []

def check_vm_security_profile(resource_group, vm_name, subscription_id):
    """Checks the security profile of a VM using Azure CLI."""
    command = f'az vm show -g {resource_group} -n {vm_name} --subscription {subscription_id} --query "securityProfile" --output json'
    output, error = run_command(command)
    
    if output:
        try:
            security_profile = json.loads(output)
            return security_profile
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error parsing security profile JSON output for VM {vm_name}.{Style.RESET_ALL}")
            return None
    else:
        print(f"{Fore.RED}Failed to retrieve security profile for VM {vm_name}. Error: {error}{Style.RESET_ALL}")
    return None

def analyze_security_profile(security_profile, vm_name):
    """Analyzes the security profile of the VM and prints the appropriate message."""
    if not security_profile:
        print(f"{Fore.RED}No security profile found for VM: {vm_name}{Style.RESET_ALL}")
        return False

    security_type = security_profile.get("securityType", "standard")
    uefi_settings = security_profile.get("uefiSettings", {})

    secure_boot_enabled = uefi_settings.get("secureBootEnabled", False)
    v_tpm_enabled = uefi_settings.get("vTpmEnabled", False)
    print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
    print()
    if security_type == "TrustedLaunch" and secure_boot_enabled and v_tpm_enabled:
        print(f"{Fore.GREEN}Trusted launch configured correctly for VM: {vm_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Security Profile:\n{json.dumps(security_profile, indent=4)}{Style.RESET_ALL}")
        return True
    else:
        print(f"{Fore.RED}Trusted launch not properly configured for VM: {vm_name}{Style.RESET_ALL}")
        print(f"{Fore.RED}Security Profile:\n{json.dumps(security_profile, indent=4)}{Style.RESET_ALL}")
        return False

def check_vm_trusted_launch(subscription_id, subscription_name):
    """Checks if each VM in the subscription has Trusted Launch correctly configured."""
    print(f"\n{Fore.YELLOW}Checking VMs for subscription: {subscription_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()

    
    if not set_subscription(subscription_id):
        return True  

    
    vms = list_vms(subscription_id)
    if not vms:
        print(f"{Fore.YELLOW}No virtual machines found in subscription {subscription_name}.{Style.RESET_ALL}")
        return True  

    all_compliant = True

    
    for vm in vms:
        vm_name = vm['name']
        resource_group = vm['resourceGroup']

        security_profile = check_vm_security_profile(resource_group, vm_name, subscription_id)
        compliant = analyze_security_profile(security_profile, vm_name)
        if not compliant:
            all_compliant = False

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
        compliant = check_vm_trusted_launch(subscription_id, subscription_name)
        if not compliant:
            overall_compliant = False

    
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN if overall_compliant else Fore.RED}{'PASS' if overall_compliant else 'FAIL'}{Style.RESET_ALL}")

    
    print("Final Status: PASS" if overall_compliant else "Final Status: FAIL")


if __name__ == "__main__":
    main()
