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

def check_unattached_disks():
    """Checks for unattached disks and their encryption settings."""
    command = 'az disk list --query "[?diskState == `Unattached`].{encryptionSettings: encryptionSettings, name: name}" -o json'
    output, error = run_command(command)
    
    
    if not output or output in ["null", "[]"]:
        return []
    
    if error:
        print(f"{Fore.RED}Error executing command: {error}{Style.RESET_ALL}")
        return None

    try:
        unattached_disks = json.loads(output)
        return unattached_disks if unattached_disks else []
    except json.JSONDecodeError:
        print(f"{Fore.RED}Error parsing unattached disks JSON output.{Style.RESET_ALL}")
        return None

def highlight_disk(disk_info):
    """Highlights encryption-related fields in the disk JSON output in red."""
    disk_str = json.dumps(disk_info, indent=4)
    disk_str = disk_str.replace('"encryptionSettings": null', f'{Fore.RED}"encryptionSettings": null{Style.RESET_ALL}')
    disk_str = disk_str.replace('"encryptionSettings"', f'{Fore.RED}"encryptionSettings"{Style.RESET_ALL}')
    return disk_str

def check_cmk_status(subscription_id, subscription_name):
    """Checks if CMK is used for unattached disks in the current subscription."""
    print(f"\n{Fore.YELLOW}Checking unattached disks for subscription: {subscription_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()
    
    if not set_subscription(subscription_id):
        return

    
    unattached_disks = check_unattached_disks()
    print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
    print()
    if unattached_disks is None:
        print(f"{Fore.RED}Failed to retrieve unattached disks for subscription {subscription_name}.{Style.RESET_ALL}")
        return False

    if not unattached_disks:
        print(f"{Fore.GREEN}No unattached disks found in subscription {subscription_name}.{Style.RESET_ALL}")
        return True

    
    non_compliant_disks = False
    for disk in unattached_disks:
        encryption_settings = disk.get("encryptionSettings", None)
        if not encryption_settings:
            print(f"{Fore.RED}Unattached disk without CMK encryption found: {disk.get('name', 'Unknown')}{Style.RESET_ALL}")
            highlighted_disk = highlight_disk(disk)
            print(highlighted_disk)
            non_compliant_disks = True
        else:
            print(f"{Fore.GREEN}Unattached disk with CMK encryption: {disk.get('name', 'Unknown')}{Style.RESET_ALL}")
    
    return not non_compliant_disks

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
        compliant = check_cmk_status(subscription_id, subscription_name)
        if not compliant:
            overall_compliant = False

    
    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN if overall_compliant else Fore.RED}{'PASS' if overall_compliant else 'FAIL'}{Style.RESET_ALL}")

    
    print("Final Status: PASS" if overall_compliant else "Final Status: FAIL")


if __name__ == "__main__":
    main()
