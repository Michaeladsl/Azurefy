import subprocess
import json
import colorama
from colorama import Fore, Style

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
        print(f"{Fore.RED}Not authenticated. Please authenticate using the main script.{Style.RESET_ALL}")
        return False

def color_text(text, color):
    """Returns the text wrapped with the specified color."""
    return f"{color}{text}{Style.RESET_ALL}"

def get_pricing_tier(service_name, subscription_id):
    """Fetches the pricing tier for a given Defender service for a specific subscription."""
    command = f"az security pricing show -n {service_name} --query pricingTier --subscription {subscription_id}"
    pricing_tier = run_command(command)
    
    if pricing_tier == '"Standard"':  
        return "Standard", color_text(pricing_tier.strip('"'), Fore.GREEN)
    elif pricing_tier == 'null':
        return "null", color_text(pricing_tier, Fore.RED)
    else:
        return pricing_tier.strip('"'), color_text(pricing_tier.strip('"'), Fore.RED)

def get_subscriptions():
    """Fetches a list of all Azure subscriptions available for the account."""
    command = "az account list --query '[].{id:id, name:name}'"
    result = run_command(command)
    if result:
        try:
            subscriptions = json.loads(result)
            return subscriptions
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve subscriptions.{Style.RESET_ALL}")
    return []

def display_defender_service_status():
    """Iterates through each subscription and displays Defender service status with color formatting."""
    subscriptions = get_subscriptions()
    overall_status = "pass"  

    for subscription in subscriptions:
        subscription_id = subscription['id']
        subscription_name = subscription['name']
        
        print(f"\n{Fore.YELLOW}Defender pricing tiers: {subscription_name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
        print()

        
        services = [
            ("Virtual Machines", "VirtualMachines"),
            ("App Services", "AppServices"),
            ("SQL Databases", "SqlServers"),
            ("SQL Servers on Machines", "SqlServerVirtualMachines"),
            ("Relational Databases", "OpenSourceRelationalDatabases"),
            ("Cosmos DBs", "CosmosDbs"),
            ("Storage", "StorageAccounts"),
            ("Containers", "ContainerRegistry"),
            ("Key Vaults", "KeyVaults"),
            ("DNS (Legacy)", "DNS"),
            ("Resource Manager", "Arm")
        ]

        for service_name, service_key in services:
            pricing_tier, formatted_output = get_pricing_tier(service_key, subscription_id)
            print(f"{service_name}: {formatted_output}")

            if pricing_tier != "Standard":
                overall_status = "fail"  
        print("----------------------------------------")

    
    if overall_status == "pass":
        print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}PASS{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.CYAN}Final Status: {Fore.RED}FAIL{Style.RESET_ALL}")

def run_defender_service_check():
    """Main function to check Defender service settings for all subscriptions."""
    if check_authentication():
        display_defender_service_status()

def main():
    """Entry point for Defender service status check."""
    run_defender_service_check()

if __name__ == "__main__":
    main()
