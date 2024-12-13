import subprocess
import json
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def run_command(command):
    """Runs a shell command and returns the output or None if the command fails."""
    try:
        process = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Error executing command: {e.stderr}{Style.RESET_ALL}")
        return None

def check_authentication():
    """Check if already authenticated with Azure CLI to skip login."""
    try:
        subprocess.run(['az', 'account', 'show'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}Not authenticated. Please authenticate using the main script.{Style.RESET_ALL}")
        return False

def get_network_rule_sets():
    """Fetches the network rule sets for all storage accounts in the current subscription."""
    command = "az storage account list --query '[*].{name:name, networkRuleSet:networkRuleSet}' -o json"
    response = run_command(command)
    
    if response:
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Error parsing JSON output for network rule sets: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Failed to retrieve network rule sets.{Style.RESET_ALL}")
    return []

def check_default_action(rule_set):
    """Checks and color-codes the default network access setting (Allow/Deny) for a specific storage account."""
    account_name = rule_set.get("name")
    network_rule_set = rule_set.get("networkRuleSet", {})
    default_action = network_rule_set.get("defaultAction", "Unknown")

    if default_action == "Deny":
        return Fore.GREEN, account_name, "Default Action: Deny"
    elif default_action == "Allow":
        return Fore.RED, account_name, "Default Action: Allow", network_rule_set
    else:
        return Fore.YELLOW, account_name, "Default Action: Unknown", network_rule_set

def display_network_access_status():
    """Iterates through all storage accounts and checks the default network access setting."""
    if not check_authentication():
        print(f"{Fore.RED}Please authenticate using the main script first.{Style.RESET_ALL}")
        return

    network_rule_sets = get_network_rule_sets()
    if not network_rule_sets:
        print(f"{Fore.RED}No network rule sets found or failed to retrieve data.{Style.RESET_ALL}")
        return
    print(f"\n{Fore.YELLOW}Checking storage accounts for default network access...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}____________________________________________________{Style.RESET_ALL}")
    print()

    all_compliant = True  

    for rule_set in network_rule_sets:
        color, account_name, status, *proof = check_default_action(rule_set)
        print(f"{Fore.YELLOW}____________________________________________________{Style.RESET_ALL}")
        print()
        print(f"Storage Account: {account_name} - {color}{status}{Style.RESET_ALL}")

        
        if color == Fore.RED and proof:
            print(f"{Fore.CYAN}Sample JSON Proof:{Style.RESET_ALL}")
            print(json.dumps(proof[0], indent=4))

            all_compliant = False

    print(f"\n{Fore.CYAN}Final Status: {Fore.GREEN}Pass{Style.RESET_ALL}" if all_compliant else f"\n{Fore.CYAN}Final Status: {Fore.RED}Fail{Style.RESET_ALL}")


def main():
    """Entry point for Default Network Access Check."""
    display_network_access_status()

if __name__ == "__main__":
    main()
