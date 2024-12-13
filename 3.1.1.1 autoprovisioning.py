import subprocess
import json
import colorama
from colorama import Fore, Style
import argparse

colorama.init(autoreset=True)

def run_command(command):
    """Runs a shell command and returns the output or 'null' if the command fails."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = process.stdout.strip()
        return result if result else 'null'
    except subprocess.CalledProcessError:
        return 'null'

def check_authentication():
    """Check if already authenticated with Azure CLI to skip login."""
    try:
        subprocess.run(['az', 'account', 'show'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}Not authenticated. Please log in using the main script.{Style.RESET_ALL}")
        return False

def get_subscriptions():
    """Fetches a list of all Azure subscriptions available for the account."""
    command = "az account list --query '[].{id:id, name:name}'"
    result = run_command(command)
    if result != 'null':
        try:
            subscriptions = json.loads(result)
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve subscriptions.{Style.RESET_ALL}")
    return []

def get_auto_provisioning_setting(subscription_id):
    """Fetches the auto provisioning setting for the specified subscription."""
    url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Security/autoProvisioningSettings?api-version=2017-08-01-preview"    
    command = f"az rest --method get --url {url}"
    response = run_command(command)
    
    if response != 'null':
        try:
            data = json.loads(response)
            auto_provision = [
                item["properties"]["autoProvision"]
                for item in data.get("value", [])
                if item.get("name") == "default"
            ]
            if auto_provision:
                setting = auto_provision[0]                
                
                if setting == "On":
                    print(f"{Fore.GREEN}{setting}{Style.RESET_ALL}")
                    print(f"\n{Fore.GREEN}Final Status: Pass{Style.RESET_ALL}\n")
                elif setting == "Off":
                    print(f"{Fore.RED}{setting}{Style.RESET_ALL}")
                    print(f"\n{Fore.RED}Final Status: Fail{Style.RESET_ALL}\n")
                else:
                    print(f"{Fore.YELLOW}Unknown setting: {setting}{Style.RESET_ALL}")
                    print(f"\n{Fore.YELLOW}Final Status: Unknown{Style.RESET_ALL}\n")
            else:
                print(f"{Fore.RED}No autoProvision setting found for name='default' in subscription {subscription_id}.{Style.RESET_ALL}")
                print(f"\n{Fore.RED}Final Status: Fail{Style.RESET_ALL}\n")
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON response: {e}{Style.RESET_ALL}")
            print(f"\n{Fore.RED}Final Status: Fail{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}Failed to retrieve auto provisioning settings for subscription {subscription_id}.{Style.RESET_ALL}")
        print(f"\n{Fore.RED}Final Status: Fail{Style.RESET_ALL}\n")

def display_auto_provisioning_settings():
    """Iterates through each subscription and displays auto provisioning settings."""
    subscriptions = get_subscriptions()
    if not subscriptions:
        print(f"{Fore.RED}No subscriptions found or failed to retrieve subscriptions.{Style.RESET_ALL}")
        return

    for subscription in subscriptions:
        subscription_id = subscription['id']
        subscription_name = subscription['name']
        print(f"\n{Fore.YELLOW}Checking Auto Provisioning Setting for: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()
        get_auto_provisioning_setting(subscription_id)

def main():
    """Entry point for Auto Provisioning Settings check."""
    if not check_authentication():
        print(f"{Fore.RED}Please authenticate using the main script first.{Style.RESET_ALL}")
        return

    
    display_auto_provisioning_settings()

if __name__ == "__main__":
    main()
